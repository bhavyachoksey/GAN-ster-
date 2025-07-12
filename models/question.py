from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone

class Question(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    tags: List[str] = Field(..., min_items=1, max_items=10)
    user_id: str = Field(..., description="ID of the user who asked the question")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    answers: List[str] = Field(default_factory=list, description="List of answer IDs")
    accepted_answer: Optional[str] = Field(None, description="ID of the accepted answer")

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class QuestionCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=5000)
    tags: List[str] = Field(..., min_items=1, max_items=10)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "How to implement JWT authentication in FastAPI?",
                "description": "I'm building a REST API with FastAPI and need to implement JWT authentication. What's the best approach?",
                "tags": ["fastapi", "jwt", "authentication", "python"]
            }
        }

class QuestionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=5000)
    tags: Optional[List[str]] = Field(None, min_items=1, max_items=10)

class QuestionResponse(BaseModel):
    id: str
    title: str
    description: str
    tags: List[str]
    user_id: str
    created_at: datetime
    answers: List[str]
    accepted_answer: Optional[str]
    
    # Additional fields for API responses
    answer_count: int = 0
    username: Optional[str] = None  # Will be populated from user lookup

class QuestionSummary(BaseModel):
    """Simplified question model for list views"""
    id: str
    title: str
    tags: List[str]
    user_id: str
    username: Optional[str] = None
    created_at: datetime
    answer_count: int
    has_accepted_answer: bool 