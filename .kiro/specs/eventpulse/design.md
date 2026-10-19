# EventPulse — Design

## State text layout (must match eval_cases.jsonl)

```
Event: <event name>

Student feedback:
<feedback text>
```

## Typed questions (QUESTIONS in decision.py)

| Key | Type | Options / levels |
|-----|------|-----------------|
| `sentiment` | choice | positive, negative, neutral |
| `needs_attention` | noul | true = actionable issue, false = general opinion |
| `severity` | score | none, minor, serious |

## Thresholds and actions (FeedbackPolicyCheck)

| Condition | Verdict |
|-----------|---------|
| `sentiment_confidence < 0.55` | `unclear` — surface for manual review |
| `severity == "serious"` AND `severity_confidence >= 0.5` | `flag` — escalate to organizer |
| `needs_attention AND sentiment == "negative"` | `flag` |
| `needs_attention` (other) | `review` |
| everything else | `store` |

## Decision seam

`FeedbackPolicyCheck.classify()` is called inside `submit_feedback` (tools.py) before
the record is written to the in-memory store. It returns a `classification` dict that is
stored with the record and returned in the tool result. `agent.py` collects from
`_classifier.log` to populate `decisions` in the `chat()` return.

## Tools

| Tool | Purpose |
|------|---------|
| `list_events` | lists events with feedback counts |
| `submit_feedback(event_id, feedback_text)` | classifies and stores one response |
| `get_feedback_summary(event_id)` | sentiment breakdown + attention items |
| `get_top_complaints(event_id)` | negative + needs-attention responses only |

## Eval-case plan (26 cases)

- 13 tune / 13 test
- Every sentiment branch covered: positive (8), negative (14), neutral (3) — matches real distribution
- Needs-attention: true (14 cases), false (12 cases)
- Near-misses: a positive with a suggestion (needs_attention=true), a neutral with no issues,
  a complaint that is mild (minor severity)
- All state strings use the exact layout above
