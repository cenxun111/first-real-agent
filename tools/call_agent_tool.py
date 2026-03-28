# tools/call_agent_tool.py
import os
import re
import uuid
from tools.base import BaseTool

class CallAgentTool(BaseTool):
    @property
    def name(self) -> str:
        return "call_sub_agent"

    @property
    def description(self) -> str:
        return "当你（前台）遇到无法处理的专业问题时，调用此工具将任务外包给特定领域的专家智能体。"

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string", 
                    "description": "专家名称。目前可选：finance_expert, coder_expert"
                },
                "task_detail": {
                    "type": "string",
                    "description": "详细的任务背景和你要专家做的事"
                }
            },
            "required": ["agent_name", "task_detail"]
        }

    def execute(self, agent_name: str, task_detail: str) -> str:
        import sys
        from agent import agent_loop, WORKDIR
        from tools.loader import tool_manager
        from session.manager import SessionManager
        from context import ContextManager
        from memory import memory_store
        
        file_path = f"agents/{agent_name}.md"
        if not os.path.exists(file_path):
            return f"转接失败：找不到名为 {agent_name} 的专家简章 (路径: {file_path})。"

        # 1. 解析 Markdown 文件 (提取元数据和 Prompt)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # 简单提取 tools 列表
        tools_match = re.search(r"# tools:\s*\[(.*?)\]", content)
        allowed_tools_names = []
        if tools_match:
            allowed_tools_names = [t.strip() for t in tools_match.group(1).split(",") if t.strip()]
            
        # 获取允许使用的工具 Schema
        all_schemas = tool_manager.get_tools_schemas()
        allowed_tools_schemas = [s for s in all_schemas if s["function"]["name"] in allowed_tools_names]
        
        # 如果没匹配到也没关系，可能这个专家只聊天不使用工具
        system_prompt = content
        
        print(f"\n[🔄 OpenClaw 路由] 正在唤醒子智能体: {agent_name}...")
        
        # 2. 动态实例化子会话
        session_id = f"sub_{agent_name}_{uuid.uuid4().hex[:6]}"
        temp_session_manager = SessionManager(WORKDIR)
        sub_session = temp_session_manager.get_or_create(session_id)
        
        sub_session.add_message("user", task_detail)
        sub_context = ContextManager(system_prompt, memory_store)
        
        # 3. 运行子循环
        agent_loop(
            sub_session, 
            context_manager_override=sub_context, 
            tools_override=allowed_tools_schemas,
            is_sub_agent=True
        )
        
        # 4. 获取结果
        history = sub_session.get_history()
        # 过滤出最后一条 assistant 的话
        assistant_msgs = [m for m in history if m.get("role") == "assistant" and m.get("content")]
        result = assistant_msgs[-1].get("content") if assistant_msgs else "【无文本回复】"
        
        # 清理临时会话（不在磁盘上保留无关内容）
        sub_session.clear()
        
        return f"{agent_name} 专家的处理结果：\n{result}"