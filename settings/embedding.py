import logging

from langchain_openai import AzureOpenAIEmbeddings

logger = logging.getLogger("diet_rag_app")


def init_embedding(azure_deployment: str, api_version: str, dimensions: int = 255) -> AzureOpenAIEmbeddings:
    logger.info("Initializing Embedding model")
    return AzureOpenAIEmbeddings(azure_deployment=azure_deployment, api_version=api_version, dimensions=dimensions)
