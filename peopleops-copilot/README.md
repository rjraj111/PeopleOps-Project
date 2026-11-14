# PeopleOps Copilot 🤖

An autonomous internal HR Policy, Leave, and Expense Reimbursement Assistant built with **LangGraph**, **LangChain**, and **Google Gemini** (with OpenRouter fallback).

## Features

- **Policy Lookup (RAG)**: Query company leave rules, expense reimbursement guidelines, and medical/wellness benefits with section-level citations using ChromaDB vector search.
- **HR System Integration**:
  - Employee profile & leave balance lookup.
  - Leave application submissions with policy validation.
  - Expense claim submissions with approval threshold checks.
  - Employee history tracking.
- **High-Risk Escalation Detection**: Automated detection of requests requiring managerial approval (e.g., >3 days consecutive leave, >5,000 BDT expense claims).
- **LangSmith Tracing**: Full observability and tracing of agent tool calls and LLM reasoning steps.

## Project Structure

```
peopleops-copilot/
├── data/
│   ├── chroma_db/       # Chroma vector store (auto-generated)
│   ├── db/              # SQLite database (hr_system.db)
│   ├── policies/        # Markdown policy documents
│   └── seed_db.py       # DB initialization script
├── src/
│   ├── tools/           # HR database tools
│   ├── agent.py         # LangGraph ReAct agent
│   ├── llm.py           # Multi-tier LLM configuration
│   └── rag.py           # Vectorstore & policy retrieval
├── .env.example         # Environment variable template
├── requirements.txt     # Python dependencies
└── README.md
```

## Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/rjraj111/PeopleOps-Project.git
   cd PeopleOps-Project
   ```

2. **Create a virtual environment & install dependencies**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate

   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```

4. **Seed Database**:
   ```bash
   python data/seed_db.py
   ```
