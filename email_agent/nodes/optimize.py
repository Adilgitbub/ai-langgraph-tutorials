from langchain_core.messages import HumanMessage
from state import EmailState
from schemas import ReviewOutput, ComposeHtmlOutput
from models import gamma_model1, lamma_model,gamma_model
from utils import _encode_image

def optimize(state: EmailState):
    use_snap = bool(state.get("client_snap_path")) and state.get("use_snap_as_template", True)

    human_feedback = state.get("human_feedback")
    auto_feedback = state.get("review_feedback")

    # human feedback takes priority — if present, auto feedback is secondary context only
    if human_feedback:
        feedback_section = (
            f"The human reviewer specifically requested these changes (highest priority):\n{human_feedback}\n\n"
            + (f"Additionally, the auto-reviewer noted (apply only if not already addressed above):\n{auto_feedback}"
               if auto_feedback else "")
        )
    else:
        feedback_section = f"The auto-reviewer found these issues:\n{auto_feedback}"

    prompt = (
        "Here is the current HTML email:\n\n" + state["html_body"] +
        f"\n\n{feedback_section}\n\n"
        "Fix ONLY the issues mentioned. Do not change anything correct. Return the full corrected HTML."
    )

    if use_snap:
        img_b64 = _encode_image(state["client_snap_path"])
        content_blocks = [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            {"type": "text", "text": prompt}
        ]
        result = gamma_model1.with_structured_output(ComposeHtmlOutput).invoke([HumanMessage(content=content_blocks)])
    else:
        result = gamma_model1.with_structured_output(ComposeHtmlOutput).invoke([HumanMessage(content=prompt)])

    return {
        "html_body": result.body_html,
        "iteration": state["iteration"] + 1,
        "human_feedback": None   # clear after use so it doesn't bleed into next auto-review cycle
    }