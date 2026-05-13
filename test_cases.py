import pytest
from ticket_classifier import classify_ticket
from agent import run_agent

# classifier tests
def test_billing_ticket():
    result = classify_ticket("I was charged twice this month")
    assert result.category == "billing"
    assert result.priority in ["high", "urgent"]

def test_account_ticket():
    result = classify_ticket("I cannot log into my account")
    assert result.category == "account"
    assert result.priority in ["high", "urgent"]

def test_general_ticket():
    result = classify_ticket("How do I export my data?")
    assert result.category == "general"
    assert result.priority in ["low", "medium"]

def test_technical_ticket():
    result = classify_ticket("The app crashes every time I open it")
    assert result.category == "technical"
    assert result.priority == "urgent"

def test_empty_ticket():
    with pytest.raises(ValueError) as exc_info:
        classify_ticket("")
    assert "empty" in str(exc_info.value).lower()

def test_whitespace_only():
    with pytest.raises(ValueError):
        classify_ticket("   ")

def test_conversational_input():
    result = classify_ticket("how are you")
    assert result.category == "general"
    assert result.priority == "low"

# agent tests
def test_agent_valid_ticket():
    response = run_agent("I was charged twice this month")
    assert response.action == "classified"
    assert response.result is not None

def test_agent_invalid_ticket():
    response = run_agent("what is the capital of Nepal")
    assert response.action == "rejected"
    assert response.reason is not None

def test_agent_needs_info():
    response = run_agent("my app")
    assert response.action == "needs_info"
    assert response.question is not None

def test_agent_empty_ticket():
    response = run_agent("")
    assert response.action == "rejected"