# Newsletter Automation Project — Summary

## What the project is
Automating a monthly newsletter publishing process currently done manually. A user (internal team) provides email content, optional reference screenshot, optional PNG image — the system generates the HTML email, reviews it, sends a test to a human reviewer, and on approval publishes it via an existing **Java microservice** (which handles actual email sending).

---

## Solution Architecture Decided
- **Python + LangGraph** = intelligence layer (agents, nodes, workflow)
- **Java microservice** = system of record for publishing (called as a tool via HTTP)
- **Local Docker models** = fallback (llama3.2:3B for text, gemma4:E4B for vision)
- **Google Gemini API (free tier)** = primary vision model (gemini-3.6-flash)
- **SQLite** = checkpointer (persistence/resume) + token store
- **FastAPI** = approve/reject server for human review
- **Streamlit** = frontend (file upload + user input)

---

## 8-Node Graph Design

| Node | Model/Tool | Status |
|---|---|---|
| `intake` | gemma4/Gemini (vision) | ✅ Done |
| `compose_html` | llama3.2:3B + Gemini styling | ✅ Done |
| `auto_review` | Gemini (vision) | ✅ Done |
| `optimize` | Gemini/llama (human feedback priority) | ✅ Done |
| `test_send_human` | Java API tool call | ✅ Done |
| `human_review` | HITL interrupt() | ✅ Done |
| `publish` | Java API tool call | ⏳ Stub only |
| `confirm_log` | Plain Python logging | ⏳ Stub only |
| `manual_handling` | Notify internal team | ⏳ Stub only |

---

## Key Design Decisions Locked
- Snap is optional — never ask user if missing
- BCC/content missing → ask user (intake clarification)
- `email_content` = original plain text (never overwritten)
- `html_body` = generated HTML (compose/optimize write here)
- Human feedback takes priority over auto-review feedback in optimize
- `iteration` resets to 0 on human reject → optimize
- `human_reject_iteration` capped at 2 → then manual_handling
- Approve/Reject links embedded in test email body
- Reject link → HTML form for feedback → POST resumes graph
- Token-based security (one-time use, stored in `review_tokens.db`)

---

## File Structure (current)
```
email_agent/
  nodes/
    __init__.py
    intake.py
    compose.py
    review.py
    human.py
    publish.py
  graph.py
  models.py
  schemas.py
  state.py
  utils.py
  db.py
  main.py
  hanlde-server.py
checkpoints.db
review_tokens.db
```

---

## Pending to Implement
1. **`publish` node** — call Java API with final payload (real BCC list, not reviewer)
2. **`confirm_log` node** — log outcome, thread_id, timestamp, publish status
3. **`manual_handling` node** — notify internal team when cap exceeded
4. **Streamlit frontend** — file upload (snap + PNG), text input, bcc input, trigger workflow
5. **End-to-end test** — full run from Streamlit input → publish via Java API
6. **Wire `human_reject_iteration` reset node** into graph edges correctly
7. **`.env` values finalised** — `JAVA_EMAIL_API_URL`, `REVIEWER_EMAIL`, `FASTAPI_BASE_URL`, `GOOGLE_MODEL`, `GOOGLE_API_KEY`