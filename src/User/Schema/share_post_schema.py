from typing import List

from pydantic import BaseModel, Field, field_validator


class SharePostRequest(BaseModel):
    recipient_ids: List[int] = Field(default_factory=list, max_length=50)

    @field_validator("recipient_ids")
    @classmethod
    def ensure_unique_recipients(cls, recipient_ids: List[int]) -> List[int]:
        if len(recipient_ids) != len(set(recipient_ids)):
            raise ValueError("recipient_ids must not contain duplicates")
        return recipient_ids
