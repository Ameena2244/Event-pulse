# EventPulse — College Event Feedback Analyzer

## One-line pitch
An AI agent that collects student feedback on college events, classifies each response as
positive, negative, or neutral using Strands Decider 2B, and surfaces recurring themes to help
organizers improve future events.

## Who it is for
College event organizers (student councils, fest committees, department heads) who want to
understand what students liked and disliked — without reading hundreds of raw responses.

## Features
1. **Submit feedback** — students submit feedback for any event in plain language
2. **Sentiment classification** — Strands Decider 2B classifies each response (positive /
   negative / neutral) and flags whether it needs organizer attention
3. **Theme extraction** — the agent groups recurring complaints and suggestions per event
4. **Event summary** — organizers ask for a summary: sentiment breakdown + top themes
5. **Top complaints** — quickly surface the most common negatives across any event

## The decision (Strands Decider 2B)
**Pattern:** `#policy`

Before storing or acting on a feedback response, Strands Decider 2B reads the text and decides:
- `sentiment`: is the feedback positive, negative, or neutral?
- `needs_attention`: does this response contain something the organizer should act on (a
  complaint, a safety concern, a specific broken item, a recurring suggestion)?
- `severity`: how serious is the issue — none, minor, or serious?

This replaces a slow LLM classification call with a single forward pass at a fraction of the
cost and latency, while returning calibrated probabilities the code can branch on.

Low-confidence cases (< 0.55) are flagged as "unclear" and surfaced separately so organizers
can review them manually rather than act on a guess.

## The data
Synthetic event feedback in `agent/data/feedback.json` — covers a tech fest, a hackathon, and
a cultural night, with a mix of positive, negative, and ambiguous responses.

## Amazon Bedrock
The agent's LLM (conversation, theme extraction, summary generation) runs on Amazon Bedrock
(Amazon Nova Pro by default). Strands Decider 2B handles the sentiment/policy classification.
The deployed agent runs on Amazon Bedrock AgentCore Runtime.

## Built with the AWS User Group Madurai Strands Decider hackathon kit
