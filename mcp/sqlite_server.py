from mcp.server.fastmcp import FastMCP
import sqlite3
import os

# Create server instance
mcp = FastMCP("sqlite-server")
DB_PATH = "/Users/xuncen/Allcode/mcp-test/todos.db"

# 确保数据库所在的目录存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


@mcp.tool()
def query(sql: str) -> str:
    """Execute a SQL query (SELECT only) and return results.

    Args:
        sql: The SELECT query to execute
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            return str(rows)
    except Exception as e:
        return f"Query Error: {str(e)}"


@mcp.tool()
def execute(sql: str) -> str:
    """Execute a SQL statement (CREATE, INSERT, UPDATE, DELETE).

    Args:
        sql: The SQL statement to execute
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            return f"Statement executed successfully. Rows affected: {cursor.rowcount}"
    except Exception as e:
        return f"Execute Error: {str(e)}"


@mcp.tool()
def list_tables() -> str:
    """List all tables in the database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            return f"Tables: {', '.join([t[0] for t in tables])}"
    except Exception as e:
        return f"Error listing tables: {str(e)}"


if __name__ == "__main__":
    mcp.run()
