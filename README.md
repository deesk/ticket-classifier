# AI Ticket Classifier

Most support teams waste time manually sorting tickets before anyone even reads them. This project automates that triage layer using Azure OpenAI, returning a category, priority, and draft reply for any incoming support ticket in under two seconds.

## What it does

Takes a raw support ticket as text input and returns three things:

- **Category**: billing, technical, account, or general
- **Priority**: low, medium, high, or urgent — defined by explicit business rules, not model guesswork
- **Draft reply**: a suggested response the support agent can review and send

## Stack

- Python 3.13
- Azure OpenAI (GPT-4.1)
- Pydantic for structured output validation
- FastAPI (week 2, in progress)

## Why structured output matters

Support routing fails when classification is inconsistent. This classifier uses Pydantic `Literal` types to enforce exact field values — if the model returns anything outside the defined categories or priorities, the request fails loudly rather than routing silently to the wrong queue. Temperature is set to 0 to maximise consistency across runs.

## How to run it locally

1. Clone the repo
2. Create a virtual environment and install dependencies

```bash
python -m venv myVenv
myVenv\Scripts\Activate.ps1
pip install openai python-dotenv pydantic
```

3. Create a `.env` file in the project root

```
AZURE_OPENAI_ENDPOINT=your_endpoint_here
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT=your_deployment_name
AZURE_OPENAI_API_VERSION=2024-12-01-preview
```

4. Run the classifier

```bash
python classifier.py
```

## Project structure

```
ticket-classifier/
  classifier.py       # Core logic: prompt, API call, validation
  main.py             # FastAPI wrapper (week 2)
  test_cases.py       # Test suite (week 2)
  .env                # Credentials, never committed
  .gitignore
  README.md
```

## What I learned

LLM output validation is not optional. Without `Literal` type enforcement, a model returning `"priority": "very important"` instead of `"priority": "high"` would pass silently and break downstream routing. Pydantic catches this at the boundary before bad data enters the system.

Priority definitions belong in the prompt, not in code. When the model returned `high` instead of `urgent` for a crashing app, the fix was adding explicit priority definitions to the system prompt — not changing any code. Prompt engineering is the first tool, code changes are the last.

Temperature=0 reduces but does not eliminate output variation. Classification fields stay locked across runs. Draft reply wording varies slightly due to distributed infrastructure variance, which is acceptable for a human-reviewed draft but would require response caching for fully deterministic output.

## Roadmap

- Week 2: FastAPI endpoint, input validation, pytest suite
- Week 3: Agentic layer — model decides if it needs more information before classifying, routes to appropriate department