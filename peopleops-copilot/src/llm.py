import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

load_dotenv()

def get_secret(key: str) -> str | None:
    val = os.getenv(key)
    if val:
        return val
    try:
        import streamlit as st
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return None

def get_llm():
    google_key = get_secret("GOOGLE_API_KEY")
    openrouter_key = get_secret("OPENROUTER_API_KEY")

    primary_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        api_key=google_key,
    )

    if openrouter_key:
        print("✅ OpenRouter Fallback LLM (Llama 3.3 70B) is ACTIVE")
        fallback_llm = ChatOpenAI(
            model="meta-llama/llama-3.3-70b-instruct:free",
            temperature=0,
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
        )
        return primary_llm.with_fallbacks([fallback_llm])

    return primary_llm
