import sys
from pathlib import Path

# 确保能导入根目录下的 rag.py
sys.path.append(str(Path(__file__).parent.parent))
from rag import RAGRetriever

# 全局检索器实例
rag_retriever = RAGRetriever()

class RAGTool:
    """如果以后需要基于类的接口，可以保留这个类，但在本系统中主要使用函数。"""
    name = "rag_search"
    description = "用来检索知识库，回答需要背景知识的问题"

    def __init__(self, retriever):
        self.retriever = retriever

    def run(self, query):
        docs = self.retriever.search(query)
        return "\n".join(docs)

def rag_search(query: str) -> str:
    """检索知识库以获得背景信息，供 Agent 调用。"""
    try:
        if not rag_retriever.docs:
            rag_retriever.load_dataset(limit=10)
            # 补充兜底文档
            backup_docs = [
                "本文档是本地知识库的示例。AI代理(Agent)可以调用rag_search工具检索这个知识库。",
                "本项目是一个能自主思考、自动调用各种工具的 AI 代理平台（first-real-agent）。",
                "你可以通过定义 .tasks 或 skills 文件夹中的文件来扩展功能。"
            ]
            rag_retriever.add_texts(backup_docs)
            
        docs = rag_retriever.search(query, k=3)
        if not docs:
            return "No relevant information found."
        return "\n".join([f"- {doc}" for doc in docs])
    except Exception as e:
        return f"Error during RAG search: {e}"

# --- 定义 Agent 需要的接口 ---
TOOL_HANDLERS = {
    "rag_search": lambda **kw: rag_search(kw.get("query")),
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "rag_search",
            "description": "用来检索本地知识库，回答需要额外背景知识或特定文档内容的问题。遇到涉及本项目、本地特定领域常识或记忆不清楚的明确事务时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "用于从知识库检索相关信息的搜索查询词或陈述句。",
                    }
                },
                "required": ["query"],
            },
        },
    }
]