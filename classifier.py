import os
import json
from pathlib import Path
from typing import Literal
from openai import AzureOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError

load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION")
)

class TicketResult(BaseModel):
    category: Literal["billing", "technical", "account", "general"]
    priority: Literal["low", "medium", "high", "urgent"]
    draft_reply: str

def classify_ticket(ticket: str) -> TicketResult:
    if not ticket.strip():
        raise ValueError("Ticket cannot be empty. Please describe your issue.")
    
    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": """You are a customer support ticket classifier. 
                Classify the ticket and respond only with raw JSON, no markdown, no backticks. 
                Use this exact format: {"category": "", "priority": "", "draft_reply": ""}.
                Categories: billing, technical, account, general.
                Priorities: 
                - urgent: system down, data loss, security breach, app completely unusable
                - high: major feature broken, billing error, cannot access account
                - medium: minor feature issue, general questions with business impact
                - low: how-to questions, feature requests, general inquiries"""
            },
            {
                "role": "user",
                "content": ticket
            }
        ]
    )

    raw = response.choices[0].message.content

    try:
        data = json.loads(raw)
        result = TicketResult(**data)
        return result
    except json.JSONDecodeError:
        print("ERROR: Model returned invalid JSON")
        print("Raw output:", raw)
        raise
    except ValidationError as e:
        print("ERROR: JSON missing required fields")
        print(e)
        raise

ticket = "I was charged twice this month and need a refund immediately."
result = classify_ticket(ticket)

print("Category:", result.category)
print("Priority:", result.priority)
print("Draft reply:", result.draft_reply)

test_tickets = [
    "I was charged twice this month",
    "I cannot log into my account",
    "How do I export my data?",
    "The app crashes every time I open it",
    ""
]

for ticket in test_tickets:
    try:
        result = classify_ticket(ticket)
        print(f"Ticket: {ticket[:40]}")
        print(f"Category: {result.category} | Priority: {result.priority}")
        print()
    except ValueError as e:
        print(f"Ticket: '{ticket}' -> REJECTED: {e}")
        print()
    except Exception as e:
        print(f"Ticket: '{ticket}' -> ERROR: {e}")
        print()