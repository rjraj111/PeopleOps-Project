import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

load_dotenv()

def get_llm():
    # Primary Model: Google Gemini (Free Tier)
    primary_llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        temperature=0,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

    # Fallback Model: OpenRouter
    fallback_llm = ChatOpenAI(
        model="meta-llama/llama-3.1-8b-instruct:free",
        temperature=0,
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
    )

    return primary_llm.with_fallbacks([fallback_llm])
