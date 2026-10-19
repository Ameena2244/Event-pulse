# EventPulse — Requirements

## Users
- **Students**: submit feedback for events they attended
- **Organizers**: review sentiment breakdowns and actionable complaints

## User stories

### Feedback submission
- WHEN a student submits feedback for a college event,
  THE agent SHALL ask Strands Decider 2B "what is the sentiment of this response?" and
  "does it need organizer attention?" BEFORE storing the record,
  paired with Amazon Bedrock for the conversational turn.
- WHEN the decider returns low confidence (< 0.55) on sentiment,
  THE agent SHALL flag the response as "unclear" and surface it for manual organizer review.
- WHEN the decider identifies a "serious" severity response,
  THE agent SHALL verdict it as "flag" and include it in the flagged_items list.
- WHEN a student submits feedback for an event id that does not exist,
  THE agent SHALL return an error and ask for the correct event id.

### Organizer summaries
- WHEN an organizer asks for a summary of an event,
  THE agent SHALL return the total response count, sentiment breakdown, needs-attention count,
  and the top attention items.
- WHEN an organizer asks for top complaints,
  THE agent SHALL return all negative or needs-attention responses for that event.
- WHEN no feedback exists for an event,
  THE agent SHALL say so clearly rather than returning empty data silently.

### Listing events
- WHEN a user asks what events are available,
  THE agent SHALL list all events with their id, name, date, organizer, and feedback count.

## Acceptance criteria (EARS)

1. Every call to `submit_feedback` triggers exactly one `Decider.ask` call with the state
   formatted as `"Event: <name>\n\nStudent feedback:\n<text>"`.
2. The decider result is returned in the tool response and collected in `agent.chat()["decisions"]`.
3. Responses with `verdict == "unclear"` appear in `get_feedback_summary` under `unclear_count`.
4. Responses with `verdict == "flag"` appear under `flagged_items`.
5. The agent's LLM runs through `decider_kit.llm.agent_model()` — no direct boto3 calls.
6. `HackathonAgent.chat()` returns `reply`, `decisions`, `model_id`, `latency_ms`, `agent`, `eager`.
