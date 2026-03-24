import os
import litellm
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(override=True)

# 默认模型 ID，优先从环境变量读取
MODEL_ID = os.getenv("MODEL_ID", "claude-3-5-sonnet-20240620")

# 配置 litellm 的基础 URL
# 兼容 .env 中的 OPENAI_BASE_URL 或 LLM_API_BASE
base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("LLM_API_BASE")
if base_url:
    litellm.api_base = base_url

# 如果使用的是 OpenAI 兼容的本地模型（如 LM Studio），且没有前缀，
# 建议在模型名前添加 openai/ 前缀，以便 litellm 正确路由
if base_url and not ("/" in MODEL_ID):
    # 如果没有提供前缀且有自定义 base_url，通常意味着它是 OpenAI 兼容接口
    effective_model = f"openai/{MODEL_ID}"
else:
    effective_model = MODEL_ID


def get_completion(messages, tools=None, system=None, **kwargs):
    """
    使用 litellm 进行对话补全。
    支持多种模型切换，只需更改环境变量 MODEL_ID。
    """
    # 准备调用参数
    params = {
        "model": effective_model,
        "messages": list(messages),  # 浅拷贝，防止修改原列表
        "max_tokens": kwargs.get("max_tokens", 8000),
    }

    # 如果提供了系统提示词，将其添加到消息列表中
    if system:
        # 检查是否已经有系统消息
        if not any(m.get("role") == "system" for m in params["messages"]):
            params["messages"] = [{"role": "system", "content": system}] + params[
                "messages"
            ]

    # 如果提供了工具定义
    if tools:
        params["tools"] = tools

    # 调用 litellm
    try:
        response = litellm.completion(**params)
        return response
    except Exception as e:
        print(f"LLM Call Error: {e}")
        raise


if __name__ == "__main__":
    # 简单的测试逻辑
    test_messages = [{"role": "user", "content": "你好，请自我介绍一下。"}]
    try:
        res = get_completion(test_messages)
        print(res.choices[0].message.content)
    except Exception as e:
        print(f"Test failed: {e}")
