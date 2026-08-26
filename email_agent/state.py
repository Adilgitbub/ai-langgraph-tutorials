from typing import TypedDict, Literal, Optional

from typing import TypedDict, Literal, Optional

class EmailState(TypedDict):
    input: str
    client_snap_path: Optional[str]
    embed_image_path: Optional[str]
    subject: Optional[str]
    bcc: Optional[list[str]]
    email_content: str
    html_body: str
    image_placement: Optional[str]
    use_snap_as_template: bool
    needs_clarification: bool
    clarification_question: Optional[str]
    evaluate: Optional[Literal["pass", "failed"]]
    iteration: int
    max_iteration: int
    review_score: Optional[int]
    review_feedback: Optional[str]
    human_decision: Optional[Literal["approve", "reject"]]
    human_feedback: Optional[str]           # NEW
    human_reject_iteration: int             # NEW
    test_send_status: Optional[Literal["sent", "failed"]]
    test_send_error: Optional[str]
    published: bool