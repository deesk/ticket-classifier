# Findings: AI Ticket Classifier

This document records four behaviours observed during the build and testing of this system. Each finding includes what happened, why it happened, how it was addressed, and what it means for building AI systems in production.

---

## Finding 1: Draft reply language is non-deterministic by default

**What happened**

The same billing ticket was sent twice at default temperature. Two different draft replies came back:

- Run 1: "process a refund if necessary" — conditional, uncommitted
- Run 2: "will begin the refund process right away" — immediate commitment

Same ticket. Same prompt. Two different promises to the customer. One says maybe. The other says now.

**Why it happened**

At default temperature (around 0.7), the model samples from a probability distribution of possible next tokens. It does not pick the single most likely word every time. It picks from a range of plausible words weighted by probability. This produces natural-sounding variation but also inconsistent language on consequential statements.

**How it was addressed**

Two changes were made. First, temperature was set to 0 to push the model toward its most probable output at each step. Second, the system prompt was updated to include explicit constraints on draft reply language, avoiding open-ended commitments.

**What this means for production**

Draft replies should never be sent automatically without human review. The model does not know your refund policy, your SLA commitments, or your legal obligations. It generates plausible language based on training data. A human must review before any reply reaches a customer.

---

## Finding 2: Temperature=0 reduces variation but does not eliminate it

**What happened**

After setting temperature=0, classification fields (category, priority) stayed locked solid across every run. Draft reply wording still varied slightly between runs, though meaning and commitment level stayed consistent.

**Why it happened**

Temperature=0 does not produce a single deterministic output. Azure OpenAI runs on distributed infrastructure. Different servers handle different requests. Floating point arithmetic at scale introduces microscopic differences that compound into occasional different word choices even at temperature=0.

**How it was addressed**

For classification fields this is not a problem. Billing is always billing. Urgent is always urgent. For draft replies the variation is acceptable because a human reviews before sending. Full determinism would require response caching: storing the result for a known input and returning that stored result instead of calling the model again.

**What this means for production**

Do not assume temperature=0 means identical output every time. It means consistent output most of the time. If your system requires guaranteed identical output for the same input, build a caching layer. If human review exists downstream, temperature=0 is sufficient.

---

## Finding 3: Without intent detection, the classifier processes all input and produces contextually irrelevant output

**What happened**

The input "what is the capital of Nepal" was sent to the `/classify` endpoint. It returned:

```json
{
  "category": "general",
  "priority": "low",
  "draft_reply": "The capital of Nepal is Kathmandu. Let us know if you have any other questions."
}
```

The model answered a geography question as a customer support draft reply. The answer was factually correct. The model did not fail. The system design did.

**Why it happened**

The classifier had one instruction: classify the ticket and return a draft reply. It had no instruction for what to do when the input is not a support ticket. With no guardrail, it applied its only job to everything that arrived. The draft reply field had to be filled with something, so the model filled it with the most relevant thing it could associate with the input.

This is not hallucination. Hallucination is when a model states something false as true. This model stated something true. The problem was architectural: no layer existed to decide whether classification should run at all.

**How it was addressed**

The agentic intent check was added as a gate before classification. A separate system prompt asks "is this a legitimate support ticket?" before the classifier runs. Invalid input is rejected immediately. The classifier and draft reply are never invoked for non-support input.

**What this means for production**

Any public facing AI system needs an intent detection layer before the main task runs. Users will send anything. Greetings, random questions, test inputs, gibberish. Without a guardrail every input gets processed and produces output that looks legitimate but is contextually wrong. The agent layer is not a nice-to-have feature. It is a necessary boundary for untrusted input.

---

## Finding 4: LLM JSON parsing failures require retry logic and safe fallbacks

**What happened**

During the pytest run, `test_agent_valid_ticket` failed with:

```
json.decoder.JSONDecodeError: Unterminated string starting at: line 1 column 31
```

The model returned a response that started as valid JSON but was cut off mid-string. Python could not parse it and the request crashed.

**Why it happened**

The model generates text token by token. Occasionally a response is truncated due to infrastructure issues: a timeout, a network interruption, or an internal Azure service hiccup. The result is partial JSON that looks valid at a glance but fails to parse.

The original code assumed the model always returned valid JSON and called `json.loads()` directly with no error handling. One bad response crashed the entire request.

**How it was addressed**

Retry logic was added to `check_intent` in `agent.py`. The API call runs inside a loop with two attempts. If `json.loads()` raises a `JSONDecodeError` on the first attempt, the model is called again with the same input. If the second attempt also fails, a safe fallback is returned instead of crashing:

```python
return {"intent": "valid", "reason": "fallback"}
```

The fallback treats the ticket as valid and passes it to the classifier. This is the safest default: better to over-classify a ticket and have a human review it than to silently reject a real customer issue because of an infrastructure glitch.

**What this means for production**

This does not fix the root cause. The model will still occasionally return malformed JSON. That cannot be controlled at the prompt level. What changes is the system's response to that failure. Defensive programming assumes failure is possible and builds paths that survive it. Never call `json.loads()` on LLM output without a try-except. Always have a retry strategy. Always have a fallback that keeps the system running.

---

## What this project taught me

Prompt engineering is the first tool, code changes are the last. When the classifier returned high instead of urgent for a crashing app, the fix was adding explicit priority definitions to the system prompt, not changing any code. The prompt is the logic layer for LLM behaviour. Reaching for code before exhausting prompt changes is a sign of misunderstanding where the actual control surface is.

Structured output validation is not optional. Without Pydantic Literal types, a model returning "priority": "very important" instead of "priority": "high" would pass silently and break downstream routing. Validation at the boundary is the difference between a system that fails loudly and one that fails quietly and incorrectly.

The agentic loop is a decision layer, not a complexity layer. The agent in this project makes three decisions before acting: is this a valid ticket, does it have enough information, and only then does it classify. That decision-making pattern before action is the core primitive of every agent I will build going forward. Complexity comes from the number of decisions and tools available, not from the loop itself.

LLM systems require defensive programming by default. The model is a probabilistic system running on distributed infrastructure. It will occasionally return unexpected output. Every production AI system must assume this and build accordingly: validate output, retry on failure, fall back safely, and never let a bad model response crash the system.