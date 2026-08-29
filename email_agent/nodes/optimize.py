from langchain_core.messages import HumanMessage
from state import EmailState
from schemas import ReviewOutput, ComposeHtmlOutput
from models import gamma_model1, lamma_model,gamma_model
from utils import _encode_image

def optimize(state: EmailState):
    print('optimixe called ------------------------')
    use_snap = bool(state.get("client_snap_path")) and state.get("use_snap_as_template", True)

    human_feedback = state.get("human_feedback")
    auto_feedback = state.get("review_feedback")

    # human feedback takes priority — if present, auto feedback is secondary context only
    if human_feedback:
        feedback_section = (
            f"CRITICAL HUMAN FEEDBACK (MUST APPLY EXACTLY):\n{human_feedback}\n\n"
            + (f"Additional context:\n{auto_feedback}" if auto_feedback else "")
        )
    else:
        feedback_section = f"Auto-reviewer issues:\n{auto_feedback}"

    system_instruction = (
        "You are an expert HTML email designer.\n"
        "Your task is to modify the given HTML email based on the review feedback.\n"
        "- Apply all styling directly using inline CSS (e.g., style='background-color: cyan; font-weight: bold;').\n"
        "- For highlights, wrap the target text in `<span style='background-color: <color>;'>...</span>`.\n"
        "- For bolding, wrap the target text in `<strong>...</strong>` or use `font-weight: bold;`.\n"
        "- Preserve the rest of the existing HTML layout and typography.\n"
        "- Output the complete, updated HTML."
    )
    user_content = (
        f"{system_instruction}\n\n"
        f"CURRENT HTML:\n{state['html_body']}\n\n"
        f"FEEDBACK TO APPLY:\n{feedback_section}"
    )

    if use_snap:
        img_b64 = _encode_image(state["client_snap_path"])
        content_blocks = [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            {"type": "text", "text": user_content}
        ]
        result = gamma_model1.with_structured_output(ComposeHtmlOutput).invoke([HumanMessage(content=content_blocks)])
    else:
        result = gamma_model1.with_structured_output(ComposeHtmlOutput).invoke([HumanMessage(content=user_content)])

    new_html = result.body_html
    print("HTML CHANGED:", new_html.strip() != state["html_body"].strip())
    print("NEW HTML SNIPPET:", new_html[:500])
    
    return {
        "html_body": result.body_html,
        "iteration": state["iteration"] + 1,
        "human_feedback": None   # clear after use so it doesn't bleed into next auto-review cycle
    }