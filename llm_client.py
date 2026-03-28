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

from retry import sync_retry, RetryConfig

# 定义重试策略：最多三次重试，处理不稳定 API 请求
llm_retry_config = RetryConfig(
    max_retries=3,
    initial_delay=1.0,
    max_delay=10.0,
    exponential_base=2.0
)


@sync_retry(config=llm_retry_config)
def get_completion(messages, tools=None, system=None, **kwargs):
    """
    使用 litellm 进行对话补全。
    支持多种模型切换，只需更改环境变量 MODEL_ID。
    (包含内置自动重试机制以容忍网络波动与并发断连)
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

    # System message handling: Extract if present, then clean the rest
    system_msg = None
    other_messages = []
    for m in params["messages"]:
        if str(m.get("role", "")).lower() == "system":
            system_msg = m
        else:
            other_messages.append(m)

    # 1. Clean 'other_messages' to ENSURE they start with a 'user' message
    while other_messages:
        if str(other_messages[0].get("role", "")).lower() == "user":
            break
        other_messages.pop(0)

    # 2. If no user message is left, add a placeholder to satisfy strict templates
    if not other_messages:
        other_messages = [{"role": "user", "content": "Assistant, please continue with the next step."}]

    # 3. Re-assemble with system message at the top
    final_messages = []
    if system_msg:
        final_messages.append(system_msg)
    final_messages.extend(other_messages)
    params["messages"] = final_messages

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


def get_langchain_llm():
    """
    返回一个兼容 browser-use 的 LLM 实例。
    注意：最新版本的 browser-use (0.12+) 使用了自己的 BaseChatModel Protocol，
    不再直接依赖 LangChain 的实现。
    """
    try:
        # 如果是 OpenAI 兼容接口，使用 browser_use 自带的 ChatOpenAI 包装器
        if "openai" in effective_model.lower() or not effective_model:
            from browser_use.llm.openai.chat import ChatOpenAI
            return ChatOpenAI(
                model=MODEL_ID,
                base_url=litellm.api_base if hasattr(litellm, "api_base") else None,
                api_key=os.getenv("OPENAI_API_KEY", "lm-studio"),
                timeout=300,  # 增加超时时间以适配本地慢模型
                dont_force_structured_output=True,  # 对于本地模型，不强制要求结构化输出，提高稳定性
                add_schema_to_system_prompt=True    # 将 schema 加入 system prompt 辅助模型理解
            )
        
        # 对于其他模型，尝试使用 browser_use 的 LiteLLM 包装器 (如果有)
        try:
            from browser_use.llm.litellm.chat import ChatLiteLLM
            return ChatLiteLLM(
                model=effective_model,
                api_base=litellm.api_base if hasattr(litellm, "api_base") else None
            )
        except ImportError:
            # 兜底：使用原来的 langchain_community 实现
            from langchain_community.chat_models import ChatLiteLLM
            return ChatLiteLLM(
                model=effective_model,
                api_base=litellm.api_base if hasattr(litellm, "api_base") else None,
                max_tokens=8000
            )
    except Exception as e:
        print(f"Error creating LLM: {e}")
        raise


if __name__ == "__main__":
    # 简单的测试逻辑
    test_messages = [{"role": "user", "content": "你好，请自我介绍一下。"}]
    try:
        res = get_completion(test_messages)
        print(res.choices[0].message.content)
    except Exception as e:
        print(f"Test failed: {e}")
