class RAGRetriever:
    def __init__(self, model_name="nomic-embed-text:latest"):
        """
        初始化 RAG 检索器
        model_name: 使用的 ollama embedding 模型名称
        """
        self.model_name = model_name
        self.index = None
        self.docs = []
        
    def _get_embedding(self, text: str) -> list:
        try:
            import ollama
            response = ollama.embeddings(
                model=self.model_name,
                prompt=text
            )
            return response['embedding']
        except Exception as e:
            print(f"Error getting embedding for text: {e}")
            return [0.0] * 768

    def add_texts(self, texts: list):
        """添加文本列表到索引中"""
        if not texts:
            return
            
        import numpy as np
        import faiss
            
        self.docs.extend(texts)
        
        # 使用 Ollama 逐个获取 embedding
        embeddings = []
        for text in texts:
            emb = self._get_embedding(text)
            embeddings.append(emb)
            
        # 构建 NumPy 数组
        embeddings_np = np.array(embeddings).astype('float32')
        
        # 构建/更新 FAISS 索引
        if self.index is None:
            dim = embeddings_np.shape[1]
            self.index = faiss.IndexFlatL2(dim)
            
        self.index.add(embeddings_np)

    def load_dataset(self, dataset_name="OxRML/MADQA", split="train", limit=20):
        """从 HuggingFace datasets 加载数据（方便测试）"""
        try:
            from datasets import load_dataset
            print(f"Loading '{dataset_name}' ...", flush=True)
            ds = load_dataset(dataset_name)
            data = ds[split]
            
            def get_doc(item):
                if isinstance(item, str): return item
                if "context" in item: return item["context"]
                if "text" in item: return item["text"]
                if "passage" in item: return item["passage"]
                return str(item)
                
            docs = [get_doc(item) for item in data[:limit]]
            self.add_texts(docs)
            print(f"Successfully loaded and indexed {len(docs)} documents.")
        except ImportError:
            print("Warning: datasets library not installed, skipping default dataset.")
        except Exception as e:
            print(f"Failed to load dataset: {e}")

    def search(self, query: str, k: int = 3) -> list:
        """根据 query 检索最相关的 k 个文档"""
        if self.index is None or not self.docs:
            return ["知识库为空，无法检索。"]
            
        import numpy as np
        q_emb = np.array([self._get_embedding(query)]).astype('float32')
        k = min(k, len(self.docs))
        D, I = self.index.search(q_emb, k=k)
        
        return [self.docs[i] for i in I[0]]

if __name__ == "__main__":
    # 作为单独运行时的测试
    retriever = RAGRetriever()
    test_docs = [
        "巴黎是法国的首都。",
        "苹果是一家著名的科技公司。",
        "Python 是一种高级编程语言，非常适合数据科学。",
        "Ollama 允许你在本地轻松运行各大开源语言模型。"
    ]
    retriever.add_texts(test_docs)
    
    query = "法国的首都在哪？"
    print(f"\nQuestion: {query}")
    print("Retrieved:")
    for i, doc in enumerate(retriever.search(query, k=2)):
        print(f"[{i+1}] {doc}")
