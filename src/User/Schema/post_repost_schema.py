from typing import Literal

from pydantic import BaseModel


class RepostRequest(BaseModel):
    visibility: Literal["anyone", "friends"] = "anyone"
