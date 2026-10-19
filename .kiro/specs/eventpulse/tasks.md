# EventPulse — Tasks

- [x] Write AGENT.md (pitch, features, decision, data, Bedrock)
- [x] Write decision.py (PATTERN_TAG, QUESTIONS, FeedbackPolicyCheck, state layout)
- [x] Write agent/data/feedback.json (synthetic: TechFest, HackMadurai, Cultural Night)
- [x] Write tools.py (list_events, submit_feedback, get_feedback_summary, get_top_complaints)
- [x] Write agent.py (HackathonAgent, SYSTEM_PROMPT, chat() contract)
- [x] Write eval_cases.jsonl (26 cases, tune + test split)
- [x] Write demo_script.yaml (4 turns, neutral narration)
- [x] Write features.yaml (memory: false, gateway: false)
- [x] Write spec (requirements.md, design.md, tasks.md)
- [x] Run `.\kit.cmd test` — 34/34 passed
- [x] Run `.\kit.cmd run` — agent replies correctly
- [ ] Run `.\kit.cmd bench --split tune` — tune questions if needed
- [ ] Run `.\kit.cmd bench --split test` — record final numbers
- [ ] Run `.\kit.cmd demo-bg` — review the live app
- [ ] Deploy to AWS (`.\kit.cmd deploy`)
- [ ] Record video (`.\kit.cmd video --target agentcore`)
- [ ] Write article (`.\kit.cmd article`)
- [ ] Publish (`.\kit.cmd publish <repo>`)
