#!/usr/bin/env python3
"""
Diet & Nutrition RAG Assistant - Streamlit Application

This application provides an AI-powered diet and nutrition assistant
using RAG (Retrieval-Augmented Generation) with Weaviate and OpenAI.

All operations are logged for container visibility.
"""

import logging
import time

import streamlit as st
import weaviate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from sentence_transformers import CrossEncoder, SentenceTransformer
from weaviate.classes.query import MetadataQuery

from settings import configs
from settings.chat_model import init_ai_model
from settings.db import init_weaviate_client
from settings.embedding import init_embedding
from settings.logger import configure_logging

configure_logging()
logger = logging.getLogger("diet_rag_app")


class EnhancedRetriever:
    """Enhanced retriever with hybrid search and reranking."""

    def __init__(
        self,
        collection: weaviate.collections.Collection,
        embedding_model: SentenceTransformer,
        reranker: CrossEncoder,
        rrf_k: int = 60,
    ):
        self.collection = collection
        self.embedding_model = embedding_model
        self.reranker = reranker
        self.rrf_k = rrf_k

    def search(self, query: str, top_k: int = 5, candidate_pool: int = 15) -> list[dict]:
        start = time.perf_counter()

        # query_embedding = self.embedding_model.encode(query).tolist()
        query_embedding = self.embedding_model.embed_query(query)
        vector_results = self.collection.query.near_vector(
            near_vector=query_embedding, limit=candidate_pool, return_metadata=MetadataQuery(distance=True)
        )

        bm25_results = self.collection.query.bm25(
            query=query,
            limit=candidate_pool,
            return_metadata=MetadataQuery(score=True),
            query_properties=["title", "content", "category"],
        )

        doc_scores = {}
        doc_data = {}

        for rank, obj in enumerate(vector_results.objects, 1):
            doc_id = obj.properties["doc_id"]
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 1 / (self.rrf_k + rank)
            doc_data[doc_id] = {
                "doc_id": doc_id,
                "title": obj.properties["title"],
                "category": obj.properties["category"],
                "content": obj.properties["content"],
                "vector_distance": obj.metadata.distance if obj.metadata else None,
            }

        for rank, obj in enumerate(bm25_results.objects, 1):
            doc_id = obj.properties["doc_id"]
            doc_scores[doc_id] = doc_scores.get(doc_id, 0) + 1 / (self.rrf_k + rank)
            if doc_id not in doc_data:
                doc_data[doc_id] = {
                    "doc_id": doc_id,
                    "title": obj.properties["title"],
                    "category": obj.properties["category"],
                    "content": obj.properties["content"],
                    "bm25_score": obj.metadata.score if obj.metadata else None,
                }

        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        candidates = [doc_data[doc_id] for doc_id, _ in sorted_docs[:candidate_pool]]

        if candidates:
            pairs = [(query, doc["content"]) for doc in candidates]
            rerank_scores = self.reranker.predict(pairs)

            for doc, score in zip(candidates, rerank_scores, strict=True):
                doc["rerank_score"] = float(score)

            candidates.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

        latency = (time.perf_counter() - start) * 1000
        logger.info(f"Enhanced search completed in {latency:.1f}ms")

        return candidates[:top_k]


def format_context(documents: list[dict]) -> str:
    """Format retrieved documents as context for LLM."""
    context_parts = []
    for i, doc in enumerate(documents, 1):
        context_parts.append(f"[Document {i}: {doc['title']} ({doc['category']})]\n{doc['content']}")
    return "\n\n".join(context_parts)


def generate_response(chat_model, user_query: str, context: str) -> str:
    """Generate LLM response using RAG context."""
    logger.info("Generating LLM response with RAG context")

    generation_prompt = ChatPromptTemplate.from_template(
        "You are a helpful Diet and Nutrition Assistant. "
        "Your task is to answer the user's question based only on the provided context, "
        "do not use common knowledge, do not correct mistakes in provided context. "
        "Synthesize the information from the context into a concise, bullet-point summary. "
        "Focus on specific details like names, numbers, and technical terms mentioned in the context. "
        "If the context does not contain the information needed to answer the question, "
        "you must state: 'The provided context does not contain the answer to this question.' "
        "\n\nContext:\n{context}\n\nQuestion: {question}"
    )

    answer_generation_chain = generation_prompt | chat_model | StrOutputParser()

    final_answer = answer_generation_chain.invoke({"context": context, "question": user_query})

    return final_answer


def main():
    """Main Streamlit application."""
    logger.info("Starting Diet & Nutrition RAG Application")

    # Page configuration
    st.set_page_config(page_title="Diet & Nutrition Assistant", page_icon="🥗", layout="wide")

    # Title and description
    st.title("🥗 Diet & Nutrition RAG Assistant")
    st.markdown("""
    Welcome to the Diet & Nutrition Assistant! Ask me anything about:
    - **Macronutrients** (proteins, carbs, fats)
    - **Micronutrients** (vitamins, minerals)
    - **Diet Types** (Mediterranean, Keto, Vegan, Paleo)
    - **Meal Planning** tips and strategies
    - **Special Diets** (weight loss, diabetic, heart-healthy)
    - **Food Facts** and nutritional information
    """)
    st.divider()

    st.markdown("""
        **Enhanced version** with:
        - Hybrid Search (Vector + BM25)
        - Cross-Encoder Reranking
        - Improved retrieval accuracy
        """)

    st.divider()

    # Initialize clients (cached)
    if "weaviate_client" not in st.session_state:
        with st.spinner("Connecting to database..."):
            try:
                st.session_state.weaviate_client = init_weaviate_client(configs.WEAVIATE_URL)
                st.session_state.collection = st.session_state.weaviate_client.collections.get(configs.COLLECTION_NAME)
                logger.info("Weaviate client and collection stored in session state")
            except Exception as e:
                st.error(f"Failed to connect to database: {e}")
                logger.error(f"Weaviate connection failed: {e}")
                return

    if "chat_model" not in st.session_state:
        st.session_state.chat_model = init_ai_model()
        logger.info("Chat model stored in session state")

    if "embedding_model" not in st.session_state:
        st.session_state.embedding_model = init_embedding()
        logger.info("Embedding model stored in session state")

    if "reranker" not in st.session_state:
        with st.spinner("Loading reranker model..."):
            st.session_state.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info("Reranker model stored in session state")

    if "enhanced_retriever" not in st.session_state:
        st.session_state.enhanced_retriever = EnhancedRetriever(
            collection=st.session_state.collection,
            embedding_model=st.session_state.embedding_model,
            reranker=st.session_state.reranker,
        )
        logger.info("Enhanced retriever initialized")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sources" in message and message["sources"]:
                with st.expander("📚 View Sources"):
                    for source in message["sources"]:
                        st.markdown(f"**{source['title']}** ({source['category']})")
                        if "rerank_score" in source:
                            st.caption(f"Relevance Score: {source['rerank_score']:.3f}")
                        st.caption(source["content"][:200] + "...")

    # User input
    if user_query := st.chat_input("Ask me about diet and nutrition..."):
        logger.info(f"User query received: {user_query}")

        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Searching knowledge base..."):
                try:
                    # Enhanced retrieval
                    documents = st.session_state.enhanced_retriever.search(user_query, top_k=5)

                    # Format context
                    context = format_context(documents)
                    logger.info(f"Context prepared ({len(context)} characters)")

                    # Generate response
                    response = generate_response(st.session_state.chat_model, user_query, context)

                    st.markdown(response)

                    # Display sources
                    if documents:
                        with st.expander("📚 View Sources"):
                            for doc in documents:
                                st.markdown(f"**{doc['title']}** ({doc['category']})")
                                if "rerank_score" in doc:
                                    st.caption(f"Relevance Score: {doc['rerank_score']:.3f}")
                                st.caption(doc["content"][:200] + "...")

                    # Save to history
                    st.session_state.messages.append({"role": "assistant", "content": response, "sources": documents})

                    logger.info("Response generated and displayed successfully")

                except Exception as e:
                    error_msg = f"Error generating response: {e}"
                    st.error(error_msg)
                    logger.exception(error_msg)

    # Sidebar with info
    with st.sidebar:
        st.header("ℹ️ About")
        st.markdown("""
        This AI assistant uses **RAG (Retrieval-Augmented Generation)**
        to provide accurate diet and nutrition information.

        **How it works:**
        1. Your question is converted to a vector embedding
        2. Similar documents are retrieved from the knowledge base
        3. The LLM generates a response using the retrieved context
        """)

        st.divider()
        st.header("💡 Example Questions")
        st.markdown("""
        - What are the benefits of the Mediterranean diet?
        - How much protein do I need daily?
        - What foods are high in vitamin D?
        - Is the keto diet safe for everyone?
        - What should a balanced meal look like?
        """)

        st.divider()
        st.header("❌ Example NOT in RAG questions")
        st.markdown("""
        - What is weather like in Almaty?
        """)

        st.divider()
        st.caption(
            "⚠️ This is for educational purposes only. Consult a healthcare professional for personalized advice."
        )


if __name__ == "__main__":
    main()
