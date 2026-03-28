import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# 添加根目录到 sys.path 以便导入 llm_client
sys.path.append(str(Path(__file__).parent.parent))
from llm_client import get_langchain_llm

try:
    from browser_use import Agent, Browser, BrowserConfig
except ImportError:
    Agent = None
    Browser = None
    BrowserConfig = None


async def _run_browser_task(instruction: str):
    """
    内部异步执行函数，运行 browser-use Agent。
    """
    if Agent is None:
        return "Error: browser-use is not installed. Please run 'pip install browser-use'."

    # 配置浏览器，可以根据需要设置 headless=True/False
    browser = Browser(config=BrowserConfig(headless=False)) # 默认可视化，方便调试
    
    try:
        llm = get_langchain_llm()
        agent = Agent(
            task=instruction,
            llm=llm,
            browser=browser,
        )
        # 设置最大步数防止死循环
        result = await agent.run(max_steps=20)
        
        # 显式关闭浏览器
        await browser.close()
        
        return f"Browser RPA Task Completed.\nResult: {str(result)}"
    except Exception as e:
        # 确保出错也关闭浏览器
        if browser:
            await browser.close()
        return f"Error during Browser RPA: {str(e)}"



def execute_browser_rpa(instruction: str) -> str:
    """
    通用浏览器自动化工具。
    """
    try:
        # browser-use 只能在异步环境中运行
        return asyncio.run(_run_browser_task(instruction))
    except Exception as e:
        return f"Async Runtime Error: {str(e)}"


def submit_expense_claim(amount: float, reason: str) -> str:
    """
    特定报销提交工具。
    """
    task = f"""
    1. 访问 FinanceFlow 登录页 (http://localhost:5176/ 或者你已知的 FinanceFlow 登录地址)
    2. 使用默认测试账号 zhouenci 和密码 sagou 登录 (如果未登录)
    3. 登录后，找到提交报销的表单。
    4. 埴入金额: {amount}，原因: '{reason}'。
    5. 点击提交按钮。
    6. 确认提交成功，并返回成功提示。
    """
    return execute_browser_rpa(task)


# --- 工具定义 ---

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_rpa_worker",
            "description": "一个强大的浏览器自动化助手。当你需要登录网页、点击按钮、或者抓取非结构化网页数据时，把自然语言指令发给它。它会打开真实的浏览器进行操作。",
            "parameters": {
                "type": "object",
                "properties": {
                    "instruction": {
                        "type": "string",
                        "description": "详细的网页操作指令。例如：'打开 google.co.jp，搜索日本东京今天的天气，提取最高温度并返回。'",
                    }
                },
                "required": ["instruction"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_expense_claim",
            "description": "在 FinanceFlow 系统中自动提交一笔报销申请。包含登录和表单填充。",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "报销金额。"},
                    "reason": {"type": "string", "description": "报销原因/备注。"},
                },
                "required": ["amount", "reason"],
            },
        },
    },
]

TOOL_HANDLERS = {
    "web_rpa_worker": lambda **kw: execute_browser_rpa(kw.get("instruction")),
    "submit_expense_claim": lambda **kw: submit_expense_claim(
        kw.get("amount"), kw.get("reason")
    ),
}

