class TodoManager:
    """
    待办事项管理器：用于维护和展示 AI 代理的任务列表。
    原理：通过一个中心化的列表存储任务状态，并在每次更新时进行严格的逻辑校验，
    最后将其序列化为易读的字符串反馈给模型。
    """

    def __init__(self):
        # 初始化存储待办事项的列表
        self.items = []

    def update(self, items: list) -> str:
        """
        更新待办事项列表并返回当前的渲染状态。
        """
        # 限制最大任务数量，防止上下文过载
        if len(items) > 20:
            raise ValueError("Max 20 todos allowed")

        validated = []
        in_progress_count = 0

        # 遍历并校验每一个传入的任务项
        for i, item in enumerate(items):
            # 提取并清洗任务描述文本
            text = str(item.get("text", "")).strip()
            # 提取状态并转换为小写，默认为 pending
            status = str(item.get("status", "pending")).lower()
            # 提取 ID，如果没有则根据索引自动生成
            item_id = str(item.get("id", str(i + 1)))

            # 校验：任务文本不能为空
            if not text:
                raise ValueError(f"Item {item_id}: text required")

            # 校验：状态必须是预定义的三个值之一
            if status not in ("pending", "in_progress", "completed"):
                raise ValueError(f"Item {item_id}: invalid status '{status}'")

            # 统计处于 "进行中" 状态的任务数量
            if status == "in_progress":
                in_progress_count += 1

            # 将校验通过的任务存入列表
            validated.append({"id": item_id, "text": text, "status": status})

        # 核心约束：同时只能有一个任务在进行中，确保模型专注
        if in_progress_count > 1:
            raise ValueError("Only one task can be in_progress at a time")

        # 更新内部状态
        self.items = validated
        # 返回渲染后的字符串，以便反馈给模型
        return self.render()

    def render(self) -> str:
        """
        将待办事项列表渲染成易读的文本格式。
        """
        if not self.items:
            return "No todos."

        lines = []
        for item in self.items:
            # 根据状态选择对应的标记符号
            # [ ] 表示未开始，[>] 表示进行中，[x] 表示已完成
            marker = {"pending": "[ ]", "in_progress": "[>]", "completed": "[x]"}[
                item["status"]
            ]
            # 拼接成类似 "[>] #1: 任务内容" 的格式
            lines.append(f"{marker} #{item['id']}: {item['text']}")

        # 计算完成进度
        done = sum(1 for t in self.items if t["status"] == "completed")
        lines.append(f"\n({done}/{len(self.items)} completed)")

        # 将所有行合并成一个多行字符串
        return "\n".join(lines)


TODO = TodoManager()

TOOL_HANDLERS = {
    "todo": lambda **kw: TODO.update(kw["items"]),
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "todo",
            "description": "Update task list. Track progress on multi-step tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "text": {"type": "string"},
                                "status": {
                                    "type": "string",
                                    "enum": ["pending", "in_progress", "completed"],
                                },
                            },
                            "required": ["id", "text", "status"],
                        },
                    }
                },
                "required": ["items"],
            },
        },
    },
]
