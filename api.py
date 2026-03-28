from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path

# 从现有 agent 中导入所需的组件
from agent import agent_loop, session_manager
from context import ContextManager
from memory import memory_store

app = FastAPI(title="Agent Web API", description="FastAPI wrapper for the intelligent agent.")

# 允许 React 开发服务器 (localhost:3000) 跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 定义请求数据模型
class ChatRequest(BaseModel):
    session_id: str
    message: str

class ApproveRequest(BaseModel):
    session_id: str
    action: str  # "approve" or "reject"

ROUTER_PROMPT = """
你是公司的高级前台助理。
你必须先理解用户的意图，如果涉及专业操作（查报销、写代码），
你必须使用 `call_sub_agent` 工具将任务派发给对应的专家。
如果你自己能回答（比如简单的问候），则直接回答。
"""

# 2. 路由提示词已准备，在聊天路由中直接作为覆盖上下文注入主循环

@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        # 获取或创建对应 session_id 的会话
        session = session_manager.get_or_create(request.session_id)
        
        # 将用户的新消息添加到会话中
        session.add_message("user", request.message)
        
        # 运行核心终端代理逻辑，并注入前台提示词
        router_context = ContextManager(ROUTER_PROMPT, memory_store)
        status = agent_loop(session, context_manager_override=router_context)
        
        # 保存会话状态到磁盘
        session_manager.save(session)
        
        if status == "PAUSED_FOR_APPROVAL":
            pending = session.metadata.get("pending_tool", {})
            return {"status": "PAUSED_FOR_APPROVAL", "pending_tool": pending}
            
        # 获取更新后的历史记录
        history = session.get_history()
        
        # 提取最后一条(应当是 assistant 的最新最终回复)
        response_content = history[-1].get("content", "")
        
        # 将可能的多模态/块状结构转换为纯文本
        if isinstance(response_content, list):
            text_parts = [
                block.get("text", "")
                for block in response_content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            response_content = "\n".join(text_parts)
            
        return {"status": "success", "response": response_content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/approve")
def approve(request: ApproveRequest):
    try:
        session = session_manager.get_or_create(request.session_id)
        pending = session.metadata.get("pending_tool")
        if not pending:
            raise HTTPException(status_code=400, detail="No pending tool found.")
            
        function_name = pending["name"]
        args = pending["args"]
        tool_call_id = pending["tool_call_id"]
        
        if request.action == "approve":
            from agent import TOOL_HANDLERS
            handler = TOOL_HANDLERS.get(function_name)
            if handler:
                output = handler(**args)
            else:
                output = f"Error: Unknown tool {function_name}"
            
            session.add_message(
                "tool", str(output), tool_call_id=tool_call_id, name=function_name
            )
        else:
            session.add_message(
                "tool", "User rejected the action.", tool_call_id=tool_call_id, name=function_name
            )
            
        session.metadata.pop("pending_tool", None)
        
        router_context = ContextManager(ROUTER_PROMPT, memory_store)
        status = agent_loop(session, context_manager_override=router_context)
        session_manager.save(session)
        
        if status == "PAUSED_FOR_APPROVAL":
            pending = session.metadata.get("pending_tool", {})
            return {"status": "PAUSED_FOR_APPROVAL", "pending_tool": pending}
            
        history = session.get_history()
        response_content = history[-1].get("content", "")
        if isinstance(response_content, list):
            text_parts = [
                block.get("text", "")
                for block in response_content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            response_content = "\n".join(text_parts)
            
        return {"status": "success", "response": response_content}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 静态文件挂载与路由
STATIC_DIR = Path(__file__).parent / "static"

# 提供前端静态文件支持
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def read_root():
    """访问根路径时返回 static/index.html"""
    return FileResponse(str(STATIC_DIR / "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
