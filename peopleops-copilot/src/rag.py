import os
import glob
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from src.llm import get_llm, get_secret

load_dotenv()

CHROMA_DIR = os.path.join("data", "chroma_db")
POLICY_DIR = os.path.join("data", "policies")

def get_vectorstore():
    google_api_key = get_secret("GOOGLE_API_KEY") or get_secret("GEMINI_API_KEY")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=google_api_key,
    )

    if os.path.exists(CHROMA_DIR) and os.listdir(CHROMA_DIR):
        return Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

    docs = []
    headers_to_split_on = [("##", "Section")]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

    for filepath in glob.glob(os.path.join(POLICY_DIR, "*.md")):
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        splits = markdown_splitter.split_text(content)
        for split in splits:
            raw_sec = split.metadata.get("Section", "General")
            sec_short = raw_sec.split(":")[0].strip()  # Extracts 'Sec 1', 'Sec 2', etc.
            docs.append(
                Document(
                    page_content=split.page_content,
                    metadata={"source": filename, "section": sec_short},
                )
            )

    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
    )
    return vectorstore

def answer_policy_question(query: str) -> str:
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    retrieved_docs = retriever.invoke(query)

    if not retrieved_docs:
        return "I'm not able to answer that request. Not found in policy. Please contact your HR team directly for further assistance."

    context_blocks = []
    for doc in retrieved_docs:
        src = doc.metadata.get("source", "unknown.md")
        sec = doc.metadata.get("section", "Sec 1")
        context_blocks.append(f"\n{doc.page_content}")

    context_text = "\n\n---\n\n".join(context_blocks)

    prompt = f"""You are PeopleOps Copilot, an internal HR policy assistant.
Answer the user's question strictly using ONLY the provided policy context below.
Rules:
1. You MUST include inline citations in the exact format at the end of relevant sentences.
2. If the answer cannot be found in the context, reply exactly: "I'm not able to answer that request. Not found in policy. Please contact your HR team directly for further assistance."
3. Be concise, accurate, and helpful.

Context:
{context_text}

Question: {query}
Answer:"""

    llm = get_llm()
    response = llm.invoke(prompt)
    return response.text if hasattr(response, "text") else "".join([b["text"] for b in response.content if isinstance(b, dict) and "text" in b]) if isinstance(response.content, list) else str(response.content)
