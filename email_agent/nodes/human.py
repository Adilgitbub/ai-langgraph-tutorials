from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt
from state import EmailState
from db import create_review_token

def test_send_human(state: EmailState, config: RunnableConfig):
    thread_id = config["configurable"]["thread_id"]
    token = create_review_token(thread_id)
    # TODO: include approve/reject links built from token in email body
    print(f"use this token for approve and reject {token}")
    return {}

def human_review(state: EmailState):
    print("Awaiting human decision...")
    decision = interrupt({
        "subject": state["subject"],
        "message": "Awaiting approve/reject decision"
    })
    print(f"Decision received: {decision}")
    return {"human_decision": decision}

def route_decision(state: EmailState):
    return "approve" if state["human_decision"] == "approve" else "reject"