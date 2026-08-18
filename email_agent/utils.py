import base64
import re

def _encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def _strip_tags(html: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", "", html).split())