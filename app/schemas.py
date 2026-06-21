from datetime import datetime
from typing import List

from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    answer: str


class DocumentInfo(BaseModel):
    id: int
    filename: str
    file_type: str
    chunk_count: int
    uploaded_at: datetime
    status: str

    class Config:
        from_attributes = True


class ChatHistoryItem(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
