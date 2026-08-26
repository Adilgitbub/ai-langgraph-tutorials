import os

from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt
from state import EmailState
from db import create_review_token

import requests

def test_send_human(state: EmailState, config: RunnableConfig):
    thread_id = config["configurable"]["thread_id"]
    token = create_review_token(thread_id)
    print(f'use this toke --------------------{token}')
    base_url = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")
    approve_link = f"{base_url}/review/{token}/approve"
    reject_link = f"{base_url}/review/{token}/reject"

    reviewer_email = os.getenv("REVIEWER_EMAIL","adilshaikh5991@gmail.com")
    java_api_url = os.getenv("JAVA_EMAIL_API_URL", "http://localhost:5000/send-email")

    # inject approve/reject links into the html body before sending
    review_links_html = f"""
    <br><hr>
    <p><b>Newsletter Review Actions:</b></p>
    <p>
        <a href="{approve_link}" style="background:#27ae60; color:white; padding:10px 20px; text-decoration:none; margin-right:10px;">
            ✅ Approve
        </a>
        <a href="{reject_link}" style="background:#c0392b; color:white; padding:10px 20px; text-decoration:none;">
            ❌ Reject
        </a>
    </p>
    <hr>
    """

    html_with_links = state["html_body"] + review_links_html

    payload = {
        "recipient_emails": [reviewer_email],
        "subject": f"[REVIEW] {state.get('subject', 'Newsletter')}",
        "body": html_with_links,
        "cc_emails": []
    }

    try:
        response = requests.post(java_api_url, json=payload, timeout=30)
        response.raise_for_status()
        print(f"Test email sent to {reviewer_email}, token: {token}")
        return {"test_send_status": "sent"}
    except requests.RequestException as e:
        print(f"Email send failed: {e}")
        return {"test_send_status": "failed", "test_send_error": str(e)}

def human_review(state: EmailState):
    result = interrupt({
        "subject": state.get("subject"),
        "message": "Awaiting approve/reject decision"
    })
    print(f'result -----------------------------------{result}')
    # approve comes as a plain string, reject comes as a dict with feedback
    if isinstance(result, dict):
        print('graph resumes.................')
        return {
            "human_decision": result.get("decision"),
            "human_feedback": result.get("feedback")
        }
    print('graph resumes.................')
    return {
        "human_decision": result,
        "human_feedback": None
    }

def route_decision(state: EmailState):
    if (state["human_decision"] == "approve") :
        return "approve"

    elif (state["human_reject_iteration"]>=2) :
        return "reject_exceeded"
    
    else :
        return  "reject_with_feedback"

def reset_for_human_retry (state : EmailState) : 
        return {
             "iteration": 0,
        "human_reject_iteration": state.get("human_reject_iteration", 0) + 1
        }