from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.agent import run_copilot
from src.tools.hr_tools import (
    get_employee_profile_and_balances,
    get_all_leave_requests,
    get_all_expense_claims,
    review_leave_request,
    review_expense_claim,
)

app = FastAPI(
    title="PeopleOps Copilot API",
    description="Autonomous HR Policy RAG, SQLite Action Agent & Admin Approval API powered by LangGraph & FastAPI",
    version="1.1.0"
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

class AdminReviewRequest(BaseModel):
    request_type: str  # "leave" or "expense"
    record_id: str     # e.g., "LV-1002" or "CLM-1002"
    action: str        # "approve" or "decline"
    note: str = ""

@app.get("/")
def health_check():
    return {"status": "active", "service": "PeopleOps Copilot FastAPI"}

@app.get("/employee/{employee_id}")
def fetch_employee(employee_id: str):
    result = get_employee_profile_and_balances.invoke({"employee_id": employee_id})
    if "not found" in result.lower():
        raise HTTPException(status_code=404, detail=result)
    return {"employee_id": employee_id, "profile": result}

@app.post("/chat", response_model=ChatResponse)
def chat_with_copilot(request: ChatRequest):
    try:
        answer = run_copilot(request.message)
        return ChatResponse(reply=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/pending")
def list_pending_escalations():
    return {
        "pending_leaves": get_all_leave_requests(pending_only=True),
        "pending_expenses": get_all_expense_claims(pending_only=True),
    }

@app.post("/admin/review")
def admin_review(request: AdminReviewRequest):
    req_type = request.request_type.strip().lower()
    if req_type == "leave":
        ok, msg = review_leave_request(request.record_id, request.action, request.note)
    elif req_type == "expense":
        ok, msg = review_expense_claim(request.record_id, request.action, request.note)
    else:
        raise HTTPException(status_code=400, detail="request_type must be 'leave' or 'expense'")
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"success": True, "message": msg}
