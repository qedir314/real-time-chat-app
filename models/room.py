from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, UTC
import uuid

class Room(BaseModel):
    room_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    owner_id: str
    members: List[str] = []
    invite_code: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    hashed_password: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class RoomCreate(BaseModel):
    name: str
    password: Optional[str] = None

class RoomJoin(BaseModel):
    invite_code: Optional[str] = None
    room_id: Optional[str] = None
    password: Optional[str] = None
