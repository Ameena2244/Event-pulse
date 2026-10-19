"""EventPulse: college event feedback analyzer agent.

Collects student feedback on college events, classifies each response as positive, negative,
or neutral using Strands Decider 2B (#policy pattern), and surfaces recurring themes to help
organizers improve future events. The LLM runs on Amazon Bedrock (or the ugmdu cloud locally).

    from agent.agent import HackathonAgent
    out = HackathonAgent().chat("Summarize the feedback for TechFest 2026.")
    out["reply"], out["decisions"]
"""

from __future__ import annotations

import time
from typing import Any

from strands import Agent

from decider_kit.llm import agent_model, default_model_id, strip_thinking

from . import tools as _tools_mod
from .tools import TOOLS, _init

NAME = "EventPulse — College Event Feedback Analyzer"

SYSTEM_PROMPT = """You are EventPulse, an AI assistant for college event organizers and students.

You help with two things:
1. Students submit feedback for college events — you classify each response using Strands Decider 2B to
   detect sentiment (positive/negative/neutral) and flag responses that need organizer attention.
2. Organizers ask for summaries — you report the sentiment breakdown, top complaints, and actionable
   suggestions for any event.

Available events: TechFest 2026 (EVT001), HackMadurai 2026 (EVT002), Cultural Night 2026 (EVT003).

Be concise and helpful. When summarizing feedback, group themes clearly. When a student submits
feedback, confirm what the decider decided (sentiment + whether it was flagged). If the decision
was low-confidence (unclear), say so honestly.

Built with the AWS User Group Madurai Strands Decider hackathon kit."""


class HackathonAgent:
    """One Strands agent per session, with the feedback policy decision wired in via tools."""

    def __init__(self, decider=None, model_id: str | None = None, eager: bool | None = None):
        _init()  # ensure data and classifier are loaded
        self.model_id = model_id or default_model_id()
        self.sessions: dict[str, Agent] = {}
        # `eager` kept for interface compatibility; not used (no destructive tools here)

    def _session(self, session_id: str) -> Agent:
        if session_id not in self.sessions:
            self.sessions[session_id] = Agent(
                model=agent_model(self.model_id),
                system_prompt=SYSTEM_PROMPT,
                tools=TOOLS,
                callback_handler=None,
            )
        return self.sessions[session_id]

    def chat(self, message: str, session_id: str = "default", images: list[Any] | None = None) -> dict[str, Any]:
        """Send a message and return reply + decisions from the policy classifier."""
        agent = self._session(session_id)
        before = len(_tools_mod._classifier.log) if _tools_mod._classifier else 0
        t0 = time.perf_counter()
        result = agent(message)
        reply = strip_thinking(str(result))
        after_log = _tools_mod._classifier.log[before:] if _tools_mod._classifier else []
        return {
            "reply": reply,
            "decisions": after_log,
            "model_id": self.model_id,
            "latency_ms": round((time.perf_counter() - t0) * 1000),
            "agent": NAME,
            "eager": False,
        }


if __name__ == "__main__":
    import json
    import sys

    a = HackathonAgent()
    msgs = sys.argv[1:] or [
        "What events have feedback?",
        "Submit feedback for EVT001: The microphone kept cutting out during the keynote!",
        "Summarize the feedback for TechFest 2026.",
    ]
    for msg in msgs:
        print(json.dumps(a.chat(msg), indent=2, default=str))
