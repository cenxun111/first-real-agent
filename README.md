# 🤖 First Real Agent - AI Agent Framework

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-blue.svg)]()

**一个强大的单兵 AI Agent 框架，具备物理引擎、专注力、长时记忆和跨会话智慧**

</div>

---

## 📖 项目简介

First Real Agent 是一个极简而强大的 AI Agent 实现，采用"单兵极致形态"设计理念：

- **强劲的物理引擎**：基于 `while True` 循环的字典路由分发系统，可精准调用任何 Python 函数
- **绝对的专注力**：一维待办列表（TodoManager）确保 Agent 每次只做一件事
- **无限的体力与长时记忆**：智能上下文压缩机制，支持连续处理上万行代码或几百页文档
- **跨越时间的智慧**：持久化 Session Notes，实现跨会话的长期记忆

---

## ✨ 核心特性

### 🧠 三层架构设计

```
┌─────────────────────────────────────┐
│         Context Manager              │  ← 智能上下文管理
│         (压缩 + 记忆注入)             │
└─────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────┐
│          Agent Loop                  │  ← 主循环引擎
│    (思考 → 工具调用 → 结果处理)       │
└─────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────┐
│         Tool Router                  │  ← 物理引擎
│   (BASE + SKILL + TODO + WEB...)     │
└─────────────────────────────────────┘
```

### 🛠️ 工具生态系统

| 工具类型 | 模块 | 功能描述 |
|---------|------|---------|
| **Base Tools** | `tools/base.py` | 基础文件操作、代码执行、数据库访问 |
| **Skill Tools** | `skills/` | 可扩展技能模块（PDF、Web Dev、MCP Builder 等） |
| **Todo Manager** | `tools/todo_tool.py` | 待办事项追踪，防止多任务发散 |
| **Web Tools** | `tools/web_tool.py` | 网络搜索 (`serper_search`)、网页读取 (`jina_read`) |
| **Code Tools** | `tools/code_tool.py` | 代码搜索、关键词查找 |
| **MCP Tools** | `tools/mcp_tool.py` | MCP 服务器加载与集成 |
| **Memory Tools** | `memory/` | 长期记忆存储与管理 |

### 🌐 Web API & Frontend

完整的 Web 界面，采用 Glassmorphism 设计风格：

- **FastAPI Backend**: `/api/chat` REST 端点
- **实时 UX**: 加载动画、Markdown 渲染、会话上下文保持
- **启动命令**: `uvicorn api:app --reload --host 0.0.0.0 --port 8000`

---

## 🚀 快速开始

### 1️⃣ 环境准备

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r mcp/requirements.txt
pip install python-dotenv rich litellm

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 API Key
```

### 2️⃣ 启动 Agent

**终端模式**:
```bash
python agent.py
```

**Web 模式**:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
# 访问 http://localhost:8000/
```

### 3️⃣ 使用示例

```python
# 基础对话
agent = Agent()
response = agent.chat("帮我写一个 Python 函数计算斐波那契数列")

# 多轮会话
session_id = "my_session"
response1 = agent.chat("介绍一下庐山", session_id=session_id)
response2 = agent.chat("把刚才的介绍保存成 markdown", session_id=session_id)
```

---

## 📁 项目结构

```
first-real-agent/
├── agent.py              # Agent 主循环（核心引擎）
├── api.py                # FastAPI Web 后端
├── context.py            # 上下文管理器（压缩 + 记忆注入）
├── llm_client.py        # LLM 客户端封装
├── memory.py             # 长期记忆存储
├── session/              # 会话管理模块
│   ├── manager.py       # SessionManager
│   └── __init__.py
├── skills/               # 技能扩展目录
│   ├── agent-builder/   # Agent 构建专家
│   ├── code-review/     # 代码审查专家
│   ├── mcp-builder/     # MCP 服务器构建
│   ├── pdf/             # PDF 处理专家
│   ├── skill-creator/   # 技能创建向导
│   └── web-dev/         # Web 开发专家
├── tools/                # 工具集
│   ├── base.py          # 基础工具
│   ├── code_tool.py     # 代码操作工具
│   ├── mcp_tool.py      # MCP 服务器加载
│   ├── skillLoader.py   # 技能动态加载
│   ├── todo_tool.py     # 待办事项管理
│   └── web_tool.py      # Web 搜索与读取
├── static/               # Web 前端资源
│   ├── index.html       # Glassmorphism UI
│   ├── script.js        # 交互逻辑
│   └── styles.css       # 样式定义
├── mcp/                  # MCP 服务器目录
│   ├── file_server.py   # 文件探索器
│   ├── sqlite_server.py # SQLite 数据库
│   └── requirements.txt
├── .env                  # 环境变量配置
├── plan.md               # 项目蓝图文档
└── lusan.md              # 示例输出（庐山介绍）
```

---

## 🔧 核心模块说明

### Agent Loop (agent.py)

主循环包含三层压缩机制：

1. **micro_compact**: 清理冗余工具输出
2. **auto_compact**: 阶段性总结重置上下文
3. **todo_reminder**: 每 3 轮未更新待办则注入提醒

```python
# 伪代码示例
while True:
    # 构建 Prompt（含记忆）
    system_prompt, messages = context_manager.build_prompt(session)
    
    # LLM 推理
    response = get_completion(messages=messages, tools=TOOLS)
    
    # 工具调用与结果处理
    for tool_call in response.tool_calls:
        output = TOOL_HANDLERS[tool_call.name](**args)
    
    # 压缩上下文（可选）
    if len(session.messages) > MAX_TOKENS:
        context_manager.compress()
```

### Context Manager (context.py)

智能上下文管理：

- **记忆注入**: 将长期记忆融入系统提示词
- **内容压缩**: 移除重复的工具输出、保留关键信息
- **会话状态**: 维护完整的对话历史

### Memory Store (memory.py)

持久化记忆系统：

```python
# 写入短期记忆（会话内）
session.add_message("user", "帮我分析这个代码")

# 写入长期记忆（跨会话）
save_memory(
    history_entry="用户请求分析代码架构...",
    memory_update="# 项目记忆\n- 用户偏好：Python 编程"
)

# 读取记忆
memory = memory_store.read_long_term()
```

---

## 🎯 使用场景

### ✅ 适合的任务类型

- **代码生成与分析**: 编写、审查、优化 Python 代码
- **文档处理**: PDF 解析、Markdown 写作、内容整理
- **Web 开发**: HTML/CSS/JS 代码生成、网站搭建
- **数据查询**: SQLite 数据库操作、SQL 语句生成
- **文件管理**: 创建、编辑、搜索项目文件
- **知识问答**: 联网搜索、信息整合

### ❌ 不适合的场景

- 需要实时硬件交互的任务（如 IoT 控制）
- 对延迟极度敏感的高频交易场景
- 需要图形界面交互的应用

---

## 📚 扩展技能

通过 `skills/` 目录动态加载新技能：

```python
# 在 tools/skillLoader.py 中注册新技能
from skills.my_new_skill import TOOL_HANDLERS, TOOLS, SYSTEM

TOOL_HANDLERS.update(TOOL_HANDLERS)
TOOLS.extend(TOOLS)
```

**示例**: 创建一个 PDF 分析技能

```python
# skills/pdf_analyzer.py
def analyze_pdf(path: str) -> str:
    """分析 PDF 文件内容"""
    # 实现逻辑...
    return "PDF 分析报告..."

TOOL_HANDLERS = {
    "analyze_pdf": lambda **kw: analyze_pdf(kw.get("path")),
}

TOOLS = [{
    "type": "function",
    "function": {
        "name": "analyze_pdf",
        "description": "分析 PDF 文件内容并生成报告",
        "parameters": {...},
    },
}]
```

---

## 🔒 安全建议

1. **API Key 管理**: 将敏感信息存入 `.env`，不要提交到 Git
2. **代码执行沙箱**: 生产环境建议使用 Docker 容器隔离
3. **输入验证**: 对用户输入进行过滤和 sanitization
4. **速率限制**: API 调用添加限流机制

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 License

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- **FastAPI**: 优秀的 Web 框架
- **Rich**: 漂亮的终端输出库
- **LiteLLM**: 统一的 LLM 接口封装
- **所有开源社区贡献者**

---

<div align="center">

**Made with ❤️ by AI Agent Team**

</div>
