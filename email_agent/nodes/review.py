from langchain_core.messages import HumanMessage
from state import EmailState
from schemas import ReviewOutput, ComposeHtmlOutput
from models import gamma_model1, lamma_model
from utils import _encode_image

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
        result: ReviewOutput = (
            gamma_model1
            .with_structured_output(ReviewOutput)
            .invoke([HumanMessage(content=content_blocks)])
        )
    else:
        prompt = (
            "Original email text:\n" + state["email_content"] +
            "\n\nGenerated HTML:\n" + html_body +
            "\n\nCheck that all content from the original text is present and correctly structured in the HTML "
            "(no missing paragraphs, no altered wording). Give a score 0-100 and passed=true only if score >= 70. "
            "List specific issues in feedback."
        )
        result: ReviewOutput = (
            lamma_model
            .with_structured_output(ReviewOutput)
            .invoke([HumanMessage(content=prompt)])
        )

    return {
        "evaluate": "pass" if result.passed else "failed",
        "review_score": result.score,
        "review_feedback": result.feedback
    }

def route_evaluation(state: EmailState):
    if state["evaluate"] == "pass" or state["iteration"] >= state["max_iteration"]:
        return "pass"
    return "failed"

def optimize(state: EmailState):
    use_snap = bool(state.get("client_snap_path")) and state.get("use_snap_as_template", True)
    feedback = state["review_feedback"]
    print(f"Feedback from reviewer: {feedback}")

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
        result: ComposeHtmlOutput = (
            gamma_model1
            .with_structured_output(ComposeHtmlOutput)
            .invoke([HumanMessage(content=content_blocks)])
        )
    else:
        result: ComposeHtmlOutput = (
            lamma_model
            .with_structured_output(ComposeHtmlOutput)
            .invoke([HumanMessage(content=prompt)])
        )

    return {
        "html_body": result.body_html,
        "iteration": state["iteration"] + 1
    }