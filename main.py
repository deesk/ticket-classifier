from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from ticket_classifier import classify_ticket, TicketResult
from agent import run_agent, AgentResponse


app = FastAPI(
    title="AI Ticket Classifier",
    description="Classifies support tickets using Azure OpenAI",
    version="1.0.0"
)

class TicketRequest(BaseModel):
    ticket: str

@app.post("/classify", response_model=TicketResult)
def classify(request: TicketRequest):
    try:
        result = classify_ticket(request.ticket)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Classification failed")
    
@app.post("/agent", response_model=AgentResponse)
def agent(request: TicketRequest):
    try:
        result = run_agent(request.ticket)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="Agent failed")

@app.get("/health")
def health():
    return {"status": "ok"}