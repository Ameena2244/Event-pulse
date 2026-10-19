"""REUSABLE DECISION PATTERN: event-feedback policy classifier  (#policy)

What it does
    Before a student feedback response is stored, Strands Decider 2B reads the text and
    classifies it:
    - Is it positive, negative, or neutral?
    - Does it contain something the organizer should act on?
    - How serious is the issue?
    This replaces a slow LLM classification call with one forward pass (~1-2 s on the hosted
    API), returning calibrated probabilities the code can branch on. Low-confidence responses
    are flagged for manual organizer review instead of being silently miscategorised.

Typed questions and options
    `sentiment` (choice): positive | negative | neutral
        positive — praise, satisfaction, enjoyment
        negative — complaints, disappointment, problems
        neutral  — factual observations, neither praise nor complaint

    `needs_attention` (noul): should the organizer act on this?
        true  — contains a complaint, safety concern, specific broken item, or actionable suggestion
        false — general opinion or praise; no action required

    `severity` (score): how serious is the issue? ["none", "minor", "serious"]

Wiring
    `FeedbackPolicyCheck` is called in tools.py before a feedback record is stored.
    It wraps `decider_kit.patterns.policy.PolicyCheck` with event-feedback-specific questions.
    Results are returned in the tool response so agent.py can collect them in `decisions`.

How to reuse it
    Copy this file and replace the SENTIMENT_CATEGORIES and FEEDBACK_POLICY strings with your
    own taxonomy. The thresholds live in FeedbackPolicyCheck (attention_at, serious_at) and
    can be tuned per deployment. The state layout must match your eval_cases.jsonl exactly.
"""

from __future__ import annotations

from typing import Any

from decider_kit import Decider

PATTERN_TAG = "#policy"

FEEDBACK_POLICY = (
    "College event feedback that needs organizer attention: complaints about logistics, "
    "safety concerns, broken equipment, poor audio/video, lack of organisation, "
    "specific actionable suggestions for improvement, or any issue that affected "
    "the student experience negatively and could be fixed next time."
)

SENTIMENT_CATEGORIES = {
    "positive": "praise, satisfaction, enjoyment, or compliments about the event",
    "negative": "complaints, disappointment, problems, or dissatisfaction with the event",
    "neutral": "factual observations, mixed opinions, or comments that are neither clearly positive nor negative",
}

QUESTIONS = {
    "sentiment": Decider.choice(
        "What is the overall sentiment of this feedback response?",
        SENTIMENT_CATEGORIES,
    ),
    "needs_attention": Decider.noul(
        "Does this feedback contain something the event organizer should act on?",
        {
            "true": (
                "contains a specific complaint, safety concern, broken equipment report, "
                "poor logistics observation, or an actionable suggestion the organizer could fix"
            ),
            "false": (
                "general praise, a vague positive or negative opinion, or a comment "
                "that does not point to a specific actionable issue"
            ),
        },
    ),
    "severity": Decider.score(
        "How serious is the issue raised in this feedback?",
        ["none", "minor", "serious"],
    ),
}


def build_state(event_name: str, feedback_text: str) -> str:
    """Build the state text the decider sees. Must match eval_cases.jsonl exactly."""
    return (
        f"Event: {event_name}\n\n"
        f"Student feedback:\n{feedback_text}"
    )


class FeedbackPolicyCheck:
    """Classifies a single feedback response with Strands Decider 2B."""

    def __init__(
        self,
        decider: Decider,
        attention_at: float = 0.55,
        serious_at: float = 0.65,
        low_confidence_threshold: float = 0.55,
    ):
        self.decider = decider
        self.attention_at = attention_at
        self.serious_at = serious_at
        self.low_conf = low_confidence_threshold
        self.log: list[dict[str, Any]] = []

    def classify(self, event_name: str, feedback_text: str) -> dict[str, Any]:
        """Classify one feedback response. Returns a record suitable for agent decisions."""
        state = build_state(event_name, feedback_text)
        a = self.decider.ask(state, QUESTIONS)

        sentiment = a["sentiment"].label or "neutral"
        sentiment_conf = round(a["sentiment"].confidence or 0.0, 3)
        needs_attention = (a["needs_attention"].p_yes or 0.0) >= self.attention_at
        severity = a["severity"].label or "none"
        p_attention = round(a["needs_attention"].p_yes or 0.0, 3)
        low_confidence = sentiment_conf < self.low_conf

        # Escalate to organizer review if confident it's serious
        serious = severity == "serious" and (a["severity"].confidence or 0.0) >= 0.5

        if low_confidence:
            verdict = "unclear"
        elif serious or (needs_attention and sentiment == "negative"):
            verdict = "flag"
        elif needs_attention:
            verdict = "review"
        else:
            verdict = "store"

        rec = {
            "pattern": PATTERN_TAG,
            "sentiment": sentiment,
            "sentiment_confidence": sentiment_conf,
            "needs_attention": needs_attention,
            "p_attention": p_attention,
            "severity": severity,
            "verdict": verdict,
            "low_confidence": low_confidence,
            "decider_ms": round(self.decider.last_latency_ms or 0),
        }
        self.log.append(rec)
        return rec
