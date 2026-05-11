from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from classifier import classify_ticket, TicketResult

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

@app.get("/health")
def health():
    return {"status": "ok"}