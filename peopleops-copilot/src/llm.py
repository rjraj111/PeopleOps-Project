import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

load_dotenv()

def get_secret(key: str, default=None):
    val = os.getenv(key)
    if not val:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and key in st.secrets:
                val = str(st.secrets[key])
        except Exception:
            pass
    return val or default

def get_llm():
    google_api_key = get_secret("GOOGLE_API_KEY") or get_secret("GEMINI_API_KEY")
    openrouter_api_key = get_secret("OPENROUTER_API_KEY")

    if not google_api_key and not openrouter_api_key:
        raise ValueError(
            "API key পাওয়া যায়নি! Streamlit Cloud-এর App Settings -> Secrets এ GOOGLE_API_KEY যুক্ত করুন。"
        )

    # Primary Model: Google Gemini (gemini-2.0-flash / gemini-1.5-flash)
    primary_llm = None
    if google_api_key:
        primary_llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            google_api_key=google_api_key,
        )

    # Fallback Model: OpenRouter
    fallback_llm = None
    if openrouter_api_key:
        fallback_llm = ChatOpenAI(
            model="meta-llama/llama-3.1-8b-instruct:free",
            temperature=0,
            openai_api_key=openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
        )

    if primary_llm and fallback_llm:
        return primary_llm.with_fallbacks([fallback_llm])
    elif primary_llm:
        return primary_llm
    elif fallback_llm:
        return fallback_llm
    else:
        raise ValueError("কোনো কার্যকরী LLM কনফিগার করা সম্ভব হয়নি।")
