from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime, timezone

# Handle ObjectId import gracefully
try:
    from bson import ObjectId
except ImportError:
    # Use mock ObjectId if bson is not available
    class ObjectId:
        def __init__(self, id_str):
            self.id_str = str(id_str)
        
        def __str__(self):
            return self.id_str

from models.question import QuestionCreate, QuestionResponse, QuestionSummary
from models.user import UserResponse
from routes.auth import get_current_user
from database import get_questions_collection, get_users_collection, get_answers_collection

# Import AI features
from models.auto_tag import auto_tag_question
from models.toxic_spam_model import is_toxic
from models.smart_search import smart_search

# Import notification functions
from routes.notification import notify_mentions

router = APIRouter(prefix="/questions", tags=["questions"])

@router.post("/", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    question_data: QuestionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new question with AI-powered features and notifications"""
    questions_collection = get_questions_collection()
    
    # AI Content Moderation - Check for toxic content
    combined_text = question_data.title + " " + question_data.description
    is_toxic_content, toxic_score = is_toxic(combined_text)
    
    if is_toxic_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your question does not meet our community guidelines. Please ensure your content is respectful and appropriate for all users."
        )
    
    # AI Auto-tagging - Suggest tags if none provided or enhance existing ones
    question_for_tagging = {
        "title": question_data.title,
        "body": question_data.description
    }
    
    # Generate AI tags
    ai_tagged_question = auto_tag_question(question_for_tagging, top_k=8)
    ai_suggested_tags = ai_tagged_question["tags"]
    
    # Combine user tags with AI suggestions (remove duplicates)
    final_tags = list(set(question_data.tags + ai_suggested_tags))[:10]  # Max 10 tags
    
    # Create question document
    question_doc = {
        "title": question_data.title,
        "description": question_data.description,
        "tags": final_tags,
        "user_id": str(current_user["_id"]),
        "created_at": datetime.now(timezone.utc),
        "answers": [],  # Empty array of answer IDs
        "accepted_answer": None,
        "ai_enhanced": True,  # Flag to indicate AI processing
        "toxic_score": toxic_score  # Store for monitoring
    }
    
    # Insert question
    result = questions_collection.insert_one(question_doc)
    
    # Get the created question
    created_question = questions_collection.find_one({"_id": result.inserted_id})
    
    # Trigger notifications for @mentions in question content
    await notify_mentions(
        combined_text, 
        str(current_user["_id"]), 
        question_id=str(result.inserted_id)
    )
    
    # Return response
    return QuestionResponse(
        id=str(created_question["_id"]),
        title=created_question["title"],
        description=created_question["description"],
        tags=created_question["tags"],
        user_id=created_question["user_id"],
        created_at=created_question["created_at"],
        answers=created_question["answers"],
        accepted_answer=created_question["accepted_answer"],
        answer_count=len(created_question["answers"]),
        username=current_user["username"]
    )

@router.get("/search")
async def search_questions(q: str):
    """Smart search questions using AI-powered semantic search"""
    from models.smart_search import smart_search
    from models.smart_search import AI_AVAILABLE as SEARCH_AI_AVAILABLE
    
    if not SEARCH_AI_AVAILABLE:
        # Fallback to simple text search
        questions_collection = get_questions_collection()
        users_collection = get_users_collection()
        
        # Simple text search in title and description
        query = {
            "$or": [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
                {"tags": {"$in": [q.lower()]}}
            ]
        }
        
        questions = list(questions_collection.find(query).limit(10))
        
        # Format results
        results = []
        for question in questions:
            user = users_collection.find_one({"_id": ObjectId(question["user_id"])})
            results.append({
                "id": str(question["_id"]),
                "title": question["title"],
                "description": question["description"][:200] + "...",
                "tags": question["tags"],
                "username": user["username"] if user else "Unknown",
                "answer_count": len(question["answers"]),
                "score": 0.5  # Default score for fallback
            })
        
        return {"results": results, "ai_powered": False}
    
    # Get all questions from database
    questions_collection = get_questions_collection()
    users_collection = get_users_collection()
    
    questions = list(questions_collection.find())
    
    # Convert to format expected by smart_search
    search_questions = []
    for q_doc in questions:
        user = users_collection.find_one({"_id": ObjectId(q_doc["user_id"])})
        search_questions.append({
            "id": str(q_doc["_id"]),
            "title": q_doc["title"],
            "body": q_doc["description"],
            "tags": q_doc["tags"],
            "username": user["username"] if user else "Unknown",
            "answer_count": len(q_doc["answers"])
        })
    
    # Use AI-powered search
    results = smart_search(q, search_questions, top_k=10)
    
    # Format results
    formatted_results = []
    for question, score in results:
        formatted_results.append({
            "id": question["id"],
            "title": question["title"],
            "description": question["body"][:200] + "...",
            "tags": question["tags"],
            "username": question["username"],
            "answer_count": question["answer_count"],
            "score": round(score, 3)
        })
    
    return {"results": formatted_results, "ai_powered": True}

@router.get("/", response_model=List[QuestionSummary])
async def get_questions(
    skip: int = 0,
    limit: int = 20,
    tag: Optional[str] = None
):
    """Get list of questions with pagination and optional tag filtering"""
    questions_collection = get_questions_collection()
    users_collection = get_users_collection()
    
    # Build query
    query = {}
    if tag:
        query["tags"] = {"$in": [tag]}
    
    # Get questions with pagination
    questions = list(questions_collection.find(query)
                    .sort("created_at", -1)
                    .skip(skip)
                    .limit(limit))
    
    # Get user info for each question
    question_summaries = []
    for question in questions:
        user = users_collection.find_one({"_id": ObjectId(question["user_id"])})
        
        question_summaries.append(QuestionSummary(
            id=str(question["_id"]),
            title=question["title"],
            tags=question["tags"],
            user_id=question["user_id"],
            username=user["username"] if user else "Unknown",
            created_at=question["created_at"],
            answer_count=len(question["answers"]),
            has_accepted_answer=question["accepted_answer"] is not None
        ))
    
    return question_summaries

@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: str):
    """Get a specific question by ID"""
    questions_collection = get_questions_collection()
    users_collection = get_users_collection()
    
    try:
        question = questions_collection.find_one({"_id": ObjectId(question_id)})
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid question ID"
        )
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Get user info
    user = users_collection.find_one({"_id": ObjectId(question["user_id"])})
    
    return QuestionResponse(
        id=str(question["_id"]),
        title=question["title"],
        description=question["description"],
        tags=question["tags"],
        user_id=question["user_id"],
        created_at=question["created_at"],
        answers=question["answers"],
        accepted_answer=question["accepted_answer"],
        answer_count=len(question["answers"]),
        username=user["username"] if user else "Unknown"
    )

@router.post("/suggest-tags")
async def suggest_tags(
    title: str,
    description: str,
    current_user: dict = Depends(get_current_user)
):
    """Get AI-suggested tags for a question"""
    question_data = {
        "title": title,
        "body": description
    }
    
    # Generate AI tags
    ai_tagged_question = auto_tag_question(question_data, top_k=8)
    
    return {
        "suggested_tags": ai_tagged_question["tags"],
        "message": "AI-generated tag suggestions based on your question content"
    }

@router.delete("/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_question(
    question_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a question (only by the author or admin)"""
    questions_collection = get_questions_collection()
    
    try:
        question = questions_collection.find_one({"_id": ObjectId(question_id)})
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid question ID"
        )
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Check if user is author or admin
    if question["user_id"] != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own questions"
        )
    
    # Delete the question
    questions_collection.delete_one({"_id": ObjectId(question_id)})
    
    # Also delete all answers for this question
    answers_collection = get_answers_collection()
    answers_collection.delete_many({"question_id": question_id}) 