import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# General Configurations
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
DATA_FILE = Path(__file__).parent.parent / "scripts" / "data" / "diet_knowledge.json"
COLLECTION_NAME = "DietKnowledge"
TOP_K_RESULTS = 5
SKIP_DATA_LOADER = bool(int(os.getenv("SKIP_DATA_LOADER", "0")))

# EMBEDDINGS CONFIGS
EMBEDDING_SOURCE = "local"
# AZURE
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "YOUR_AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "YOUR_EMBEDDING_DEPLOYMENT_NAME")
# Local
LOCAL_EMBEDDING_MODEL_NAME = "google/embeddinggemma-300m"
LOCAL_ALTERNATIVE_EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
# Serverless
HF_API_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "")


# LLM (CHAT) CONFIGS
LLM_SOURCE = "local"
# AZURE
AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "YOUR_CHAT_DEPLOYMENT_NAME")
# Local
LOCAL_LLM_MODEL_NAME = "google/gemma-3-1b-it"
# Serverless
HF_API_CHAT_MODEL = "Qwen/Qwen2.5-72B-Instruct"
HF_API_ENDPOINT_BASE = "https://router.huggingface.co"
