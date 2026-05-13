# AI Ticket Classifier

Most support teams waste time manually sorting tickets before anyone even reads them. This project automates that triage layer using Azure OpenAI, returning a category, priority, and draft reply for any incoming support ticket in under two seconds.

## What it does

Takes a raw support ticket as text input and returns three things:

- **Category**: billing, technical, account, or general
- **Priority**: low, medium, high, or urgent — defined by explicit business rules, not model guesswork
- **Draft reply**: a suggested response the support agent can review and send

The system has two layers. The classifier handles valid tickets. The agent decides whether a ticket is worth classifying at all.

## Stack

- Python 3.13
- Azure OpenAI (GPT-4.1)
- Pydantic for structured output validation
- FastAPI for the API layer
- pytest for the test suite

## Architecture

```
ticket-classifier/
  ticket_classifier.py  # Core logic: prompt, API call, Pydantic validation
  agent.py              # Agentic layer: intent detection, routing, retry logic
  main.py               # FastAPI: /classify and /agent endpoints
  test_cases.py         # 11 tests covering classifier and agent behaviour
  requirements.txt
  .env                  # Credentials, never committed
  .gitignore
  README.md
```

### Two endpoints, one deliberate reason

`POST /classify` accepts pre-validated input and runs classification directly. It exists for internal use or upstream systems that already guarantee ticket validity.

`POST /agent` is the recommended public endpoint. It runs an intent check before classification, handles invalid input gracefully, and asks for more information when the ticket is too vague to classify. Any untrusted input should go through this endpoint.

This separation follows the single responsibility principle. The classifier classifies. The agent decides. Each component is independently testable.

### Agent decision flow

```
Input received
    │
    ├── Empty? → rejected (no API call made)
    │
    ├── Invalid? (greeting, off-topic, nonsense) → rejected with reason
    │
    ├── Too vague? → needs_info with follow-up question
    │
    └── Valid? → classify → return category, priority, draft reply
```

### Response shape

The agent always returns the same structure regardless of outcome. The caller checks `action` first, then reads the relevant field.

```json
// Valid ticket
{
  "action": "classified",
  "result": { "category": "billing", "priority": "high", "draft_reply": "..." }
}

// Invalid input
{
  "action": "rejected",
  "reason": "This is a greeting, not a support ticket."
}

// Insufficient detail
{
  "action": "needs_info",
  "question": "Could you please provide more details about your issue?"
}
```

## How to run it locally

1. Clone the repo
2. Create a virtual environment and install dependencies

```bash
python -m venv myVenv
myVenv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with these four variables:

```
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

4. Start the API

```bash
uvicorn main:app --reload
```

5. Open the interactive docs at `http://127.0.0.1:8000/docs`

6. Run the test suite

```bash
pytest test_cases.py -v
```

## Findings

Four behaviours emerged during testing that are not obvious from documentation alone. Full analysis in [docs/findings.md](docs/findings.md).

- Draft reply language is non-deterministic by default even when classification fields are consistent
- Temperature=0 reduces variation but does not eliminate it due to distributed infrastructure
- Without intent detection, the classifier processes all input and produces contextually irrelevant output
- LLM JSON parsing failures require retry logic and safe fallbacks, not fixes
