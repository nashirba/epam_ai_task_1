import logging

import torch
from huggingface_hub import login
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from transformers import pipeline

from settings import configs

logger = logging.getLogger(__name__)


class LocalHuggingFaceChatModel(Runnable):
    """
    A simple wrapper around the Transformers Pipeline to make it compatible
    with LangChain's 'invoke' method and the pipe '|' operator.
    """

    def __init__(self, model_name):
        print(f"📥 Loading local LLM: {model_name}...")
        # This is the 'Automatic Transmission' setup we discussed:
        # 1. device=-1 forces CPU usage.
        # 2. torch_dtype=torch.float32 is the fastest format for CPU.
        self.pipe = pipeline("text-generation", model=model_name, device=-1, torch_dtype=torch.float32)
        print("✅ Local LLM loaded successfully.")

    def invoke(self, input_data, config: RunnableConfig = None, **kwargs):
        """
        Adapts LangChain inputs (PromptValue or Messages) to the pipeline format.
        """
        # 1. Convert LangChain input to the list-of-dicts format expected by the pipeline
        messages = []

        # Handle LangChain PromptValue (which has .to_messages())
        if hasattr(input_data, "to_messages"):
            lc_messages = input_data.to_messages()
            for msg in lc_messages:
                # Map LangChain message types to role strings
                role = "user"
                if msg.type == "system":
                    role = "system"
                elif msg.type == "ai":
                    role = "assistant"

                # Gemma pipeline expects content as a list of dicts or string.
                messages.append({"role": role, "content": [{"type": "text", "text": msg.content}]})

        # Handle raw string input (fallback)
        elif isinstance(input_data, str):
            messages = [{"role": "user", "content": [{"type": "text", "text": input_data}]}]

        # 2. Run the pipeline ("Automatic Transmission")
        # We set max_new_tokens to limit the answer length
        outputs = self.pipe(messages, max_new_tokens=512)

        # 3. Extract the generated text
        # The pipeline returns a list of dicts. The last message is the assistant's reply.
        generated_text = outputs[0]["generated_text"][-1]["content"]

        # 4. Return as an AIMessage to satisfy LangChain's StrOutputParser
        return AIMessage(content=generated_text)


def init_ai_model() -> AzureChatOpenAI | LocalHuggingFaceChatModel | ChatOpenAI:
    logger.info("Initializing OpenAI client")
    if configs.LLM_SOURCE == "local":
        logger.info("Logging to HUGGINGFACE...")
        login(token=configs.HUGGINGFACE_API_TOKEN)
        return LocalHuggingFaceChatModel(configs.LOCAL_LLM_MODEL_NAME)

    elif configs.LLM_SOURCE == "hf_api":
        logger.info(f"🌐 Connecting to HF Serverless Chat: {configs.HF_API_CHAT_MODEL}")
        # Using standard OpenAI client but pointing to HF URL
        return ChatOpenAI(
            model=configs.HF_API_CHAT_MODEL,
            openai_api_key=configs.HUGGINGFACE_API_TOKEN,
            # openai_api_base=f"{configs.HF_API_ENDPOINT_BASE}/models/{configs.HF_API_CHAT_MODEL}/v1",
            openai_api_base=f"{configs.HF_API_ENDPOINT_BASE}/v1",
            temperature=0.1,
            max_tokens=1024,
        )

    return AzureChatOpenAI(
        azure_deployment=configs.AZURE_OPENAI_CHAT_DEPLOYMENT,
        api_version=configs.AZURE_OPENAI_API_VERSION,
        temperature=0,
    )
