from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from langgraph.prebuilt import create_react_agent
from src.llm import get_llm
from src.rag import answer_policy_question
from src.tools.hr_tools import (
    get_employee_profile_and_balances,
    submit_leave_request,
    submit_expense_claim,
    get_employee_history,
)

@tool
def lookup_hr_policy(question: str) -> str:
    """Search official company HR policy documents (Leave Policy, Expense Reimbursement Rules, Medical & Wellness Benefits) to answer policy questions with citations."""
    return answer_policy_question(question)

TOOLS = [
    lookup_hr_policy,
    get_employee_profile_and_balances,
    submit_leave_request,
    submit_expense_claim,
    get_employee_history,
]

SYSTEM_PROMPT = """You are PeopleOps Copilot, an autonomous internal HR Policy, Leave & Expense Reimbursement Assistant.
You have access to official company HR policy documents via `lookup_hr_policy` and the live employee database via HR database tools.

Operational Rules:
1. For any question about company rules, quotas, caps, notice periods, medical coverage, or approval thresholds, ALWAYS call `lookup_hr_policy` first and preserve its citations.
2. When an employee asks to check balances, view history, apply for leave, or submit an expense claim, use the appropriate database tool. If `employee_id` is missing, politely ask for it (e.g., EMP-101).
3. Highlight any High-Risk Escalation flags clearly (e.g., leave > 3 consecutive days or expense claims > 5,000 BDT requiring human manager approval).
4. Keep responses concise, structured, and helpful. Never fabricate policy details or database records."""

def build_agent():
    llm = get_llm()
    return create_react_agent(llm, tools=TOOLS, prompt=SystemMessage(content=SYSTEM_PROMPT))

def run_copilot(user_message: str) -> str:
    agent = build_agent()
    result = agent.invoke({"messages": [("user", user_message)]})
    final_msg = result["messages"][-1]
    content = final_msg.content
    if isinstance(content, list):
        return "".join([b["text"] for b in content if isinstance(b, dict) and "text" in b])
    return str(content)
