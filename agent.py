import json
from pathlib import Path
import re
import subprocess
import time

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from llm_client import get_completion
from memory import MemoryStore
from session.manager import SessionManager

# 初始化 Rich 控制台
console = Console()

# 加载环境变量
load_dotenv(override=True)

# 定义工作目录和技能目录
WORKDIR = Path.cwd()
SKILLS_DIR = WORKDIR / "skills"
TASKS_DIR = WORKDIR / ".tasks"

# 初始化存储和会话管理器
memory_store = MemoryStore(WORKDIR)
session_manager = SessionManager(WORKDIR)


# --- 工具定义 ---
# 导入各个工具模块
from tools.base import TOOL_HANDLERS as BASE_HANDLERS, TOOLS as BASE_TOOLS
from tools.skillLoader import (
    TOOL_HANDLERS as SKILL_HANDLERS,
    TOOLS as SKILL_TOOLS,
    SKILL_LOADER,
    SYSTEM as SKILL_SYSTEM,
)
from tools.todo_tool import TOOL_HANDLERS as TODO_HANDLERS, TOOLS as TODO_TOOLS
from tools.web_tool import TOOL_HANDLERS as WEB_HANDLERS, TOOLS as WEB_TOOLS
from tools.code_tool import TOOL_HANDLERS as CODE_HANDLERS, TOOLS as CODE_TOOLS
from tools.mcp_tool import load_mcp_server
from context import ContextManager

# 初始化上下文管理器
context_manager = ContextManager(SKILL_SYSTEM, memory_store)


# --- 长期记忆工具 ---
def save_to_memory(history_entry: str, memory_update: str = None) -> str:
    """保存信息到长期记忆。"""
    if history_entry:
        memory_store.append_history(history_entry)
    if memory_update:
        memory_store.write_long_term(memory_update)
    return "Memory updated successfully."


MEMORY_HANDLERS = {
    "save_memory": lambda **kw: save_to_memory(
        kw.get("history_entry"), kw.get("memory_update")
    ),
}

MEMORY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Save important facts or summaries to long-term memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "history_entry": {
                        "type": "string",
                        "description": "A paragraph summarizing key events or decisions to append to history log.",
                    },
                    "memory_update": {
                        "type": "string",
                        "description": "Full updated long-term memory as markdown. Use this to overwrite the current facts.",
                    },
                },
            },
        },
    }
]

# --- 加载 MCP 服务器 ---
# 自动加载 mcp/ 目录下所有以 _server.py 结尾的服务器
MCP_TOOLS = []
MCP_HANDLERS = {}

mcp_dir = WORKDIR / "mcp"
if mcp_dir.exists():
    for f in mcp_dir.glob("*_server.py"):
        server_path = str(f)
        try:
            tools, handlers = load_mcp_server(server_path)
            MCP_TOOLS.extend(tools)
            MCP_HANDLERS.update(handlers)
            print(f"[MCP Server Loaded: {f.name}]")
        except Exception as e:
            print(f"Error loading MCP server {f.name}: {e}")

# 合并并扩展工具处理器
TOOL_HANDLERS = {
    **BASE_HANDLERS,
    **TODO_HANDLERS,
    **SKILL_HANDLERS,
    **MEMORY_HANDLERS,
    **WEB_HANDLERS,
    **CODE_HANDLERS,
    **MCP_HANDLERS,
}

# 合并工具定义
TOOLS = (
    BASE_TOOLS
    + SKILL_TOOLS
    + TODO_TOOLS
    + MEMORY_TOOLS
    + WEB_TOOLS
    + CODE_TOOLS
    + MCP_TOOLS
)


# --- 主循环 ---
def agent_loop(session):
    """
    Agent的主循环，包含三层压缩机制。
    """
    rounds_since_todo = 0
    step_count = 1
    while True:
        console.print(
            f"\n[bold white]{'━'*20} [ 第 {step_count} 轮思考开始 ] {'━'*20}[/bold white]"
        )

        # 使用上下文管理器组装最终 Prompt
        system_prompt, messages = context_manager.build_prompt(session)

        # 使用 litellm 进行对话补全
        with console.status("[bold cyan]Agent is thinking...", spinner="dots"):
            response = get_completion(
                messages=messages,
                system=system_prompt,  # 使用包含记忆的系统提示提示词
                tools=TOOLS,
                max_tokens=8000,
            )

        # 获取消息对象
        raw_msg = response.choices[0].message

        # 将消息转换为标准字典格式，确保跨模型兼容性
        msg_dict = {"role": "assistant", "content": raw_msg.content}
        if raw_msg.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in raw_msg.tool_calls
            ]

        session.add_message(
            msg_dict["role"], msg_dict["content"], tool_calls=msg_dict.get("tool_calls")
        )

        # 【教育打印 1：大模型的内在思考 / 推理文字】
        if raw_msg.content:
            console.print(f"\n[bold magenta]🧠 [Agent 思考]:[/bold magenta]")
            console.print(raw_msg.content)

        # 如果没有工具调用且内容为空，可能发生了异常中断
        if response.choices[0].finish_reason != "tool_calls" and not raw_msg.content:
            console.print(
                "[red]⚠️  Warning: Agent returned empty response. Retrying with a nudge...[/red]"
            )
            session.add_message("user", "Please continue with the task.")
            continue

        # 如果没有工具调用，则认为是最终回复，退出循环
        if response.choices[0].finish_reason != "tool_calls":
            console.print(
                f"\n[bold yellow]🏁 [任务完成 / 最终回复]: Agent 停止调用工具。[/bold yellow]"
            )
            return

        used_todo = False
        tool_calls = raw_msg.tool_calls or []
        tool_calls_count = len(tool_calls)

        # 处理并收集工具调用结果
        for i, tool_call in enumerate(tool_calls, 1):
            function_name = tool_call.function.name
            # 解析参数
            args = json.loads(tool_call.function.arguments)

            # 【教育打印 2：大模型决定使用的工具和参数】
            console.print(
                f"\n[bold cyan]🛠️  [Agent 动作] ({i}/{tool_calls_count}): 决定调用工具 -> 【{function_name}】[/bold cyan]"
            )
            console.print(f"[cyan]   传入参数: {args}[/cyan]")

            handler = TOOL_HANDLERS.get(function_name)
            start_time = time.time()
            try:
                with console.status(
                    f"[bold magenta]⏳ 正在本地机器执行 {function_name}...",
                    spinner="bouncingBar",
                ):
                    output = (
                        handler(**args)
                        if handler
                        else f"Unknown tool: {function_name}"
                    )
            except Exception as e:
                output = f"Error: {e}"
            cost_time = time.time() - start_time

            # 【教育打印 3：本地代码执行的结果】
            # 截断太长的输出
            short_output = str(output)[:300] + ("..." if len(str(output)) > 300 else "")
            console.print(
                f"[bold green]✅ [执行结果] (耗时 {cost_time:.2f}s):[/bold green]"
            )
            console.print(f"[green]{short_output}[/green]")

            # 添加工具调用结果到 session
            session.add_message(
                "tool", str(output), tool_call_id=tool_call.id, name=function_name
            )

            if function_name == "todo":
                used_todo = True
        # 处理待办事项提醒逻辑
        rounds_since_todo = 0 if used_todo else rounds_since_todo + 1
        if rounds_since_todo >= 3:
            console.log(
                "[yellow]Step: Injecting todo reminder to keep agent on track.[/yellow]"
            )
            # 注入提醒消息
            session.add_message("user", "<reminder>Update your todos.</reminder>")

        step_count += 1


if __name__ == "__main__":
    console.print(
        Panel.fit(
            "[bold green]🤖 Agent Initialized and Ready![/bold green]\nType [bold red]q[/bold red] or [bold red]exit[/bold red] to quit.",
            title="System",
            border_style="green",
        )
    )

    # 获取或创建默认会话
    session = session_manager.get_or_create("default:main")

    while True:
        try:
            query = Prompt.ask("\n[bold cyan]You[/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            console.print("[bold red]Goodbye![/bold red]")
            break

        session.add_message("user", query)
        agent_loop(session)

        # 保存会话状态
        session_manager.save(session)

        history = session.get_history()
        response_content = history[-1].get("content")
        if response_content:
            if isinstance(response_content, str):
                console.print(
                    Panel(
                        Markdown(response_content),
                        title="[bold blue]Agent[/bold blue]",
                        border_style="blue",
                    )
                )
            elif isinstance(response_content, list):
                # 处理多模态或块状内容
                text_parts = [
                    block.get("text", "")
                    for block in response_content
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                if text_parts:
                    console.print(
                        Panel(
                            Markdown("\n".join(text_parts)),
                            title="[bold blue]Agent[/bold blue]",
                            border_style="blue",
                        )
                    )
        else:
            # 如果 content 为空但有工具调用记录，说明 Agent 还在中间状态（通常不应该发生在这里）
            console.print("[dim]Agent provided no text response.[/dim]")
