from memory import memory_store

# 这个 JSON Schema 就是你要放进 TOOLS 数组里，发给 LLM 的说明书
REMEMBER_TOOL_SCHEMA = {
    "name": "save_core_memory",
    "description": "当你得知了关于用户的重要事实（如：偏好、公司规定、出差计划、报错经验等），必须调用此工具将其永久保存。",
    "input_schema": {
        "type": "object",
        "properties": {
            "fact": {
                "type": "string",
                "description": "要保存的精简事实。例如：'用户张三对海鲜过敏' 或 '2026年3月27日确认去大阪出差'。"
            }
        },
        "required": ["fact"]
    }
}

def execute_remember_tool(fact: str):
    # 真正调用我们刚刚写的 memory.py 里的追加方法
    return memory_store.remember(fact)

TOOL_HANDLERS = {
    "save_core_memory": lambda **kw: execute_remember_tool(kw.get("fact", "")),
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": REMEMBER_TOOL_SCHEMA["name"],
            "description": REMEMBER_TOOL_SCHEMA["description"],
            "parameters": REMEMBER_TOOL_SCHEMA["input_schema"],
        },
    }
]