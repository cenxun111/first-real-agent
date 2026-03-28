# tools/write_code_tool.py
import os

# from tools.base import BaseTool


class WriteCodeTool:
    name = "write_code"
    description = "将生成的代码写入或覆盖指定文件。必须提供完整的文件路径和内容。"

    # V3.0 核心：修改代码必须经过人类审批
    requires_approval = True

    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "文件的相对路径，例如 'src/api.py'",
            },
            "content": {"type": "string", "description": "要写入的完整代码内容"},
        },
        "required": ["path", "content"],
    }

    def execute(self, path: str, content: str):
        # 【安全护栏】限制 AI 只能操作当前项目文件夹
        # 防止路径穿越攻击 (Path Traversal)
        base_dir = os.getcwd()
        safe_path = os.path.abspath(os.path.join(base_dir, path))

        if not safe_path.startswith(base_dir):
            return "错误：禁止访问项目目录以外的路径！"

        try:
            # 确保父目录存在
            os.makedirs(os.path.dirname(safe_path), exist_ok=True)

            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(content)

            return f"成功：代码已成功写入到 {path}。"
        except Exception as e:
            return f"写入失败：{str(e)}"


write_code_tool = WriteCodeTool()
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": write_code_tool.name,
            "description": write_code_tool.description,
            "parameters": write_code_tool.parameters,
        },
    }
]

TOOL_HANDLERS = {write_code_tool.name: write_code_tool.execute}
