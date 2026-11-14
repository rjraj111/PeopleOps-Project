# PeopleOps Project

A workspace repository for PeopleOps Copilot — an autonomous internal HR Policy, Leave, and Expense Reimbursement Assistant built with **LangGraph**, **LangChain**, and **Google Gemini** (with OpenRouter fallback).

## Modules

- [`peopleops-copilot/`](./peopleops-copilot) : Core source code, RAG policy retriever, SQLite database schema & seeds, and ReAct agent workflows.

## Quick Start

1. **Clone the repository**:
   ```bash
   git clone https://github.com/rjraj111/PeopleOps-Project.git
   cd PeopleOps-Project
   ```

2. **Set up Python Virtual Environment**:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   cd peopleops-copilot
   pip install -r requirements.txt
   ```

4. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your Google Gemini / OpenRouter API keys
   ```

5. **Seed Database**:
   ```bash
   python data/seed_db.py
   ```
