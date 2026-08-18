from langchain_core.messages import HumanMessage
from state import EmailState
from schemas import EmailIntakeExtraction
from models import gamma_model1
from utils import _encode_image

def intake(state: EmailState):
    content_blocks = []

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

    result: EmailIntakeExtraction = (
        gamma_model1
        .with_structured_output(EmailIntakeExtraction)
        .invoke([HumanMessage(content=content_blocks)])
    )

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