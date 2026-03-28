import json
from pathlib import Path
import re
import subprocess
import time
import traceback
from time import perf_counter

from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from llm_client import get_completion
from memory import memory_store
from session.manager import SessionManager
from logger import AgentLogger
from retry import RetryExhaustedError

# 初始化 Rich 控制台
console = Console()

# 加载环境变量
load_dotenv(override=True)

# 定义工作目录和技能目录
WORKDIR = Path.cwd()
SKILLS_DIR = WORKDIR / "skills"
TASKS_DIR = WORKDIR / ".tasks"

# 初始化存储和会话管理器
session_manager = SessionManager(WORKDIR)
run_logger = AgentLogger()


# --- 工具定义 ---
from tools.loader import tool_manager
from tools.mcp_tool import load_mcp_server
from context import ContextManager
from tools.skillLoader import SYSTEM as SKILL_SYSTEM

# 初始化上下文管理器
context_manager = ContextManager(SKILL_SYSTEM, memory_store)

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
    **tool_manager.get_handlers(),
    **MCP_HANDLERS,
}

# 审批工具清单
APPROVAL_TOOLS = ["send_via_gmail", "send_via_resend", "write_code", "web_rpa_worker", "submit_expense_claim"]

# 合并工具定义
TOOLS = (
    tool_manager.get_tools_schemas()
    + MCP_TOOLS
)


def _auto_extract_facts(session, response_content: str):
    """分析对话提取长期记忆事实。"""
    if not response_content or len(response_content) < 10:
        return
        
    # 为自动提取添加状态灯，避免用户误以为程序卡死
    with console.status("[dim]🧠 [长期记忆] 正在分析并提取重要事实...[/dim]", spinner="dots"):
        history = session.get_history(max_messages=5)
        prompt = f"""分析对话片段并提取【永恒事实】（用户偏好、习惯、规章制度）。
不要摘要对话，只提取对未来对话有用的永恒事实。
如果没有提取到新事实，仅回复 "NONE"。

上下文：
{json.dumps(history[-3:], ensure_ascii=False)}

最新回复：
{response_content}

提取出的事实："""

        try:
            # 限制提取任务的 token 以保证响应速度
            res = get_completion(messages=[{"role": "user", "content": prompt}], max_tokens=200)
            content = res.choices[0].message.content.strip()
            if content and "NONE" not in content.upper():
                count = 0
                for line in content.splitlines():
                    fact = line.strip().lstrip("-").lstrip("*").strip()
                    if fact and len(fact) > 3:
                        memory_store.remember(fact)
                        count += 1
                if count > 0:
                    console.print(f"[dim]✅ 成功提取并记录了 {count} 条长期事实。[/dim]")
        except Exception:
            # 静默失败，不打断主流程
            pass


# --- 主循环 ---
def agent_loop(session, context_manager_override=None, tools_override=None, is_sub_agent=False):
    """
    Agent的主循环，包含三层压缩机制。
    支持作为子 Agent 运行。
    """
    run_logger.start_new_run()
    rounds_since_todo: int = 0
    step_count: int = 1
    run_start_time = perf_counter()
    while True:
        step_start_time = perf_counter()
        console.print(
            f"\n[bold white]{'━'*20} [ 第 {step_count} 轮思考开始 ] {'━'*20}[/bold white]"
        )

        current_context = context_manager_override if context_manager_override else context_manager
        current_tools = tools_override if tools_override is not None else TOOLS

        # 使用上下文管理器组装最终 Prompt
        system_prompt, messages = current_context.build_prompt(session)

        # 1. 显示即将发给 LLM 的包裹
        console.print("\n[bold blue][发送给 LLM 的数据包裹 (发包)][/bold blue]")
        for msg in messages[-2:]:
            if isinstance(msg, dict):
                role = str(msg.get("role", "UNKNOWN")).upper()
                content_str = str(msg.get("content", "")).replace("\n", " ")
                content_disp = content_str[:200] + (
                    "..." if len(content_str) > 200 else ""
                )
                console.print(f"  - [cyan]{role}[/cyan]: {content_disp}")

        # 使用 litellm 进行对话补全
        try:
            run_logger.log_request(messages, current_tools)
            with console.status("[bold cyan]Agent is thinking...", spinner="dots"):
                response = get_completion(
                    messages=messages,
                    system=system_prompt,  # 使用包含记忆的系统提示提示词
                    tools=current_tools,
                    max_tokens=8000,
                )
        except RetryExhaustedError as e:
            console.print(f"\n[bold red]❌ LLM API 请求重试耗尽终止: {e}[/bold red]")
            session.add_message("assistant", "[System: Network timeout or API failure. Please retry your request.]")
            return "ERROR_LLM_TIMEOUT"
        except Exception as e:
            console.print(f"\n[bold red]❌ 出现严重系统异常: {e}[/bold red]")
            return "ERROR_SYSTEM"

        # 获取消息对象
        raw_msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        # 2. 显示 LLM 的响应和思考
        console.print(f"\n[bold green][LLM 响应 (接包)][/bold green]")
        console.print(f"  - 停止原因: {finish_reason}")

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

        run_logger.log_response(
            content=raw_msg.content, 
            tool_calls=msg_dict.get("tool_calls"), 
            finish_reason=str(finish_reason)
        )

        # 【教育打印 1：大模型的内在思考 / 推理文字】
        if raw_msg.content:
            console.print(
                f"  - [bold magenta]🧠 思考内容[/bold magenta]:\n{raw_msg.content}"
            )

        # 如果没有工具调用且内容为空，可能发生了异常中断
        if not raw_msg.tool_calls and not raw_msg.content:
            console.print(
                "[red]⚠️  Warning: Agent returned empty response. Retrying with a nudge...[/red]"
            )
            session.add_message("user", "Please continue with the task.")
            continue

        # 如果没有工具调用，则认为是最终回复，退出循环
        if not raw_msg.tool_calls:
            console.print(
                f"\n[bold yellow]🏁 [任务完成 / 最终回复]: Agent 停止调用工具。退出循环。[/bold yellow]"
            )
            # ── Auto-fact extraction ────────────────────────────────────────
            # When the agent finishes, extract any important long-term facts
            # from this turn and append them (never overwrite) to MEMORY.md.
            if not is_sub_agent:
                _auto_extract_facts(session, raw_msg.content or "")
            return

        used_todo = False
        tool_calls = raw_msg.tool_calls or []
        tool_calls_count = len(tool_calls)

        # 处理并收集工具调用结果 (干活)
        for i, tool_call in enumerate(tool_calls, 1):
            function_name = tool_call.function.name
            # 解析参数
            args = json.loads(tool_call.function.arguments)

            # --- 审批拦截逻辑 ---
            if function_name in APPROVAL_TOOLS:
                console.print(
                    f"\n[bold red]⚠️  拦截了需要审批的工具: {function_name}[/bold red]"
                )
                session.metadata["pending_tool"] = {
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "args": args,
                }
                return "PAUSED_FOR_APPROVAL"

            # 【教育打印 2：大模型决定使用的工具和参数】
            console.print(
                f"\n[bold yellow]🛠️  [执行工具 (干活)] ({i}/{tool_calls_count}): {function_name}[/bold yellow]"
            )
            
            # 截断超长参数以美化打印输出
            truncated_args = {}
            for k, v in args.items():
                v_str = str(v)
                truncated_args[k] = v_str[:200] + "..." if len(v_str) > 200 else v
            console.print(f"  - 传入参数: {truncated_args}")

            handler = TOOL_HANDLERS.get(function_name)
            start_time = time.time()
            try:
                with console.status(
                    f"[bold magenta]⏳ 正在本地机器执行 {function_name}...",
                    spinner="bouncingBar",
                ):
                    output = (
                        handler(**args) if handler else f"Unknown tool: {function_name}"
                    )
                success_flag = not str(output).startswith("Unknown tool:")
                run_logger.log_tool_result(function_name, args, success_flag, str(output) if success_flag else None, str(output) if not success_flag else None)
            except Exception as e:
                error_trace = traceback.format_exc()
                output = f"Tool execution failed: {type(e).__name__}: {str(e)}\n\nTraceback:\n{error_trace}"
                run_logger.log_tool_result(function_name, args, False, None, output)
            cost_time = time.time() - start_time

            # 【教育打印 3：本地代码执行的结果】
            # 截断太长的输出
            short_output = str(output)[:300].replace("\n", " ") + (
                "..." if len(str(output)) > 300 else ""
            )
            console.print(
                f"  - [bold green]执行结果[/bold green] (耗时 {cost_time:.2f}s): {short_output}"
            )

            # 添加工具调用结果到 session
            session.add_message(
                "tool", str(output), tool_call_id=tool_call.id, name=function_name
            )

            if function_name == "todo":
                used_todo = True

        # 4. 回传结果
        if tool_calls:
            console.print(
                "\n[bold cyan]🔄 [回传数据][/bold cyan]: 将工具结果追加到 messages，准备进入下一轮..."
            )

        # 处理待办事项提醒逻辑
        rounds_since_todo = 0 if used_todo else rounds_since_todo + 1
        if rounds_since_todo >= 3:
            console.log(
                "[yellow]Step: Injecting todo reminder to keep agent on track.[/yellow]"
            )
            # 注入提醒消息
            session.add_message("user", "<reminder>Update your todos.</reminder>")

        step_elapsed = perf_counter() - step_start_time
        total_elapsed = perf_counter() - run_start_time
        console.print(f"\n[dim]⏱️ 第 {step_count} 轮完成，本轮耗时 {step_elapsed:.2f}s (Agent 累计运行: {total_elapsed:.2f}s)[/dim]")

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
        status = agent_loop(session)

        # Handle console approval loop
        while status == "PAUSED_FOR_APPROVAL":
            pending = session.metadata.get("pending_tool")
            if not pending:
                break

            console.print(
                Panel(
                    f"[bold yellow]⚠️  Approval Required for Tool:[/bold yellow] [cyan]{pending['name']}[/cyan]\n"
                    f"[bold white]Arguments:[/bold white] {json.dumps(pending['args'], indent=2)}",
                    title="Action Required",
                    border_style="yellow",
                )
            )

            choice = Prompt.ask("Approve this action?", choices=["y", "n"], default="y")

            if choice == "y":
                handler = TOOL_HANDLERS.get(pending["name"])
                if handler:
                    start_time = time.time()
                    with console.status(
                        f"[bold magenta]⏳ Executing {pending['name']}...",
                        spinner="bouncingBar",
                    ):
                        try:
                            output = handler(**pending["args"])
                            run_logger.log_tool_result(pending["name"], pending["args"], True, str(output), None)
                        except Exception as e:
                            error_trace = traceback.format_exc()
                            output = f"Tool execution failed: {type(e).__name__}: {str(e)}\n\nTraceback:\n{error_trace}"
                            run_logger.log_tool_result(pending["name"], pending["args"], False, None, output)
                    cost_time = time.time() - start_time
                    console.print(
                        f"  - [bold green]执行结果[/bold green] (耗时 {cost_time:.2f}s): {str(output)[:300]}"
                    )
                else:
                    output = f"Error: Unknown tool {pending['name']}"

                session.add_message(
                    "tool",
                    str(output),
                    tool_call_id=pending["tool_call_id"],
                    name=pending["name"],
                )
            else:
                session.add_message(
                    "tool",
                    "User rejected the action.",
                    tool_call_id=pending["tool_call_id"],
                    name=pending["name"],
                )

            session.metadata.pop("pending_tool", None)
            # Continue the agent's logic after tool execution
            status = agent_loop(session)

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
