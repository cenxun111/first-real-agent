import os
import json
import requests
from typing import Any, Dict, List

def serper_search(query: str) -> str:
    """
    使用 Serper API 进行谷歌搜索。
    """
    api_key = os.getenv("Serper_API_KEY")
    if not api_key:
        return "Error: Serper_API_KEY not found in environment variables."

    url = "https://google.serper.dev/search"
    payload = json.dumps({"q": query})
    headers = {
        'X-API-KEY': api_key.strip(),
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        results = response.json()
        
        output = []
        if "organic" in results:
            for item in results["organic"][:5]: # 取前5条结果
                output.append(f"Title: {item.get('title')}\nLink: {item.get('link')}\nSnippet: {item.get('snippet')}\n")
        
        return "\n".join(output) if output else "No results found."
    except Exception as e:
        return f"Error during Serper search: {str(e)}"

def jina_read(url: str) -> str:
    """
    使用 Jina Reader 将网页内容转换为 Markdown。
    """
    jina_url = f"https://r.jina.ai/{url}"
    try:
        response = requests.get(jina_url)
        response.raise_for_status()
        # 截断太长的内容，防止上下文溢出
        return response.text[:10000] 
    except Exception as e:
        return f"Error during Jina read: {str(e)}"

TOOL_HANDLERS = {
    "serper_search": lambda **kw: serper_search(kw["query"]),
    "jina_read": lambda **kw: jina_read(kw["url"]),
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "serper_search",
            "description": "Search the web using Serper (Google Search).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "jina_read",
            "description": "Read a webpage and convert it to markdown using Jina Reader.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The URL of the webpage to read."}
                },
                "required": ["url"],
            },
        },
    },
]
