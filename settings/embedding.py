import logging

from huggingface_hub import InferenceClient, login
from langchain_openai import AzureOpenAIEmbeddings
from sentence_transformers import SentenceTransformer

from settings import configs

logger = logging.getLogger("diet_rag_app")


class LocalHuggingFaceEmbeddings:
    """
    This class adapts a local SentenceTransformer model
    to the LangChain interface, which expects the methods embed_documents and embed_query.
    """

    def __init__(self, model_name: str, alternative_model_name: str):
        logger.info(f"📥 Loading local model: {model_name}...")
        try:
            self.model = SentenceTransformer(model_name)
            logger.info("✅ Local model loaded successfully.")
        except Exception as e:
            logger.error(f"❌ Error loading {model_name}. Falling back to {alternative_model_name}.")
            logger.error(f"Error details: {e}")
            self.model = SentenceTransformer(alternative_model_name)

    def embed_documents(self, texts):
        # Returns a list of lists
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, text):
        # Returns a single list
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()


class HFServerlessEmbeddings:
    """Обертка над InferenceClient для совместимости с LangChain"""

    def __init__(self, model_name, api_key):
        self.client = InferenceClient(token=api_key)
        self.model_name = model_name

    def embed_documents(self, texts):
        # Используем feature_extraction, который у вас работает
        result = self.client.feature_extraction(texts, model=self.model_name)
        return result.tolist()  # Превращаем numpy array в список

    def embed_query(self, text):
        # Для одного запроса
        result = self.client.feature_extraction([text], model=self.model_name)
        return result.tolist()[0]


def init_embedding() -> AzureOpenAIEmbeddings | LocalHuggingFaceEmbeddings | HFServerlessEmbeddings:
    logger.info("Initializing Embedding model")
    if configs.EMBEDDING_SOURCE == "local":
        logger.info("Logging to HUGGINGFACE...")
        login(token=configs.HUGGINGFACE_API_TOKEN)
        return LocalHuggingFaceEmbeddings(
            model_name=configs.LOCAL_EMBEDDING_MODEL_NAME,
            alternative_model_name=configs.LOCAL_ALTERNATIVE_EMBEDDING_MODEL_NAME,
        )

    elif configs.EMBEDDING_SOURCE == "hf_api":
        logger.info(f"🌐 Connecting to HF Serverless Embeddings: {configs.HF_API_EMBED_MODEL}")
        return HFServerlessEmbeddings(model_name=configs.HF_API_EMBED_MODEL, api_key=configs.HUGGINGFACE_API_TOKEN)

    return AzureOpenAIEmbeddings(
        azure_deployment=configs.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        api_version=configs.AZURE_OPENAI_API_VERSION,
        dimensions=255,
    )
