# tools/ingest_tools.py
import subprocess
import os
import shutil
from pathlib import Path

# --- 核心函数实现 ---
from langchain_text_splitters import RecursiveCharacterTextSplitter
from tools.hybrid_search_tool import get_kb_manager, get_ollama_embedding

def process_and_save(file_path: str, content: str) -> str:
    """
    保存文本到知识库目录，并对其进行分块存入向量数据库，确保与全局知识库同步。
    """
    try:
        # 0. 首先将文件保存到 knowledge_base/refined 目录
        file_name = os.path.basename(file_path)
        if not file_name.endswith(".md"):
            file_name += ".md"
            
        kb_dir = Path("./knowledge_base/refined")
        kb_dir.mkdir(parents=True, exist_ok=True)
        safe_path = kb_dir / file_name
        
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)

        # 1. 获取管理器并准备向量库
        kb_manager = get_kb_manager()
        collection = kb_manager.collection
        
        # 2. 执行切分（复用管理器定义的分块逻辑）
        chunks = kb_manager.text_splitter.split_text(content)
        if not chunks:
            return f"文件内容为空，已保存为 {safe_path}，但无需切分。"

        # 2.5. 将分块内容保存到单独的文件夹中
        base_name = os.path.splitext(file_name)[0]
        chunks_dir = Path("./knowledge_base/chunks") / base_name
        chunks_dir.mkdir(parents=True, exist_ok=True)
        
        for i, chunk_text in enumerate(chunks):
            chunk_file_path = chunks_dir / f"{base_name}_chunk_{i}.md"
            with open(chunk_file_path, "w", encoding="utf-8") as f:
                f.write(chunk_text)
        
        # 3. 准备批量数据
        ids = [f"{base_name}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": file_name, "index": i} for i in range(len(chunks))]
        
        # 4. 批量获取向量
        embeddings = [get_ollama_embedding(chunk) for chunk in chunks]
        
        # 5. 批量写入 ChromaDB
        collection.upsert(
            ids=ids,
            documents=chunks,
            metadatas=metadatas,
            embeddings=embeddings
        )

        return f"✅ 成功！知识点已存为本地文件 {safe_path}，并切分为 {len(chunks)} 个块存入检索库及 {chunks_dir} 目录下的独立MD文件中。"
    except Exception as e:
        return f"处理失败：{str(e)}"

def convert_file_to_md(file_path: str, file_type: str = None) -> str:
    """
    将 PDF 或 EPUB 文件转换为 Markdown 格式。
    返回转换后的文本内容摘要或成功信息。
    """
    file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        return f"错误：找不到文件 {file_path}"
    
    if not file_type:
        file_type = file_path.split('.')[-1].lower()

    try:
        if file_type == "pdf":
            # 优先尝试 marker_single (高质量转换)
            if shutil.which("marker_single"):
                result = subprocess.run(
                    ["marker_single", file_path, "--batch_multiplier", "2"],
                    capture_output=True, text=True, timeout=300
                )
                if result.returncode == 0:
                    return f"PDF 转换成功 (使用 marker)。预览：\n{result.stdout[:500]}..."
            
            # 备选方案：pdfplumber (快速提取文本)
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text = ""
                    for page in pdf.pages[:20]: # 限制页数以防过长
                        text += page.extract_text() or ""
                    return f"PDF 文本提取成功 (使用 pdfplumber)。预览：\n{text[:1000]}..."
            except ImportError:
                return "错误：未安装 pdfplumber，且找不到 marker_single 命令。"

        elif file_type == "epub":
            if shutil.which("pandoc"):
                output_path = file_path.rsplit('.', 1)[0] + ".md"
                subprocess.run(["pandoc", file_path, "-o", output_path], check=True)
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return f"EPUB 转换成功 (使用 pandoc)。内容摘要：\n{content[:1000]}..."
            else:
                return "错误：未安装 pandoc，无法转换 EPUB。"

        else:
            return f"错误：不支持的文件类型 {file_type}。目前仅支持 pdf, epub。"

    except Exception as e:
        return f"转换失败：{str(e)}"

def save_refined_knowledge(filename: str, content: str) -> str:
    """
    将清洗后的内容保存到知识库。
    """
    if not filename.endswith(".md"):
        filename += ".md"
    
    kb_dir = Path("./knowledge_base/refined")
    kb_dir.mkdir(parents=True, exist_ok=True)
    
    safe_path = kb_dir / filename
    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return f"成功：知识点已保存至 {safe_path}。系统将自动进行索引。"

# --- Agent 接口定义 ---

TOOL_HANDLERS = {
    "convert_file_to_md": lambda **kw: convert_file_to_md(kw.get("file_path"), kw.get("file_type")),
    "save_refined_knowledge": lambda **kw: save_refined_knowledge(kw.get("filename"), kw.get("content")),
    "process_and_save": lambda **kw: process_and_save(kw.get("file_path"), kw.get("content")),
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "convert_file_to_md",
            "description": "将 PDF 或 EPUB 文件转换为纯文本或 Markdown。建议在处理本地长文档前调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "原始文件的绝对路径"},
                    "file_type": {"type": "string", "enum": ["pdf", "epub"], "description": "文件类型（可选）"}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_refined_knowledge",
            "description": "将经过 LLM 优化、去噪并添加元数据后的知识内容保存到本地检索库。这会让 Agent 记住这些知识。",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "保存的文件名（如 tutorial.md）"},
                    "content": {"type": "string", "description": "完整的知识点内容"}
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "process_and_save",
            "description": "对经过清洗的内容进行高级分块处理，并直接存入向量检索数据库。适用于需要立即检索的大型知识片段。",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "源文件路径或名称（用于溯源）"},
                    "content": {"type": "string", "description": "要分块并入库的内容"}
                },
                "required": ["file_path", "content"]
            }
        }
    }
]