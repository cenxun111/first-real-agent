"""
Context Manager — Professional implementation.

Responsibilities:
  1. Assemble a clean, sliding-window message history for the LLM.
  2. Inject long-term memory with explicit section markers.
  3. Suppress noise (tool messages, reminder injections) from the history window.
"""

from __future__ import annotations

from memory import LongTermMemory
from session.manager import Session

# ───────────────────────── constants ─────────────────────────
# How many of the most recent TURNS (user + assistant pairs) to
# pass to the LLM.  Each turn ≈ 2 messages, so 10 turns ≈ 20 msgs.
_MAX_WINDOW_TURNS: int = 10

# Roles that are always stripped from the window to reduce noise.
# "tool" results (raw tool output) are bulky and confuse frontier LLMs
# when stacked across many loops; we keep only the assistant's reasoning.
_STRIP_ROLES: frozenset[str] = frozenset()  # set to {"tool"} if you want to strip tool results

# Message content prefixes that are injected by the agent loop itself
# and should NOT be forwarded to the LLM as user input.
_STRIP_CONTENT_PREFIXES: tuple[str, ...] = ("<reminder>",)

# ─────────────────────────────────────────────────────────────


def _is_noisy(msg: dict) -> bool:
    """Return True if a message should be excluded from the LLM window.

    Strips:
    - Internal agent reminder injections (e.g. <reminder>Update todos</reminder>)
    - Any role listed in _STRIP_ROLES
    """
    if msg.get("role") in _STRIP_ROLES:
        return True
    content = msg.get("content") or ""
    if isinstance(content, str):
        return any(content.startswith(p) for p in _STRIP_CONTENT_PREFIXES)
    return False



class ContextManager:
    """Assembles the final (system_prompt, messages) pair for the LLM call.

    Design goals:
    - Never pass the whole session history — only the last N turns.
    - Clearly separate long-term memory from the recent conversation
      via section markers, preventing facts from bleeding into the chat flow.
    - Strip internal agent scaffolding messages that are meaningless to the LLM.
    """

    def __init__(
        self,
        base_system_prompt: str,
        memory_store: LongTermMemory,
        max_window_turns: int = _MAX_WINDOW_TURNS,
    ) -> None:
        self.base_system_prompt = base_system_prompt
        self.memory_store = memory_store
        self.max_window_turns = max_window_turns

    # ─────────────────── public API ───────────────────

    def build_prompt(self, session: Session) -> tuple[str, list[dict]]:
        """Build the (system_prompt, messages) tuple for the next LLM call.

        Returns:
            system_prompt: The full system prompt with memory injected.
            messages:      A clean, windowed list of recent messages.
        """
        raw_history = session.get_history()
        clean_history = [m for m in raw_history if not _is_noisy(m)]

        # 尝试提取最近的一个用户问题，用于检索相关的长期事实
        query = ""
        for msg in reversed(clean_history):
            if str(msg.get("role", "")).lower() == "user":
                query = str(msg.get("content", ""))
                break
        
        # 检索相关的长期事实
        relevant_memory = self.memory_store.recall(query) if query else ""
        
        system_prompt = self._build_system_prompt(relevant_memory)
        return system_prompt, clean_history

    # ─────────────────── private helpers ──────────────

    def _build_system_prompt(self, relevant_memory: str) -> str:
        """Compose the system prompt with clearly separated memory sections."""
        parts = [self.base_system_prompt]

        # ── Long-term memory block ──────────────────────────────────────────
        if relevant_memory and "暂无长期记忆" not in relevant_memory:
            parts.append(
                "\n\n"
                "═══════════════════════════════════════════════\n"
                "  LONG-TERM MEMORY  (relevant facts)\n"
                "═══════════════════════════════════════════════\n"
                f"{relevant_memory}\n"
                "═══════════════════════════════════════════════"
            )

        return "".join(parts)

    def _get_history_snippet(self, max_lines: int = 10) -> str:
        """Return the last *max_lines* lines of HISTORY.md for context."""
        history_file = self.memory_store.history_file
        if not history_file.exists():
            return ""
        lines = history_file.read_text(encoding="utf-8").strip().splitlines()
        if not lines:
            return ""
        snippet = "\n".join(lines[-max_lines:])
        return snippet
