from typing import TypedDict, Literal, Optional

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
    published: bool
    html_body: str