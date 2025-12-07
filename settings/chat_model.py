import logging

from langchain_openai import AzureChatOpenAI

logger = logging.getLogger("diet_rag_app")


def init_ai_model(azure_deployment: str, api_version: str, temperature: float = 0) -> AzureChatOpenAI:
    logger.info("Initializing OpenAI client")
    return AzureChatOpenAI(azure_deployment=azure_deployment, api_version=api_version, temperature=temperature)
