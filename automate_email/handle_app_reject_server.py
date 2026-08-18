from fastapi import FastAPI
from langgraph.types import Command
import sqlite3
from  automate_announcement import workflow

app = FastAPI()


@app.get("/review/{token}/{decision}")
def handle_review(token: str, decision: str):
    conn = sqlite3.connect("review_tokens.db", check_same_thread=False)
    row = conn.execute("SELECT thread_id, used FROM tokens WHERE token=?", (token,)).fetchone()
    if not row or row[1] == 1:
        return {"status": "invalid or already used"}

    thread_id, _ = row
    conn.execute("UPDATE tokens SET used=1 WHERE token=?", (token,))
    conn.commit()
    print(f'Thread id fetched from DB ................{thread_id}')

    workflow.invoke(Command(resume=decision), config={"configurable": {"thread_id": thread_id}})
    return {"status": f"Recorded: {decision}"}