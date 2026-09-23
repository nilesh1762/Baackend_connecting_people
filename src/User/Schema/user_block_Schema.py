from pydantic import BaseModel

class BlockActionRequest(BaseModel):
    user_id_to_block: int
