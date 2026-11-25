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

def configure_langsmith() -> bool:
    """Enable LangSmith tracing automatically whenever a LangSmith/LangChain API key is available."""
    api_key = get_secret("LANGSMITH_API_KEY") or get_secret("LANGCHAIN_API_KEY")
    if api_key and not api_key.startswith("your_"):
        project = get_secret("LANGSMITH_PROJECT") or get_secret("LANGCHAIN_PROJECT") or "PeopleOps-Copilot"
        endpoint = get_secret("LANGSMITH_ENDPOINT") or get_secret("LANGCHAIN_ENDPOINT") or "https://api.smith.langchain.com"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGSMITH_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project
        os.environ["LANGSMITH_PROJECT"] = project
        os.environ["LANGCHAIN_ENDPOINT"] = endpoint
        os.environ["LANGSMITH_ENDPOINT"] = endpoint
        return True
    return False

configure_langsmith()

class ResilientLLM:
    def __init__(self, primary, fallbacks):
        self.primary = primary
        self.fallbacks = fallbacks
        self.chain = primary.with_fallbacks(fallbacks) if fallbacks else primary

    def invoke(self, *args, **kwargs):
        return self.chain.invoke(*args, **kwargs)

    def bind_tools(self, tools, **kwargs):
        bound_primary = self.primary.bind_tools(tools, **kwargs)
        bound_fallbacks = [fb.bind_tools(tools, **kwargs) for fb in self.fallbacks]
        return bound_primary.with_fallbacks(bound_fallbacks) if bound_fallbacks else bound_primary

    def with_structured_output(self, schema, **kwargs):
        bound_primary = self.primary.with_structured_output(schema, **kwargs)
        bound_fallbacks = [fb.with_structured_output(schema, **kwargs) for fb in self.fallbacks]
        return bound_primary.with_fallbacks(bound_fallbacks) if bound_fallbacks else bound_primary

    def __getattr__(self, name):
        return getattr(self.chain, name)

def get_llm():
    google_key = get_secret("GOOGLE_API_KEY") or get_secret("GEMINI_API_KEY")
    openrouter_key = get_secret("OPENROUTER_API_KEY")

    gemini_llm = ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        temperature=0,
        max_retries=1,
        timeout=15,
        api_key=google_key,
    )

    if openrouter_key:
        openrouter_llm = ChatOpenAI(
            model="openrouter/free",
            temperature=0,
            max_retries=2,
            timeout=20,
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
        )
        return ResilientLLM(openrouter_llm, [gemini_llm])

    return ResilientLLM(gemini_llm, [])
