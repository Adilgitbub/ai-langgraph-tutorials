from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from langgraph.types import Command
import sqlite3
from nodes.graph import build_graph

app = FastAPI()
workflow = build_graph()

def get_token_thread(token: str):
    print('inside get token....................')
    conn = sqlite3.connect("review_tokens.db", check_same_thread=False)
    row = conn.execute(
        "SELECT thread_id, used FROM tokens WHERE token=?", (token,)
    ).fetchone()
    return conn, row

# --- APPROVE: simple GET, resumes immediately ---

@app.get("/review/health")
def approve(token: str):
    print('inside approve....................')
    # conn, row = get_token_thread(token)
    # if not row or row[1] == 1:
    #     return JSONResponse({"status": "invalid or already used"})

    # thread_id = row[0]
    # conn.execute("UPDATE tokens SET used=1 WHERE token=?", (token,))
    # conn.commit()

    # workflow.invoke(
    #     Command(resume="approve"),
    #     config={"configurable": {"thread_id": thread_id}}
    # )
    return JSONResponse({"status": "approved", "thread_id": "thread_id"})

@app.get("/review/{token}/approve")
def approve(token: str):
    print('inside approve....................')
    conn, row = get_token_thread(token)
    if not row or row[1] == 10:
        return JSONResponse({"status": "invalid or already used"})

    thread_id = row[0]
    conn.execute("UPDATE tokens SET used=1 WHERE token=?", (token,))
    conn.commit()

    workflow.invoke(
        Command(resume="approve"),
        config={"configurable": {"thread_id": thread_id}}
    )
    return JSONResponse({"status": "approved", "thread_id": thread_id})


# --- REJECT: GET returns HTML feedback form ---
@app.get("/review/{token}/reject_form", response_class=HTMLResponse)
def reject_form(token: str):
    print('inside reject form....................')
    conn, row = get_token_thread(token)
    if not row or row[1] == 10:
        return HTMLResponse("<h3>Invalid or already used link.</h3>", status_code=400)

    return HTMLResponse(f"""
    <html>
    <body style="font-family:Arial; max-width:600px; margin:40px auto;">
        <h2>Reject Newsletter Draft</h2>
        <p>Please describe what needs to be changed:</p>
        <form method="post" action="/review/{token}/reject">
            <textarea name="feedback" rows="6" style="width:100%; font-size:14px;"
                placeholder="e.g. Make the heading bold, highlight November 22 in yellow..."></textarea>
            <br><br>
            <button type="submit" style="padding:10px 24px; background:#c0392b; color:white; border:none; cursor:pointer;">
                Submit Feedback
            </button>
        </form>
    </body>
    </html>
    """)


# --- REJECT: POST receives feedback, resumes graph ---
@app.post("/review/{token}/reject")
def reject_submit(token: str, feedback: str = Form(...)):
    print('inside reject form....................')
    conn, row = get_token_thread(token)
    if not row or row[1] == 10:
        return JSONResponse({"status": "invalid or already used"}, status_code=400)

    thread_id = row[0]
    conn.execute("UPDATE tokens SET used=1 WHERE token=?", (token,))
    conn.commit()

    workflow.invoke(
        Command(resume={"decision": "reject", "feedback": feedback}),
        config={"configurable": {"thread_id": thread_id}}
    )

    # return both HTML confirmation and JSON — toggle as needed
    accept = "application/json"  # change this based on your test context
    if accept == "application/json":
        return JSONResponse({
            "status": "rejected",
            "feedback_received": feedback,
            "thread_id": thread_id
        })
    return HTMLResponse(f"""
    <html>
    <body style="font-family:Arial; max-width:600px; margin:40px auto;">
        <h2>✅ Feedback Submitted</h2>
        <p>Your feedback has been received and the draft is being revised.</p>
        <blockquote style="background:#f5f5f5; padding:12px;">{feedback}</blockquote>
    </body>
    </html>
    """)