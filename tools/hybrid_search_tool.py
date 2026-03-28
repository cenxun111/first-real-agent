# tools/hybrid_search_tool.py
import os
import hashlib
import json
from pathlib import Path
from typing import List, Dict

import jieba
import chromadb
from rank_bm25 import BM25Okapi
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- 配置与模型初始化 ---

KB_DIR = Path("./knowledge_base/refined")
DB_PATH = Path("./chroma_db")
METADATA_FILE = DB_PATH / "indexing_metadata.json"

# Ollama Embedding 接口封装
def get_ollama_embedding(text: str) -> List[float]:
    try:
        import ollama
        response = ollama.embeddings(model="nomic-embed-text", prompt=text)
        return response["embedding"]
    except Exception as e:
        print(f"Embedding error: {e}")
        return [0.0] * 768 # 兜底向量

class KnowledgeBaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KnowledgeBaseManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        # 1. 初始化 ChromaDB
        self.chroma_client = chromadb.PersistentClient(path=str(DB_PATH))
        self.collection = self.chroma_client.get_or_create_collection(
            name="company_docs",
            metadata={"hnsw:space": "cosine"}
        )
        
        # 2. 初始化文本分块器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            length_function=len,
        )
        
        # 3. 加载索引状态元数据
        self.metadata = self._load_metadata()
        
        # 4. 同步文档并构建索引
        self._sync_and_index()
        
        # 5. 初始化 BM25 (基于当前所有文档块)
        self._init_bm25()

    def _load_metadata(self) -> Dict:
        if METADATA_FILE.exists():
            return json.loads(METADATA_FILE.read_text())
        return {}

    def _save_metadata(self):
        DB_PATH.mkdir(parents=True, exist_ok=True)
        METADATA_FILE.write_text(json.dumps(self.metadata))

    def _calculate_hash(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def _sync_and_index(self):
        KB_DIR.mkdir(parents=True, exist_ok=True)
        files = list(KB_DIR.glob("*.md"))
        
        for file_path in files:
            content = file_path.read_text(encoding="utf-8")
            file_hash = self._calculate_hash(content)
            
            # 如果文件已更新或未索引
            if self.metadata.get(file_path.name) != file_hash:
                print(f"Indexing {file_path.name}...")
                
                # 删除旧块
                self.collection.delete(where={"source": file_path.name})
                
                # 分块
                chunks = self.text_splitter.create_documents(
                    [content], 
                    metadatas=[{"source": file_path.name}]
                )
                
                # 添加新块到 Chroma
                ids = [f"{file_path.name}_{i}" for i in range(len(chunks))]
                embeddings = [get_ollama_embedding(c.page_content) for c in chunks]
                self.collection.upsert(
                    ids=ids,
                    documents=[c.page_content for c in chunks],
                    metadatas=[c.metadata for c in chunks],
                    embeddings=embeddings
                )
                
                # 更新元数据
                self.metadata[file_path.name] = file_hash
        
        self._save_metadata()

    def _init_bm25(self):
        # 获取所有文档内容用于 BM25
        results = self.collection.get()
        self.all_chunks = results['documents'] if results['documents'] else []
        
        if self.all_chunks:
            tokenized_corpus = [list(jieba.cut(doc)) for doc in self.all_chunks]
            self.bm25 = BM25Okapi(tokenized_corpus)
        else:
            self.bm25 = None

    def hybrid_search(self, query: str, top_k: int = 5) -> str:
        if not self.all_chunks:
            return "知识库目前为空，请先导入文件。"
            
        # 1. 向量搜索
        query_embed = get_ollama_embedding(query)
        v_results = self.collection.query(
            query_embeddings=[query_embed],
            n_results=top_k
        )
        v_docs = v_results['documents'][0] if v_results['documents'] else []
        
        # 2. 关键词搜索 (BM25)
        bm25_docs = []
        if self.bm25:
            tokenized_query = list(jieba.cut(query))
            bm25_docs = self.bm25.get_top_n(tokenized_query, self.all_chunks, n=top_k)
        
        # 3. 结果去重与合并
        combined = list(dict.fromkeys(v_docs + bm25_docs)) # 保持顺序去重
        
        if not combined:
            return "未找到匹配的相关信息。"
            
        context = "\n\n---\n\n".join(combined[:top_k])
        return f"从知识库中检索到的相关片段：\n\n{context}"

# 全局管理器实例（按需初始化）
_kb_manager = None
def get_kb_manager():
    global _kb_manager
    if _kb_manager is None:
        _kb_manager = KnowledgeBaseManager()
    return _kb_manager

# --- Agent 接口定义 ---

def hybrid_search_handler(query: str) -> str:
    manager = get_kb_manager()
    return manager.hybrid_search(query)

TOOL_HANDLERS = {
    "hybrid_search": lambda **kw: hybrid_search_handler(kw.get("query")),
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "hybrid_search",
            "description": "搜索本地知识库。支持语义理解和关键词精准匹配。适用于回答公司业务、本地文档内容或规章制度等需要检索知识的问题。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词或具体问题"}
                },
                "required": ["query"]
            }
        }
    }
]