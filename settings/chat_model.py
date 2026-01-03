import logging

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

from settings import configs

logger = logging.getLogger(__name__)


def init_chat_model():
    logger.info(f"Initializing chat model with provider: {configs.LLM_PROVIDER}")

    if configs.LLM_PROVIDER == "groq":
        if not configs.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required for Groq provider")

        logger.info(f"Using Groq with model: {configs.GROQ_MODEL}")
        return ChatGroq(
            api_key=configs.GROQ_API_KEY,
            model=configs.GROQ_MODEL,
            temperature=0.1,
            max_tokens=2048,
        )

    elif configs.LLM_PROVIDER == "xai":
        if not configs.XAI_API_KEY:
            raise ValueError("XAI_API_KEY is required for xAI provider")

        logger.info(f"Using xAI Grok with model: {configs.XAI_MODEL}")
        return ChatOpenAI(
            api_key=configs.XAI_API_KEY,
            base_url="https://api.x.ai/v1",
            model=configs.XAI_MODEL,
            temperature=0.1,
            max_tokens=2048,
        )

    elif configs.LLM_PROVIDER == "openrouter":
        if not configs.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required for OpenRouter provider")

        logger.info(f"Using OpenRouter with model: {configs.OPENROUTER_MODEL}")
        return ChatOpenAI(
            api_key=configs.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            model=configs.OPENROUTER_MODEL,
            temperature=0.1,
            max_tokens=2048,
        )

    else:
        raise ValueError(f"Unknown LLM provider: {configs.LLM_PROVIDER}")
