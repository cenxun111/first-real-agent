#!/usr/bin/env python3
"""my_server.py - A simple MCP server demonstrating tools, resources, and prompts."""

from mcp.server.fastmcp import FastMCP
import json

# Create server instance
mcp = FastMCP("file-explorer")

# Define a tool for file operations
@mcp.tool()
def read_file(path: str) -> str:
    """Read the contents of a file.

    Args:
        path: The absolute or relative path to the file
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found at path '{path}'"
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def list_directory(path: str) -> str:
    """List the contents of a directory.

    Args:
        path: The absolute or relative path to the directory
    """
    import os
    try:
        items = []
        for item in os.listdir(path):
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                items.append(f"[DIR] {item}")
            else:
                items.append(f"[FILE] {item}")
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@mcp.tool()
def get_file_info(path: str) -> str:
    """Get information about a file or directory.

    Args:
        path: The absolute or relative path to the file/directory
    """
    import os
    try:
        stat = os.stat(path)
        info = {
            "path": path,
            "type": "directory" if os.path.isdir(path) else "file",
            "size_bytes": stat.st_size,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "permissions": oct(stat.st_mode)[-3:]
        }
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"Error getting file info: {str(e)}"

if __name__ == "__main__":
    mcp.run()

