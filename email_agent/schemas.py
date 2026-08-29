from typing import List, Optional
from pydantic import BaseModel, Field

class EmailIntakeExtraction(BaseModel):
    subject: Optional[str] = Field(default=None, description="Email subject, if mentioned")
    bcc: Optional[List[str]] = Field(default=None, description="BCC email addresses, if mentioned")
    email_body_text: str = Field(description="The core newsletter content, cleaned up from the user's message")
    image_placement: Optional[str] = Field(default=None, description="Where the embedded image goes, e.g. 'middle of the text'")
    use_snap_as_template: bool = Field(default=False, description="True if user referenced the snap for layout/formatting or True if client_snap_path is present")

class ComposeHtmlOutput(BaseModel):
    body_html: str 
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
    feedback: str = Field(description="Specific, actionable issues to fix. Empty string if passed.")