from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class SessionCreate(BaseModel):
    title: str = Field(default="New conversation", max_length=200)

class SessionOut(BaseModel):
    id: UUID
    title: str
    total_prompt_tokens: int
    total_completion_tokens: int
    total_cost_usd: float
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class MessageOut(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    tokens: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=20000)
