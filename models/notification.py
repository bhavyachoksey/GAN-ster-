from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum

class NotificationType(str, Enum):
    ANSWER = "answer"
    COMMENT = "comment"  
    MENTION = "mention"
    ACCEPTED_ANSWER = "accepted_answer"

class Notification(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    user_id: str = Field(..., description="ID of user receiving notification")
    from_user_id: str = Field(..., description="ID of user who triggered notification")
    type: NotificationType
    message: str = Field(..., max_length=500)
    question_id: Optional[str] = None
    answer_id: Optional[str] = None
    read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class NotificationResponse(BaseModel):
    id: str
    type: NotificationType
    message: str
    question_id: Optional[str]
    answer_id: Optional[str]
    read: bool
    created_at: datetime
    from_username: str
    question_title: Optional[str] = None

class NotificationStats(BaseModel):
    unread_count: int
    total_count: int 