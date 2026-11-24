import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

load_dotenv()

def get_secret(key: str, default=None):
    # 1. Direct environment variable
    val = os.getenv(key)
    if val:
        return val

    # 2. Case-insensitive environment variable check
    for env_k, env_v in os.environ.items():
        if env_k.strip().upper() == key.strip().upper() and env_v:
            return env_v

    # 3. Streamlit secrets & session state
    try:
        import streamlit as st
        if hasattr(st, "session_state") and key in st.session_state and st.session_state[key]:
            return str(st.session_state[key])

        if hasattr(st, "secrets"):
            if key in st.secrets and st.secrets[key]:
                return str(st.secrets[key])
            for s_k, s_v in st.secrets.items():
                if s_k.strip().upper() == key.strip().upper() and s_v:
                    return str(s_v)
                if isinstance(s_v, dict):
                    for sub_k, sub_v in s_v.items():
                        if sub_k.strip().upper() == key.strip().upper() and sub_v:
                            return str(sub_v)
    except Exception:
        pass

    return default

def get_llm():
    google_api_key = get_secret("GOOGLE_API_KEY") or get_secret("GEMINI_API_KEY")
    openrouter_api_key = get_secret("OPENROUTER_API_KEY")

    if not google_api_key and not openrouter_api_key:
        raise ValueError(
            "API key à¦ªà¦¾à¦“à¦¯à¦¼à¦¾ à¦¯à¦¾à¦¯à¦¼à¦¨à¦¿! Streamlit Cloud-à¦à¦° App Settings -> Secrets à¦ GOOGLE_API_KEY à¦¯à§à¦•à§à¦¤ à¦•à¦°à§à¦¨ã€‚"
        )

    # Primary Model: Google Gemini (gemini-3.8-flash / gemini-1.5-flash)
    primary_llm = None
    if google_api_key:
        primary_llm = ChatGoogleGenerativeAI(
            model="gemini-3.8-flash",
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
        return primary_llm.with_fallbacks([fallback_llm], exceptions_to_handle=(Exception,))
    elif primary_llm:
        return primary_llm
    elif fallback_llm:
        return fallback_llm
    else:
        raise ValueError("à¦•à§‹à¦¨à§‹ à¦•à¦¾à¦°à§à¦¯à¦•à¦°à§€ LLM à¦•à¦¨à¦«à¦¿à¦—à¦¾à¦° à¦•à¦°à¦¾ à¦¸à¦®à§à¦­à¦¬ à¦¹à¦¯à¦¼à¦¨à¦¿à¥¤")
