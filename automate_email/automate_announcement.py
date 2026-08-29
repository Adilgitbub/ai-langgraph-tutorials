# %%
import base64
import os
import re
import secrets
import sqlite3
import stat
import time
from unittest import result

from jinja2 import Template
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing import List, TypedDict, Literal, Optional
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv
from IPython.display import Image
from langgraph_sdk.schema import Interrupt
from pydantic import BaseModel, Field
from langgraph.types import interrupt

load_dotenv()

# %%
class EmailState(TypedDict):
    input: str
    client_snap_path: Optional[str]
    embed_image_path: Optional[str]
    subject: Optional[str]
    bcc: Optional[list[str]]

    email_content: str
    image_placement: Optional[str]
    use_snap_as_template: bool

    needs_clarification: bool
    clarification_question: Optional[str]

    evaluate: Optional[Literal["pass", "failed"]]
    iteration: int
    max_iteration: int
    human_decision: Optional[Literal["approve", "reject"]]
    published: bool           # idempotency guard
    html_body: str 

#  ----------------- pydantic structure format o/p and model  ------------------------
class EmailIntakeExtraction(BaseModel):
    subject: Optional[str] = Field(default=None, description="Email subject, if mentioned")
    bcc: Optional[List[str]] = Field(default=None, description="BCC email addresses, if mentioned")
    email_body_text: str = Field(description="The core newsletter content, cleaned up from the user's message")
    image_placement: Optional[str] = Field(default=None, description="Where the embedded image goes, e.g. 'middle of the text'")
    use_snap_as_template: bool = Field(default=False, description="True if user referenced the snap for layout/formatting")

class ComposeHtmlOutput(BaseModel):
    body_html: str = Field(description="Plain HTML using <p> tags, unstyled content, exact wording preserved.")
    bold_phrases: list[str] = Field(default_factory=list, description="Exact phrases that should appear bold, based on the reference snap's styling.")
    highlighted_phrases: list[dict] = Field(
        default_factory=list,
        description="List of {'text': exact phrase, 'color': css color like 'yellow' or 'cyan'} based on highlight colors seen in the snap."
    )

class StyledHtmlOutput(BaseModel):
    styled_html: str = Field(
        description="The exact same HTML provided, with <b>...</b> and "
                    "<span style=\"background-color:COLOR\">...</span> tags inserted "
                    "around phrases that appear bold/highlighted in the reference screenshot. "
                    "Do not change, add, or remove any wording — only insert styling tags."
    )

class ReviewOutput(BaseModel):
    score: int = Field(ge=0, le=100, description="Match quality score, 0-100")
    passed: bool = Field(description="True if score is high enough to proceed, false if it needs another revision pass")
    feedback: str = Field(description="Specific, actionable issues to fix — e.g. 'November 22 should be highlighted yellow," \
    " currently unstyled'. Empty string if passed.")    


#  ----------------- LLM's  ----------------  
gamma_model1 = ChatOpenAI(
    base_url="http://localhost:12434/engines/v1",
    api_key="not-needed",
    model="ai/gemma4:E4B"
)

gamma_model = ChatGoogleGenerativeAI(
    model=os.getenv("GOOGLE_MODEL", "gemini-3.6-flash"),
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    max_retries=2  # Prevents LangChain from spamming retries if it hits a snag
)

lamma_model = ChatOpenAI(
    base_url="http://localhost:12434/engines/v1",
    api_key="not-needed",
    model="ai/llama3.2:3B-Q4_K_M"
)


#  ----------------- Nodes declaration and logic  ---------------


def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")    
# %%
# STEP 1 — Intake
def intake(state: EmailState):
    content_blocks = []

    # image first, then text — gemma4 multimodal prompting best practice
    if state.get("client_snap_path"):
        img_b64 = _encode_image(state["client_snap_path"])
        content_blocks.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{img_b64}"}
        })

    instruction = (
        "Parse this user request for a newsletter/notification email.\n"
        "Extract subject, bcc, the core body content, and where an embedded image "
        "should go if mentioned. If a reference screenshot is attached above, note "
        "that its layout/formatting should be followed.\n\n"
        f"User's message:\n{state['input']}"
    )
    content_blocks.append({"type": "text", "text": instruction})

    result: EmailIntakeExtraction = gamma_model1.with_structured_output(EmailIntakeExtraction).invoke([HumanMessage(content=content_blocks)])
    # time.sleep(5)
    # merge: explicit values already in state win over what the LLM extracted
    bcc = result.bcc
    subject = result.subject
    email_content = result.email_body_text
    image_placement = result.image_placement if state.get("embed_image_path") else None

    missing = []
    if not email_content or not email_content.strip():
        missing.append("email content")
    if not bcc:
        missing.append("bcc")

    if missing:
        return {
            "needs_clarification": True,
            "clarification_question": f"I need a bit more before I can proceed: {', '.join(missing)}. Could you provide that?"
        }

    return {
        "needs_clarification": False,
        "subject": subject or "Newsletter Update",
        "bcc": bcc,
        "email_content": email_content,
        "image_placement": image_placement,
        "use_snap_as_template": result.use_snap_as_template
    }

# ------------- STEP 2 — Compose HTML --------------------------
EMAIL_TEMPLATE = Template("""
<html>
<body style="font-family: Arial, sans-serif; font-size: 14px; color: #222222; line-height: 1.5;">
{{ body_html | safe }}
</body>
</html>
""")
# def _apply_styling(html: str, bold_phrases: list[str], highlighted: list[dict]) -> str:
#     for phrase in bold_phrases:
#         if phrase and phrase in html:
#             html = html.replace(phrase, f"<b>{phrase}</b>")
#     for h in highlighted:
#         text, color = h.get("text"), h.get("color", "yellow")
#         if text and text in html:
#             html = html.replace(text, f'<span style="background-color:{color}">{text}</span>')
#     return html
def _strip_tags(html: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", "", html).split())

def apply_snap_styling(body_html: str, snap_path: str) -> str:
    print(f'----------------------------------- {snap_path}')
    img_b64 = _encode_image(snap_path)
    content_blocks = [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
        {"type": "text", "text": (
            "Here is an HTML email body:\n\n" + body_html +
            "\n\nLooking at the reference screenshot above, add <b> tags around bold text "
            "also add <span style=\"background-color:COLOR\"> tags around highlighted text wherever applicable based on refernce screenshot shared, "
            "matching the styling shown. Return the full HTML with tags inserted. "
            "Do not alter the wording in any way."
        )}
    ]
    result: StyledHtmlOutput = gamma_model1.with_structured_output(StyledHtmlOutput).invoke(
        [HumanMessage(content=content_blocks)]
    )
    # time.sleep(5)
    # safety check: make sure the model didn't sneak in wording changes
    if _strip_tags(result.styled_html) == _strip_tags(body_html):
        return result.styled_html
    else:
        print("⚠️ Styling step altered wording — falling back to unstyled HTML")
        return body_html

def compose_html(state: EmailState):
    has_image = bool(state.get("embed_image_path"))
    placement_instruction = state.get("image_placement") or "at the end, before the sign-off"
    # state['client_snap_path']='uploads/0feef4d5/client_snap.png'
    use_snap = bool(state.get("client_snap_path")) and state.get("use_snap_as_template", True)
    

    prompt = (
        "Convert the following plain text email into clean HTML using <p> tags for each paragraph. "
        "Preserve the wording exactly — only add HTML structure, do not rewrite the content.\n\n"
        + (f"Insert the marker {{{{IMAGE_HERE}}}} at this position: {placement_instruction}\n\n"
           if has_image else "Do not include any image marker.\n\n")
        + f"Email text:\n{state['email_content']}"
    )
    print(f"this is the snap path ......... {state['client_snap_path']}")
 
    # if use_snap:
    #     img_b64 = _encode_image(state["client_snap_path"])
    #     content_blocks = [
    #         {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
    #         {"type": "text", "text": (
    #             prompt +
    #             "\n\nAlso look at the reference screenshot above: identify which exact phrases are "
    #             "bold, and which are highlighted (and in what color). List those separately — "
    #             "do not embed styling tags directly in body_html."
    #         )}
    #     ]
    #     result: ComposeHtmlOutput = gamma_model.with_structured_output(ComposeHtmlOutput).invoke([HumanMessage(content=content_blocks)])
    # else:
    # always use llama for base structure — fast, no image needed here anymore
    result: ComposeHtmlOutput = gamma_model1.with_structured_output(ComposeHtmlOutput).invoke([HumanMessage(content=prompt)])
    body_html = result.body_html
   
    # time.sleep(5)
    if has_image:
        image_filename = os.path.basename(state["embed_image_path"])
        img_tag = f'<img src="{image_filename}" alt="embedded image" style="max-width:100%; margin:12px 0;">'
        body_html = (
            body_html.replace("{{IMAGE_HERE}}", img_tag)
            if "{{IMAGE_HERE}}" in body_html
            else body_html + img_tag  # fallback if model forgot the marker
        )
    else:
        body_html = body_html.replace("{{IMAGE_HERE}}", "")  # safety strip

    # if use_snap:
    #     body_html = _apply_styling(body_html, result.bold_phrases, result.highlighted_phrases)    
    if use_snap:
        body_html = apply_snap_styling(body_html, state["client_snap_path"])

    final_html = EMAIL_TEMPLATE.render(body_html=body_html)
    return {"html_body": final_html}


# STEP 3 — Auto-review
def auto_review(state: EmailState):
    use_snap = bool(state.get("client_snap_path")) and state.get("use_snap_as_template", True)
    html_body = state["html_body"]

    if use_snap:
        img_b64 = _encode_image(state["client_snap_path"])
        content_blocks = [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            {"type": "text", "text": (
                "Here is a generated HTML email:\n\n" + html_body +
                "\n\nCompare it against the reference screenshot above. Check: "
                "does the wording match, is bold/highlight styling applied correctly and in the right places, "
                "is any embedded image positioned reasonably. "
                "Give a match score 0-100 and passed=true only if score >= 70. "
                "List specific, concrete issues in feedback — not vague comments."
            )}
        ]
        result: ReviewOutput = gamma_model1.with_structured_output(ReviewOutput).invoke([HumanMessage(content=content_blocks)])
    else:
        prompt = (
            "Original email text:\n" + state["email_content"] +
            "\n\nGenerated HTML:\n" + html_body +
            "\n\nCheck that all content from the original text is present and correctly structured in the HTML "
            "(no missing paragraphs, no altered wording). Give a score 0-100 and passed=true only if score >= 70. "
            "List specific issues in feedback."
        )
        result: ReviewOutput = lamma_model.with_structured_output(ReviewOutput).invoke([HumanMessage(content=prompt)])

    return {
        "evaluate": "pass" if result.passed else "failed",
        "review_score": result.score,
        "review_feedback": result.feedback
    }

def route_evaluation(state: EmailState):
    if state["evaluate"] == "pass" or state.get('iteration',0) >= state.get('max_iteration',0):
        return "pass"
    return "failed"

# STEP 3b — Optimize (revise loop)
def optimize(state: EmailState):
    use_snap = bool(state.get("client_snap_path")) and state.get("use_snap_as_template", True)
    feedback =  state['review_feedback']
    print(f"feedback from reviewer {state['review_feedback']}")
    prompt = (
        "Here is the current HTML email:\n\n" + state["html_body"] +
        f"\n\nA reviewer found these issues: {feedback}\n\n"
        "Fix ONLY these specific issues. Do not change anything else — preserve all correct wording, "
        "structure, and styling that isn't mentioned as a problem. Return the full corrected HTML."
    )

    if use_snap:
        img_b64 = _encode_image(state["client_snap_path"])
        content_blocks = [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            {"type": "text", "text": prompt}
        ]
        result: ComposeHtmlOutput = gamma_model1.with_structured_output(ComposeHtmlOutput).invoke([HumanMessage(content=content_blocks)])
    else:
        result: ComposeHtmlOutput = lamma_model.with_structured_output(ComposeHtmlOutput).invoke([HumanMessage(content=prompt)])

    return {
        "html_body": result.body_html,
        "iteration": state["iteration"] + 1
    }

# STEP 4 — Test-send to human
def test_send_human(state: EmailState, config: RunnableConfig):
    thread_id = config["configurable"]["thread_id"]
    token = create_review_token(thread_id)
    # later, once Java is wired in: include approve/reject links built from `token` in the email body
    return {}

# STEP 5 — Human review (HITL)
def human_review(state: EmailState):
    # TODO: use interrupt() here to pause and wait for approve/reject
    print('calling review .............1')
    decision =interrupt({
        "subject":state['subject'],
        "message":"Awaiting approve/reject decision"
    })
    print(decision)
    return {
        "human_decision": decision
    }

def route_decision(state: EmailState):
    return "approve" if state["human_decision"] == "approve" else "reject"

# STEP 6/7 — Publish
def publish(state: EmailState):
    print(f'final result ----------- {route_decision(state)}')

    if state.get("published"):
        return {}  # idempotency guard
    # TODO: call Java publish API tool with final payload
    return {"published": True}

# STEP 8 — Manual fallback
def manual_handling(state: EmailState):
    # TODO: notify internal team, no automation yet
    return {}

def confirm_log(state: EmailState):
    # TODO: log final outcome
    return {}

def create_review_token(thread_id: str) -> str:
    token = secrets.token_urlsafe(16)
    conn = sqlite3.connect("review_tokens.db")
    conn.execute("CREATE TABLE IF NOT EXISTS tokens (token TEXT PRIMARY KEY, thread_id TEXT, used INTEGER DEFAULT 0)")
    conn.execute("INSERT INTO tokens VALUES (?, ?, 0)", (token, thread_id))
    conn.commit()
    return token
# %%
email_graph = StateGraph(EmailState)

email_graph.add_node("intake", intake)
email_graph.add_node("compose_html", compose_html)
email_graph.add_node("auto_review", auto_review)
email_graph.add_node("optimize", optimize)
email_graph.add_node("test_send_human", test_send_human)
email_graph.add_node("human_review", human_review)
email_graph.add_node("publish", publish)
email_graph.add_node("manual_handling", manual_handling)
email_graph.add_node("confirm_log", confirm_log)

email_graph.add_edge(START, "human_review")
# email_graph.add_edge("intake", "compose_html")
email_graph.add_edge("human_review", "publish")
email_graph.add_edge("publish", END)
# email_graph.add_edge("compose_html", "auto_review")
# email_graph.add_conditional_edges(
#     "auto_review", route_evaluation, {"pass": "test_send_human", "failed": "optimize"}
# )
# email_graph.add_edge("optimize", "auto_review")
# email_graph.add_edge("test_send_human", "human_review")
# email_graph.add_conditional_edges(
#     "human_review", route_decision, {"approve": "publish", "reject": "manual_handling"}
# )
# email_graph.add_edge("publish", "confirm_log")
# email_graph.add_edge("manual_handling", END)
# email_graph.add_edge("confirm_log", END)


#  ------ connecting to DB ------------
conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)
workflow = email_graph.compile(checkpointer=checkpointer)

thread_id = "test-run-001"
token = create_review_token(thread_id)
print("Use this token in Postman:", token)
initial_state={
    "subject":"Please approve or reject "
}

result=workflow.invoke(initial_state,config={"configurable": {"thread_id": thread_id}})
print(result)

# Image(workflow.get_graph().draw_mermaid_png())