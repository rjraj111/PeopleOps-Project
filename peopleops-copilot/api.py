from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.agent import run_copilot
from src.tools.hr_tools import get_employee_profile_and_balances

app = FastAPI(
    title="PeopleOps Copilot API",
    description="Autonomous HR Policy RAG & SQLite Action Agent powered by LangGraph & FastAPI",
    version="1.0.0"
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

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
