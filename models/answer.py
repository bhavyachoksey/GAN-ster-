from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone

class Answer(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    question_id: str = Field(..., description="ID of the question this answer belongs to")
    user_id: str = Field(..., description="ID of the user who provided the answer")
    content: str = Field(..., min_length=10, max_length=10000)
    votes: int = Field(default=0, description="Net votes (upvotes - downvotes)")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_accepted: bool = Field(default=False, description="Whether this answer is accepted by the question author")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AnswerCreate(BaseModel):
    content: str = Field(..., min_length=10, max_length=10000)

    class Config:
        json_schema_extra = {
            "example": {
                "content": "You can implement JWT authentication in FastAPI using the python-jose library. First, install the dependencies and then create authentication utilities for token generation and validation."
            }
        }

class AnswerUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=10, max_length=10000)

class AnswerResponse(BaseModel):
    id: str
    question_id: str
    user_id: str
    content: str
    votes: int
    created_at: datetime
    is_accepted: bool
    
    # Additional fields for API responses
    username: Optional[str] = None  # Will be populated from user lookup
    user_role: Optional[str] = None  # Will be populated from user lookup

class AnswerSummary(BaseModel):
    """Simplified answer model for list views"""
    id: str
    question_id: str
    user_id: str
    username: Optional[str] = None
    content_preview: str  # First 200 characters of content
    votes: int
    created_at: datetime
    is_accepted: bool

class VoteAction(BaseModel):
    """Model for voting on answers"""
    action: str = Field(..., pattern="^(upvote|downvote|remove)$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "upvote"
            }
        } 