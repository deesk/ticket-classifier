import os
import json
from pathlib import Path
from openai import AzureOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Literal
from ticket_classifier import classify_ticket, TicketResult

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

class AgentResponse(BaseModel):
    action: Literal["classified", "rejected", "needs_info"]
    reason: str | None = None
    question: str | None = None
    result: TicketResult | None = None

def check_intent(ticket: str) -> dict:
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": """You are a support ticket gatekeeper.
                Analyse the input and respond only with raw JSON, no markdown, no backticks.
                Use this exact format: {"intent": "", "reason": ""}
                Intent values:
                - valid: this is a legitimate customer support issue
                - invalid: this is not a support ticket (greeting, question, nonsense, off-topic)
                - needs_info: this is support related but lacks enough detail to classify"""
            },
            {
                "role": "user",
                "content": ticket
            }
        ]
    )
    return json.loads(response.choices[0].message.content)

def run_agent(ticket: str) -> AgentResponse:
    if not ticket.strip():
        return AgentResponse(
            action="rejected",
            reason="Ticket cannot be empty. Please describe your issue."
        )

    intent = check_intent(ticket)

    if intent["intent"] == "invalid":
        return AgentResponse(
            action="rejected",
            reason=intent["reason"]
        )

    if intent["intent"] == "needs_info":
        return AgentResponse(
            action="needs_info",
            question="Could you please provide more details about your issue?"
        )

    result = classify_ticket(ticket)
    return AgentResponse(
        action="classified",
        result=result
    )