from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

# 从现有 agent 中导入所需的组件
from agent import agent_loop, session_manager

app = FastAPI(title="Agent Web API", description="FastAPI wrapper for the intelligent agent.")

# 定义请求数据模型
class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        # 获取或创建对应 session_id 的会话
        session = session_manager.get_or_create(request.session_id)
        
        # 将用户的新消息添加到会话中
        session.add_message("user", request.message)
        
        # 运行核心终端代理逻辑 (阻塞执行直至该轮思考结束)
        agent_loop(session)
        
        # 保存会话状态到磁盘
        session_manager.save(session)
        
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
