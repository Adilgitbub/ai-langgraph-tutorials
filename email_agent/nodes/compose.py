import os
from jinja2 import Template
from langchain_core.messages import HumanMessage
from state import EmailState
from schemas import ComposeHtmlOutput, StyledHtmlOutput
from models import gamma_model1
from utils import _encode_image, _strip_tags

EMAIL_TEMPLATE = Template("""
<html>
<body style="font-family: Arial, sans-serif; font-size: 14px; color: #222222; line-height: 1.5;">
{{ body_html | safe }}
</body>
</html>
""")

def apply_snap_styling(body_html: str, snap_path: str) -> str:
    img_b64 = _encode_image(snap_path)
    content_blocks = [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
        {"type": "text", "text": (
            "Here is an HTML email body:\n\n" + body_html +
            "\n\nLooking at the reference screenshot above, add <b> tags around bold text "
            "and <span style=\"background-color:COLOR\"> tags around highlighted text, "
            "matching the styling shown. Return the full HTML with tags inserted. "
            "Do not alter the wording in any way."
        )}
    ]
    result: StyledHtmlOutput = (
        gamma_model1
        .with_structured_output(StyledHtmlOutput)
        .invoke([HumanMessage(content=content_blocks)])
    )

    if _strip_tags(result.styled_html) == _strip_tags(body_html):
        return result.styled_html
    else:
        print("⚠️ Styling step altered wording — falling back to unstyled HTML")
        return body_html

def compose_html(state: EmailState):
    has_image = bool(state.get("embed_image_path"))
    placement_instruction = state.get("image_placement") or "at the end, before the sign-off"
    use_snap = bool(state.get("client_snap_path")) and state.get("use_snap_as_template", True)

    prompt = (
        "Convert the following plain text email into clean HTML using <p> tags for each paragraph. "
        "Preserve the wording exactly — only add HTML structure, do not rewrite the content.\n\n"
        + (f"Insert the marker {{{{IMAGE_HERE}}}} at this position: {placement_instruction}\n\n"
           if has_image else "Do not include any image marker.\n\n")
        + f"Email text:\n{state['email_content']}"
    )

    result: ComposeHtmlOutput = (
        gamma_model1
        .with_structured_output(ComposeHtmlOutput)
        .invoke([HumanMessage(content=prompt)])
    )
    body_html = result.body_html

    if has_image:
        image_filename = os.path.basename(state["embed_image_path"])
        img_tag = f'<img src="{image_filename}" alt="embedded image" style="max-width:100%; margin:12px 0;">'
        body_html = (
            body_html.replace("{{IMAGE_HERE}}", img_tag)
            if "{{IMAGE_HERE}}" in body_html
            else body_html + img_tag
        )
    else:
        body_html = body_html.replace("{{IMAGE_HERE}}", "")

    if use_snap:
        body_html = apply_snap_styling(body_html, state["client_snap_path"])

    final_html = EMAIL_TEMPLATE.render(body_html=body_html)
    return {"html_body": final_html}