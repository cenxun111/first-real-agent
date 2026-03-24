import os
import subprocess
from pathlib import Path

# 定义工作目录
WORKDIR = Path.cwd()


def safe_path(p: str) -> Path:
    """确保路径安全，不会逃逸出工作目录。"""
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path


def list_files(path: str = ".", depth: int = 2) -> str:
    """
    列出目录下的所有文件和文件夹。
    """
    try:
        root = safe_path(path)
        output = []
        prefix = "  "

        for p in sorted(root.rglob("*")):
            # 计算相对深度
            rel_depth = len(p.relative_to(root).parts)
            if rel_depth > depth:
                continue

            indent = prefix * (rel_depth - 1)
            if p.is_dir():
                output.append(f"{indent}📁 {p.name}/")
            else:
                output.append(f"{indent}📄 {p.name}")

        return "\n".join(output) if output else "No files found."
    except Exception as e:
        return f"Error listing files: {str(e)}"


def search_code(query: str, path: str = ".") -> str:
    """
    在代码中搜索指定的关键词（类似 grep）。
    """
    try:
        root = safe_path(path)
        # 使用 grep 命令进行搜索，排除掉一些常见的干扰目录
        cmd = [
            "grep",
            "-rn",
            "--exclude-dir={.git,.tasks,.transcripts,node_modules,__pycache__}",
            query,
            str(root),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if r.returncode == 0:
            # 限制输出行数，防止过长
            lines = r.stdout.splitlines()
            if len(lines) > 100:
                lines = lines[:100] + [
                    f"... (Found {len(lines)} results, showing first 100)"
                ]
            return "\n".join(lines)
        elif r.returncode == 1:
            return "No matches found."
        else:
            return f"Error: {r.stderr}"
    except Exception as e:
        return f"Error searching code: {str(e)}"


TOOL_HANDLERS = {
    "list_files": lambda **kw: list_files(kw.get("path", "."), kw.get("depth", 2)),
    "search_code": lambda **kw: search_code(kw["query"], kw.get("path", ".")),
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List the project structure recursively up to a certain depth.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to list. Defaults to '.'.",
                    },
                    "depth": {
                        "type": "integer",
                        "description": "How deep to go. Defaults to 2.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search for a keyword in all files in the codebase.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search term."},
                    "path": {
                        "type": "string",
                        "description": "Optional: restrict search to a specific path.",
                    },
                },
                "required": ["query"],
            },
        },
    },
]
