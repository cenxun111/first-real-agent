import os
from datetime import datetime

class LongTermMemory:
    """
    负责 Agent 的长期记忆管理。
    所有事实将以 Markdown 列表的形式持久化追加到文件中。
    """
    def __init__(self, file_path="data/memory.md"):
        self.file_path = file_path
        
        # 1. 确保目录存在
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        # 2. 如果文件不存在，初始化一个好看的 Markdown 头部
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write("# Agent 长期核心记忆库\n")
                f.write("> 这里记录了跨越会话的重要事实、用户偏好和历史关键决策。\n\n")

    def remember(self, fact: str) -> str:
        """
        【写操作】存入新记忆。
        核心修复：使用 'a' (append) 模式，永远追加，绝不覆盖！
        """
        # 加上时间戳，让 LLM 知道这个记忆是多久以前的
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(f"- [{timestamp}] {fact}\n")
            
        return f"记忆已永久保存: {fact}"

    def recall(self, query: str = None, max_items: int = 15) -> str:
        """
        【读操作】检索记忆。
        如果记忆太多，全发给 LLM 会导致 Token 爆炸或产生幻觉。
        这里实现了一个轻量级的“关键词检索 + 最近记忆”策略。
        """
        if not os.path.exists(self.file_path):
            return "暂无长期记忆。"

        with open(self.file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 过滤掉 MD 的标题和空行，只提取记忆条目
        facts =[line.strip() for line in lines if line.strip().startswith("- [")]

        if not facts:
            return "暂无长期记忆。"

        # 如果传入了当前的问题 (query)，尝试做简单的关键词匹配
        if query:
            # 增加一些常用的停用词，避免因为 'the', 'is' 等词误匹配
            stop_words = {"the", "and", "about", "your", "that", "this", "what", "with", "from"}
            keywords = set(query.lower().replace("？", "").replace("。", "").split())
            keywords = {k for k in keywords if len(k) > 1 and k not in stop_words}
            
            relevant_facts =[]
            for fact in facts:
                if any(k in fact.lower() for k in keywords):
                    relevant_facts.append(fact)
            
            if relevant_facts:
                return "\n".join(relevant_facts[-max_items:])
                
        # 默认情况：返回最近的 max_items 条记忆
        return "\n".join(facts[-max_items:])

# 实例化一个全局的记忆库对象，供其他模块调用
memory_store = LongTermMemory("data/long_term_memory.md")