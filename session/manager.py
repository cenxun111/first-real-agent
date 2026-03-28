"""Session management for conversation history."""

import json
import shutil
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from loguru import logger

def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)
    return path

def safe_filename(filename: str) -> str:
    """Convert a string to a safe filename."""
    return re.sub(r"[^a-zA-Z0-9_\-]", "_", filename)

def get_legacy_sessions_dir() -> Path:
    """Return the legacy sessions directory."""
    return Path.home() / ".nanobot" / "sessions"

def serialize_message(msg: dict[str, Any]) -> str:
    role = msg.get("role", "unknown")
    timestamp = msg.get("timestamp", datetime.now().isoformat())
    content = msg.get("content") or ""
    
    parts = [f"### [{role}] ({timestamp})"]
    
    sys_data = {}
    for k in ("tool_calls", "tool_call_id", "name"):
        if k in msg:
            sys_data[k] = msg[k]
            
    if sys_data:
        parts.append(f"```json\n{json.dumps(sys_data, ensure_ascii=False)}\n```")
        
    if content:
        parts.append(content)
        
    return "\n".join(parts)


def parse_session_md(text: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    metadata = {}
    messages = []
    
    lines = text.splitlines()
    if not lines:
        return metadata, messages
        
    if lines[0].strip() == "---":
        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                end_idx = i
                break
        if end_idx != -1:
            for line in lines[1:end_idx]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    metadata[k.strip()] = v.strip()
            lines = lines[end_idx+1:]
            
    content = "\n".join(lines)
    pattern = re.compile(r"^### \[([a-zA-Z]+)\] \((.*?)\)\n", re.MULTILINE)
    
    matches = list(pattern.finditer(content))
    for i, match in enumerate(matches):
        role = match.group(1).lower()
        timestamp = match.group(2)
        start = match.end()
        end = matches[i+1].start() if i + 1 < len(matches) else len(content)
        
        msg_content = content[start:end].strip()
        msg: dict[str, Any] = {"role": role, "timestamp": timestamp}
        
        json_pattern = re.compile(r"^```json\n(.*?)\n```\n?", re.DOTALL)
        json_match = json_pattern.match(msg_content)
        if json_match:
            try:
                sys_data = json.loads(json_match.group(1))
                msg.update(sys_data)
            except Exception:
                pass
            msg_content = msg_content[json_match.end():].strip()
            
        if msg_content:
            msg["content"] = msg_content
        else:
            msg["content"] = ""
            
        messages.append(msg)
        
    return metadata, messages


@dataclass
class Session:
    """
    A conversation session.

    Stores messages in MD format for easy reading and persistence.
    """

    key: str  # channel:chat_id
    messages: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    last_consolidated: int = 0  # Number of messages already consolidated to files

    def add_message(self, role: str, content: str, **kwargs: Any) -> None:
        """Add a message to the session."""
        msg = {
            "role": role.lower(),
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        }
        self.messages.append(msg)
        self.updated_at = datetime.now()

    @staticmethod
    def _find_legal_start(messages: list[dict[str, Any]]) -> int:
        """Find first index where every tool result has a matching assistant tool_call."""
        declared: set[str] = set()
        start = 0
        for i, msg in enumerate(messages):
            role = str(msg.get("role", "")).lower()
            if role == "assistant":
                for tc in msg.get("tool_calls") or []:
                    if isinstance(tc, dict) and tc.get("id"):
                        declared.add(str(tc["id"]))
            elif role == "tool":
                tid = msg.get("tool_call_id")
                if tid and str(tid) not in declared:
                    start = i + 1
                    declared.clear()
                    for prev in messages[start:i + 1]:
                        if prev.get("role") == "assistant":
                            for tc in prev.get("tool_calls") or []:
                                if isinstance(tc, dict) and tc.get("id"):
                                    declared.add(str(tc["id"]))
        return start

    def get_history(self, max_messages: int = 500, max_turns: int = 10) -> list[dict[str, Any]]:
        """
        Return unconsolidated messages for LLM input, aligned to a legal tool-call boundary.
        Implements short-term memory sliding window by retaining the most recent max_turns.
        """
        unconsolidated = self.messages[self.last_consolidated:]
        sliced = unconsolidated[-max_messages:]
        
        # Apply strict turn-based truncation for short-term coherence
        turn_count = 0
        cut = 0
        for i in range(len(sliced) - 1, -1, -1):
            if sliced[i].get("role") == "user":
                turn_count += 1
                if turn_count > max_turns:
                    cut = i + 1
                    break
        
        sliced = sliced[cut:]

        # Drop leading non-user messages to avoid starting mid-turn when possible.
        for i, message in enumerate(sliced):
            if str(message.get("role", "")).lower() == "user":
                sliced = sliced[i:]
                break

        start = self._find_legal_start(sliced)
        if start:
            sliced = sliced[start:]

        out: list[dict[str, Any]] = []
        for message in sliced:
            entry: dict[str, Any] = {"role": message["role"], "content": message.get("content", "")}
            for key in ("tool_calls", "tool_call_id", "name"):
                if key in message:
                    entry[key] = message[key]
            out.append(entry)
        return out

    def clear(self) -> None:
        """Clear all messages and reset session to initial state."""
        self.messages = []
        self.last_consolidated = 0
        self.updated_at = datetime.now()


class SessionManager:
    """
    Manages conversation sessions.

    Sessions are stored as Markdown (.md) files in the sessions directory.
    """

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.sessions_dir = ensure_dir(self.workspace / "sessions")
        self.legacy_sessions_dir = get_legacy_sessions_dir()
        self._cache: dict[str, Session] = {}

    def _get_session_path(self, key: str) -> Path:
        """Get the file path for a session .md file."""
        safe_key = safe_filename(key.replace(":", "_"))
        return self.sessions_dir / f"{safe_key}.md"

    def _get_legacy_session_path(self, key: str) -> Path:
        """Legacy global session path (.jsonl)."""
        safe_key = safe_filename(key.replace(":", "_"))
        return self.legacy_sessions_dir / f"{safe_key}.jsonl"

    def get_or_create(self, key: str) -> Session:
        if key in self._cache:
            return self._cache[key]

        session = self._load(key)
        if session is None:
            session = Session(key=key)

        self._cache[key] = session
        return session

    def _load(self, key: str) -> Session | None:
        path = self._get_session_path(key)
        
        if not path.exists():
            # Check for existing legacy .jsonl in local directory to upgrade
            safe_key = safe_filename(key.replace(":", "_"))
            local_jsonl = self.sessions_dir / f"{safe_key}.jsonl"
            legacy_jsonl = self._get_legacy_session_path(key)
            
            target_jsonl = local_jsonl if local_jsonl.exists() else (legacy_jsonl if legacy_jsonl.exists() else None)
            
            if target_jsonl:
                try:
                    session = self._load_jsonl(target_jsonl, key)
                    if session:
                        # upgrade instantly to md
                        self.save(session)
                        if target_jsonl.exists():
                            target_jsonl.unlink() # remove old format
                        return session
                except Exception as e:
                    logger.warning(f"Failed to migrate .jsonl session {key}: {e}")

        if not path.exists():
            return None

        try:
            text = path.read_text(encoding="utf-8")
            meta, messages = parse_session_md(text)
            
            created_at = datetime.now()
            updated_at = datetime.now()
            last_consolidated = 0
            
            if "created_at" in meta:
                created_at = datetime.fromisoformat(meta["created_at"])
            if "updated_at" in meta:
                updated_at = datetime.fromisoformat(meta["updated_at"])
            if "last_consolidated" in meta:
                last_consolidated = int(meta["last_consolidated"])
                
            return Session(
                key=key,
                messages=messages,
                created_at=created_at,
                updated_at=updated_at,
                metadata={},
                last_consolidated=last_consolidated
            )
        except Exception as e:
            logger.warning(f"Failed to load .md session {key}: {e}")
            return None

    def _load_jsonl(self, path: Path, key: str) -> Session | None:
        """Fallback to load legacy JSONL."""
        messages = []
        metadata = {}
        created_at = None
        last_consolidated = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                if data.get("_type") == "metadata":
                    metadata = data.get("metadata", {})
                    created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
                    last_consolidated = data.get("last_consolidated", 0)
                else:
                    messages.append(data)
        
        created_now = datetime.now()
        return Session(
            key=key,
            messages=messages,
            created_at=created_at or created_now,
            updated_at=created_now,
            metadata=metadata,
            last_consolidated=last_consolidated
        )

    def save(self, session: Session) -> None:
        """Save a session to disk as a Markdown file."""
        path = self._get_session_path(session.key)

        parts = [
            "---",
            f"key: {session.key}",
            f"created_at: {session.created_at.isoformat()}",
            f"updated_at: {session.updated_at.isoformat()}",
            f"last_consolidated: {session.last_consolidated}",
            "---",
            ""
        ]
        
        for msg in session.messages:
            parts.append(serialize_message(msg))
            parts.append("\n")
            
        path.write_text("\n".join(parts), encoding="utf-8")
        self._cache[session.key] = session

    def invalidate(self, key: str) -> None:
        self._cache.pop(key, None)

    def list_sessions(self) -> list[dict[str, Any]]:
        sessions = []

        for path in self.sessions_dir.glob("*.md"):
            try:
                # Read frontmatter
                with open(path, encoding="utf-8") as f:
                    lines = []
                    for _ in range(10):
                        try:
                            lines.append(next(f).strip())
                        except StopIteration:
                            break
                    
                meta = {}
                if lines and lines[0] == "---":
                    for line in lines[1:]:
                        if line == "---":
                            break
                        if ":" in line:
                            k, v = line.split(":", 1)
                            meta[k.strip()] = v.strip()
                            
                key = meta.get("key") or path.stem.replace("_", ":", 1)
                sessions.append({
                    "key": key,
                    "created_at": meta.get("created_at"),
                    "updated_at": meta.get("updated_at"),
                    "path": str(path)
                })
            except Exception:
                continue

        return sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)
