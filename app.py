#!/usr/bin/env python3
"""
Diet & Nutrition RAG Assistant - Streamlit Application

This application provides an AI-powered diet and nutrition assistant
using RAG (Retrieval-Augmented Generation) with Weaviate and OpenAI.

All operations are logged for container visibility.
"""

import logging

import streamlit as st
import weaviate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from weaviate.classes.query import MetadataQuery

from settings import configs
from settings.chat_model import init_ai_model
from settings.db import init_weaviate_client
from settings.embedding import init_embedding
from settings.logger import configure_logging

configure_logging()
logger = logging.getLogger("diet_rag_app")


def generate_embedding(
    chat_model: AzureChatOpenAI, embedding_model: AzureOpenAIEmbeddings, user_query: str
) -> list[float]:
    """Generate embedding vector for query text."""
    logger.info(f"Generating embedding for query: {user_query[:50]}...")

    expansion_prompt = ChatPromptTemplate.from_template(
        "You are an expert in information retrieval. "
        "Please rephrase the following user query to be more descriptive and detailed, "
        "making it suitable for a vector database search. "
        "Return only the rephrased query, without any additional text, headers, or explanations. "
        "\n\nOriginal Query: '{query}'\n\nRephrased Query:"
    )
    query_expansion_chain = expansion_prompt | chat_model | StrOutputParser()

    expanded_query = query_expansion_chain.invoke({"query": user_query})
    query_embedding = embedding_model.embed_query(expanded_query)

    logger.info(f"Generated embedding with {len(query_embedding)} dimensions")
    return query_embedding


def search_similar_documents(
    collection: weaviate.collections.Collection, query_embedding: list[float], top_k: int = configs.TOP_K_RESULTS
) -> list[dict]:
    """Search for similar documents in Weaviate."""
    logger.info(f"Searching for top {top_k} similar documents")

    results = collection.query.near_vector(
        near_vector=query_embedding, limit=top_k, return_metadata=MetadataQuery(distance=True)
    )

    documents = []
    for obj in results.objects:
        doc = {
            "title": obj.properties["title"],
            "category": obj.properties["category"],
            "content": obj.properties["content"],
            "distance": obj.metadata.distance if obj.metadata else None,
        }
        documents.append(doc)
        logger.info(f"  - Found: {doc['title']} (distance: {doc['distance']:.4f})")

    logger.info(f"Retrieved {len(documents)} relevant documents")
    return documents


def format_context(documents: list[dict]) -> str:
    """Format retrieved documents as context for LLM."""
    context_parts = []
    for i, doc in enumerate(documents, 1):
        context_parts.append(f"[Document {i}: {doc['title']} ({doc['category']})]\n{doc['content']}")
    return "\n\n".join(context_parts)


def generate_response(chat_model: AzureChatOpenAI, user_query: str, context: str) -> str:
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

    if "openai_client" not in st.session_state:
        if not configs.AZURE_OPENAI_API_KEY:
            st.error("OpenAI API key not configured!")
            logger.error("AZURE_OPENAI_API_KEY not set")
            return

        st.session_state.chat_model = init_ai_model()
        logger.info("OpenAI client stored in session state")

        st.session_state.embedding_model = init_embedding()
        logger.info("Embedding model stored in session state")

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
                    # Step 1: Generate embedding for query
                    query_embedding = generate_embedding(
                        st.session_state.chat_model, st.session_state.embedding_model, user_query
                    )

                    # Step 2: Search for relevant documents
                    documents = search_similar_documents(st.session_state.collection, query_embedding)

                    # Step 3: Format context
                    context = format_context(documents)
                    logger.info(f"Context prepared ({len(context)} characters)")

                    # Step 4: Generate LLM response
                    response = generate_response(st.session_state.chat_model, user_query, context)

                    # Display response
                    st.markdown(response)

                    # Display sources
                    if documents:
                        with st.expander("📚 View Sources"):
                            for doc in documents:
                                st.markdown(f"**{doc['title']}** ({doc['category']})")
                                st.caption(f"Relevance: {1 - doc['distance']:.2%}")
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
        st.caption(
            "⚠️ This is for educational purposes only. Consult a healthcare professional for personalized advice."
        )


if __name__ == "__main__":
    main()
