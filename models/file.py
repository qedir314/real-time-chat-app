from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, UTC
import uuid


class FileMetadata(BaseModel):
    """Model for file metadata stored in MongoDB"""
    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_name: str
    stored_name: str  # UUID-based name on disk
    content_type: str
    size: int  # bytes
    uploader: str  # username
    room_id: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FileResponse(BaseModel):
    """Response model for file upload"""
    file_id: str
    original_name: str
    content_type: str
    size: int
    url: str
