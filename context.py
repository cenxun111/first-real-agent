"""Context management for the agent. Assembles the final Prompt for the LLM."""

from memory import MemoryStore
from session.manager import Session

class ContextManager:
    """Responsible for assembling the final system prompt and message history."""

    def __init__(self, base_system_prompt: str, memory_store: MemoryStore):
        self.base_system_prompt = base_system_prompt
        self.memory_store = memory_store

    def build_prompt(self, session: Session) -> tuple[str, list[dict]]:
        """
        Assemble the final prompt for the LLM.
        
        Args:
            session: The active conversation session containing message history.
            
        Returns:
            tuple: (system_prompt: str, messages: list[dict])
        """
        # 获取会话历史（已自动包含当前消息）
        messages = session.get_history()

        # 获取长期记忆并注入系统提示词
        lt_memory = self.memory_store.get_memory_context()
        if lt_memory:
            system_prompt = f"{self.base_system_prompt}\n\n{lt_memory}"
        else:
            system_prompt = self.base_system_prompt

        return system_prompt, messages
