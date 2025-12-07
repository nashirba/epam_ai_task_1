import logging
import time

import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.collections.classes.config import VectorDistances

logger = logging.getLogger(__name__)


def init_weaviate_client(url: str, max_retries: int = 3, delay: int = 2) -> weaviate.WeaviateClient:
    """Initialize Weaviate client with connection retry."""
    logger.info(f"Connecting to Weaviate at {url}")

    for attempt in range(max_retries):
        try:
            client = weaviate.connect_to_custom(
                http_host=url.replace("http://", "").split(":")[0],
                http_port=int(url.split(":")[-1]),
                http_secure=False,
                grpc_host=url.replace("http://", "").split(":")[0],
                grpc_port=50051,
                grpc_secure=False,
            )
            if client.is_ready():
                logger.info("Successfully connected to Weaviate")
                return client
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries}: Weaviate not ready - {e}")
            time.sleep(delay)

    raise ConnectionError(f"Could not connect to Weaviate after {max_retries} attempts")


def create_schema(client: weaviate.WeaviateClient, collection_name: str) -> weaviate.collections.Collection:
    """Create the Weaviate collection schema."""
    logger.info(f"Creating collection schema: {collection_name}")

    if client.collections.exists(collection_name):
        logger.info(f"Collection {collection_name} already exists, deleting data...")
        client.collections.delete(collection_name)

    rag_collection = client.collections.create(
        name=collection_name,
        properties=[
            Property(name="doc_id", data_type=DataType.TEXT),
            Property(name="category", data_type=DataType.TEXT),
            Property(name="title", data_type=DataType.TEXT),
            Property(name="content", data_type=DataType.TEXT),
        ],
        vectorizer_config=Configure.Vectorizer.none(),
        vector_index_config=Configure.VectorIndex.hnsw(distance_metric=VectorDistances.COSINE),
    )

    logger.info(f"Collection {collection_name} created successfully")
    return rag_collection
