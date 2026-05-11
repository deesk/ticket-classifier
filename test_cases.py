import pytest
from classifier import classify_ticket

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

def test_whitespace_only():
    with pytest.raises(ValueError):
        classify_ticket("   ")

def test_conversational_input():
    result = classify_ticket("how are you")
    assert result.category == "general"
    assert result.priority == "low"

def test_empty_ticket():
    with pytest.raises(ValueError) as exc_info:
        classify_ticket("")
    assert "empty" in str(exc_info.value).lower()