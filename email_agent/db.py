import secrets
import sqlite3

def create_review_token(thread_id: str) -> str:
    token = secrets.token_urlsafe(16)
    conn = sqlite3.connect("review_tokens.db")
    conn.execute("CREATE TABLE IF NOT EXISTS tokens (token TEXT PRIMARY KEY, thread_id TEXT, used INTEGER DEFAULT 0)")
    conn.execute("INSERT INTO tokens VALUES (?, ?, 0)", (token, thread_id))
    conn.commit()
    return token

def get_checkpointer():
    conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
    from langgraph.checkpoint.sqlite import SqliteSaver
    return SqliteSaver(conn)