#!/usr/bin/env python3
"""
Data Loader Script for Diet & Nutrition RAG System

This script:
1. Connects to Weaviate vector database
2. Creates the schema for diet knowledge
3. Generates embeddings using configured embedding model
4. Loads all diet knowledge into Weaviate

Supports both original and expanded datasets.

Usage:
    python scripts/data_loader.py [--use-expanded]
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import weaviate  # noqa
from weaviate.util import generate_uuid5  # noqa

from settings import configs  # noqa
from settings.db import create_schema, init_weaviate_client  # noqa
from settings.embedding import init_embedding  # noqa
from settings.logger import configure_logging  # noqa

configure_logging()
logger = logging.getLogger("data_loader")

DATA_DIR = Path(__file__).parent / "data"
ORIGINAL_DATA_FILE = DATA_DIR / "diet_knowledge.json"
EXPANDED_DATA_FILE = DATA_DIR / "expanded_diet_knowledge.json"


def get_data_with_embedding_vector(data_file: Path, embedding_model) -> list[dict]:
    """Load data from JSON file and generate embeddings."""
    logger.info(f"Loading data from {data_file}")
    with open(data_file) as f:
        documents_data = json.load(f)

    logger.info(f"Found {len(documents_data)} documents to process")

    logger.info("Generating embeddings for all documents")
    contents_to_embed = [doc["content"] for doc in documents_data]
    vector_embeddings = embedding_model.embed_documents(contents_to_embed)

    if isinstance(vector_embeddings, dict):
        raise ValueError(f"Embedding API Error: {vector_embeddings}")

    logger.info(f"Generated {len(vector_embeddings)} embeddings. Vector dimension: {len(vector_embeddings[0])}")

    for i, doc in enumerate(documents_data):
        doc["content_vector"] = vector_embeddings[i]

    return documents_data


def load_data(collection: weaviate.collections.Collection, documents_data: list[dict]) -> None:
    """Load documents into Weaviate collection."""
    logger.info(f"Ingesting {len(documents_data)} documents into database")

    with collection.batch.dynamic() as batch:
        for doc in documents_data:
            properties = {
                "doc_id": doc["id"],
                "category": doc["category"],
                "title": doc["title"],
                "content": doc["content"],
            }
            batch.add_object(
                properties=properties,
                vector=doc["content_vector"],
                uuid=generate_uuid5(doc["title"]),
            )

    logger.info(f"Data ingestion complete. Total objects in collection: {len(collection)}")


def verify_data(collection: weaviate.collections.Collection) -> None:
    """Verify the loaded data."""
    logger.info("Verifying loaded data...")

    count = collection.aggregate.over_all(total_count=True).total_count
    logger.info(f"Total documents in collection: {count}")

    sample = collection.query.fetch_objects(limit=3)
    if sample.objects:
        logger.info("Sample documents:")
        for obj in sample.objects:
            logger.info(f"  - {obj.properties['title']} ({obj.properties['category']})")


def get_collection_stats(collection: weaviate.collections.Collection) -> dict:
    """Get statistics about the collection."""
    stats = {
        "total_count": collection.aggregate.over_all(total_count=True).total_count,
        "categories": {},
    }

    all_docs = collection.query.fetch_objects(limit=1000)
    for obj in all_docs.objects:
        category = obj.properties.get("category", "Unknown")
        stats["categories"][category] = stats["categories"].get(category, 0) + 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="Load diet knowledge data into Weaviate")
    parser.add_argument("--use-expanded", action="store_true", help="Use the expanded dataset with more documents")
    parser.add_argument("--force-reload", action="store_true", help="Force reload even if data exists")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Starting Diet & Nutrition RAG Data Loader")
    logger.info("=" * 60)

    if configs.SKIP_DATA_LOADER and not args.force_reload:
        logger.info("Skipping data loader due to SKIP_DATA_LOADER environment variable")
        return

    data_file = EXPANDED_DATA_FILE if args.use_expanded else ORIGINAL_DATA_FILE

    if args.use_expanded:
        logger.info("Using EXPANDED dataset")
    else:
        logger.info("Using ORIGINAL dataset")

    if not data_file.exists():
        logger.error(f"Data file not found: {data_file}")
        sys.exit(1)
    logger.info(f"Data file found: {data_file}")

    weaviate_client = None
    try:
        weaviate_client = init_weaviate_client(configs.WEAVIATE_URL)

        embedding_model = init_embedding()
        logger.info("Embedding model initialized")

        rag_collection = create_schema(weaviate_client, configs.COLLECTION_NAME)
        documents_data = get_data_with_embedding_vector(data_file, embedding_model)
        load_data(rag_collection, documents_data)

        verify_data(rag_collection)

        stats = get_collection_stats(rag_collection)
        logger.info("=" * 60)
        logger.info("Collection Statistics:")
        logger.info(f"  Total Documents: {stats['total_count']}")
        logger.info("  By Category:")
        for category, count in sorted(stats["categories"].items()):
            logger.info(f"    - {category}: {count}")
        logger.info("=" * 60)

        logger.info("Data loading completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.exception(f"Error during data loading: {e}")
        sys.exit(1)
    finally:
        if weaviate_client:
            weaviate_client.close()


if __name__ == "__main__":
    main()
