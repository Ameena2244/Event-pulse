"""EventPulse tools: college event feedback storage and retrieval.

Data lives in agent/data/feedback.json (synthetic). The FeedbackPolicyCheck decision is called
here before storing a response; its result is returned so agent.py can collect it in `decisions`.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from strands import tool

from decider_kit import Decider

from .decision import FeedbackPolicyCheck

# --------------------------------------------------------------------------- data helpers

_DATA_PATH = Path(__file__).parent / "data" / "feedback.json"

def _load() -> dict[str, Any]:
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))

# In-memory store: keyed by feedback id. Pre-loaded from the file, new submissions appended.
_store: dict[str, dict[str, Any]] = {}
_events: dict[str, dict[str, Any]] = {}
_classifier: FeedbackPolicyCheck | None = None


def _init():
    global _store, _events, _classifier
    if _classifier is not None:
        return
    data = _load()
    _events = {e["id"]: e for e in data["events"]}
    # Load existing feedback without classifying (keep startup fast)
    for fb in data["feedback"]:
        _store[fb["id"]] = {**fb, "classification": None}
    _classifier = FeedbackPolicyCheck(Decider())


def _next_id() -> str:
    existing = [k for k in _store if k.startswith("F")]
    nums = [int(k[1:]) for k in existing if k[1:].isdigit()]
    return f"F{(max(nums) + 1) if nums else 1:03d}"


# --------------------------------------------------------------------------- tools

@tool
def list_events() -> dict:
    """List all college events that have feedback available."""
    _init()
    return {
        "events": [
            {
                "id": eid,
                "name": ev["name"],
                "date": ev["date"],
                "organizer": ev["organizer"],
                "feedback_count": sum(1 for f in _store.values() if f["event_id"] == eid),
            }
            for eid, ev in _events.items()
        ]
    }


@tool
def submit_feedback(event_id: str, feedback_text: str) -> dict:
    """Submit a student feedback response for a college event; classifies sentiment with Strands Decider 2B."""
    _init()
    event = _events.get(event_id.strip().upper())
    if not event:
        return {"error": f"no event with id {event_id}"}
    if not feedback_text or len(feedback_text.strip()) < 5:
        return {"error": "feedback text is too short"}

    classification = _classifier.classify(event["name"], feedback_text.strip())
    fid = _next_id()
    record = {
        "id": fid,
        "event_id": event_id.upper(),
        "text": feedback_text.strip(),
        "classification": classification,
    }
    _store[fid] = record
    return {
        "submitted": True,
        "feedback_id": fid,
        "event": event["name"],
        "sentiment": classification["sentiment"],
        "needs_attention": classification["needs_attention"],
        "verdict": classification["verdict"],
        "decider_ms": classification["decider_ms"],
    }


@tool
def get_feedback_summary(event_id: str) -> dict:
    """Get a sentiment breakdown and top themes for a college event."""
    _init()
    event = _events.get(event_id.strip().upper())
    if not event:
        return {"error": f"no event with id {event_id}"}

    responses = [f for f in _store.values() if f["event_id"] == event_id.upper()]
    if not responses:
        return {"event": event["name"], "message": "no feedback yet"}

    classified = [f for f in responses if f.get("classification")]
    unclassified_count = len(responses) - len(classified)

    sentiments = Counter(f["classification"]["sentiment"] for f in classified)
    attention_items = [f["text"] for f in classified if f["classification"].get("needs_attention")]
    flagged = [f["text"] for f in classified if f["classification"].get("verdict") == "flag"]
    unclear = [f["text"] for f in classified if f["classification"].get("verdict") == "unclear"]

    return {
        "event": event["name"],
        "total_responses": len(responses),
        "classified": len(classified),
        "unclassified": unclassified_count,
        "sentiment_breakdown": dict(sentiments),
        "needs_attention_count": len(attention_items),
        "flagged_count": len(flagged),
        "unclear_count": len(unclear),
        "attention_items": attention_items[:10],
        "flagged_items": flagged[:5],
    }


@tool
def get_top_complaints(event_id: str) -> dict:
    """Get the top complaints and actionable suggestions from negative or flagged feedback for an event."""
    _init()
    event = _events.get(event_id.strip().upper())
    if not event:
        return {"error": f"no event with id {event_id}"}

    responses = [f for f in _store.values() if f["event_id"] == event_id.upper()]
    complaints = [
        f["text"] for f in responses
        if f.get("classification") and (
            f["classification"]["sentiment"] == "negative"
            or f["classification"].get("needs_attention")
        )
    ]
    if not complaints:
        return {"event": event["name"], "message": "no complaints or actionable feedback found"}

    return {
        "event": event["name"],
        "complaint_count": len(complaints),
        "complaints": complaints,
    }


TOOLS = [list_events, submit_feedback, get_feedback_summary, get_top_complaints]
