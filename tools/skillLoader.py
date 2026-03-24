import re
from pathlib import Path

WORKDIR = Path.cwd()
SKILLS_DIR = WORKDIR / "skills"


class SkillLoader:
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills = {}
        self._load_all()

    def _load_all(self):
        if not self.skills_dir.exists():
            return
        for f in sorted(self.skills_dir.rglob("SKILL.md")):
            text = f.read_text()
            meta, body = self._parse_frontmatter(text)
            name = meta.get("name", f.parent.name)
            self.skills[name] = {"meta": meta, "body": body, "path": str(f)}

    def _parse_frontmatter(self, text: str) -> tuple:
        """Parse frontmatter from SKILL.md files. Expected format:"""
        match = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
        if not match:
            return {}, text
        meta = {}
        for line in match.group(1).strip().splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                meta[key.strip()] = val.strip()
        return meta, match.group(2).strip()

    def get_descriptions(self) -> str:
        """Layer 1: short descriptions for system prompt."""
        if not self.skills:
            return "(no skills available)"
        lines = []
        for name, skill in self.skills.items():
            desc = skill["meta"].get("description", "No description")
            tags = skill["meta"].get("tags", "")
            line = f" - {name}: {desc}"
            if tags:
                line += f" [{tags}]"
            lines.append(line)
        return "\n".join(lines)

    def get_content(self, name: str) -> str:
        """Layer 2: full content for tool calls."""
        skill = self.skills.get(name)
        if not skill:
            return f"Error: Unknown skill '{name}'. Available: {', '.join(self.skills.keys())}"
        return f"<skill name=\"{name}\">\n{skill['body']}\n</skill>"


SKILL_LOADER = SkillLoader(SKILLS_DIR)

# Layer 1: skill metadata injected into system prompt
SYSTEM = f"""You are a powerful coding agent working in {WORKDIR}.

Core Capabilities:
1. File Management: Read, write, and edit files using `read_file`, `write_file`, and `edit_file`.
2. Code Intelligence: Use `list_files` to explore project structure and `search_code` to find specific code snippets or symbols.
3. Execution: Run shell commands using `bash` to install dependencies, run scripts, or perform system tasks.
4. Task Tracking: Always use `todo` to plan and track multi-step tasks.
5. Memory: Use `save_memory` to persist important context and summaries to long-term memory.
6. Web Search & Reading: Use `serper_search` to find information on the internet and `jina_read` to read specific webpage content.
7. MCP Integration: Access standardized external tools and resources through MCP servers (like the file-explorer server providing `list_directory`, `get_file_info`, etc.).
8. Specialized Skills: Use `load_skill` to access expert knowledge before tackling unfamiliar topics (like PDF processing, Web development, MCP building, etc.).

Important Rules:
- When a user asks you to perform a task (like searching the web), use the appropriate tool (e.g., `serper_search`) to DO IT immediately.
- Use `list_files` and `search_code` to understand the codebase before making changes.
- After loading a skill with `load_skill`, you should use the knowledge provided to guide your tool calls.
- Do not just explain how to do it; use your tools to actually perform the work.
- Use MCP tools whenever they provide specialized functionality that core tools don't.
- Use `jina_read` to get the full context of a page after finding it with `serper_search`.

Skills currently available:
{SKILL_LOADER.get_descriptions()}"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "load_skill",
            "description": "Load specialized knowledge by name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Skill name to load"}
                },
                "required": ["name"],
            },
        },
    },
]

TOOL_HANDLERS = {
    "load_skill": lambda **kw: SKILL_LOADER.get_content(kw["name"]),
}
