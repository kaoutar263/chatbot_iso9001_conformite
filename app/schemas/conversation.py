from pydantic import BaseModel
from datetime import datetime
from typing import List

class ConversationCreateResponse(BaseModel):
    convo_id: str

class ConversationListResponse(BaseModel):
    conversations: List[str]
