# 🤖 PeopleOps Copilot (`peopleops-copilot`)

Core application module for **PeopleOps Copilot** — an autonomous HR Policy RAG, Leave & Expense Reimbursement Assistant with a **Human-in-the-Loop Admin Governance Panel**, **Real-Time Employee Notifications**, **LangSmith Observability**, and a **FastAPI REST Backend**.

## ✨ Highlights

- **💬 User Copilot:** LangGraph ReAct agent with ChromaDB cited policy RAG (`[filename, Section]`), conversation memory, and searchable access to all **1,470 employees**.
- **🛡️ Admin Governance Panel:** Review High-Risk escalations (`> 3 days` leave, `> 5,000 BDT` or over-cap expenses), add manager remarks, approve/decline with automatic balance updates, and inspect full audit logs.
- **🔔 Real-Time Notifications:** Instant inbox delivery to employees whenever an admin approves or declines a request.
- **⚡ Resilient Dual-LLM:** OpenRouter (`openrouter/free`) primary with automatic fallback to Google Gemini (`gemini-3.8-flash`).
- **🔌 FastAPI Backend:** Interactive Swagger UI at `/docs` exposing `/chat`, `/employee/{id}`, `/admin/pending`, and `/admin/review`.

## 🚀 Running Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure .env from template
cp .env.example .env

# 3. Seed the SQLite database (1,470 employees + sample escalations)
python data/seed_db.py

# 4. Run Streamlit UI (http://localhost:8501)
streamlit run app.py

# 5. (Optional) Run FastAPI Backend (http://127.0.0.1:8000/docs)
uvicorn api:app --reload
```

For full architecture diagrams, policy rules, and demo walkthrough, see the root [README.md](../README.md).
