from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime, timezone
from bson import ObjectId

from models.answer import AnswerCreate, AnswerResponse, AnswerSummary, VoteAction
from routes.auth import get_current_user
from database import get_answers_collection, get_questions_collection, get_users_collection

# Import AI features
from models.toxic_spam_model import is_toxic
from models.ai_generated_answer import generate_chatgpt_answer

# Import notification functions
from routes.notification import notify_new_answer, notify_accepted_answer, notify_mentions

router = APIRouter(prefix="/answers", tags=["answers"])

@router.get("/", response_model=List[AnswerResponse])
async def get_all_answers():
    """Get all answers with user information"""
    answers_collection = get_answers_collection()
    users_collection = get_users_collection()
    
    # Get all answers sorted by creation time (newest first)
    answers = list(answers_collection.find().sort("created_at", -1))
    
    # Get user info for each answer
    answer_responses = []
    for answer in answers:
        user = users_collection.find_one({"_id": ObjectId(answer["user_id"])})
        
        # Check if this is an AI-generated answer
        username = user["username"] if user else "Unknown"
        if answer.get("ai_generated", False):
            username = f"{username} (AI-assisted)"
        
        answer_responses.append(AnswerResponse(
            id=str(answer["_id"]),
            question_id=answer["question_id"],
            user_id=answer["user_id"],
            content=answer["content"],
            votes=answer["votes"],
            created_at=answer["created_at"],
            is_accepted=answer["is_accepted"],
            username=username,
            user_role=user["role"] if user else "unknown"
        ))
    
    return answer_responses

@router.post("/", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED)
async def create_answer(
    question_id: str,
    answer_data: AnswerCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new answer for a question with AI moderation and notifications"""
    try:
        answers_collection = get_answers_collection()
        questions_collection = get_questions_collection()
        
        # Verify question exists
        try:
            question = questions_collection.find_one({"_id": ObjectId(question_id)})
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid question ID"
            )
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        # AI Content Moderation - Check for toxic content
        try:
            is_toxic_content, toxic_score = is_toxic(answer_data.content)
        except Exception as e:
            # Use fallback values if AI check fails
            is_toxic_content, toxic_score = False, 0.0
        
        if is_toxic_content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your answer does not meet our community guidelines. Please ensure your content is respectful and appropriate for all users."
            )
        
        # Create answer document
        answer_doc = {
            "question_id": question_id,
            "user_id": str(current_user["_id"]),
            "content": answer_data.content,
            "votes": 0,
            "is_accepted": False,
            "created_at": datetime.now(timezone.utc),
            "toxic_score": toxic_score,  # Store for monitoring
            "ai_moderated": True  # Flag to indicate AI processing
        }
        
        # Insert answer
        result = answers_collection.insert_one(answer_doc)
        
        # Update question with answer ID
        questions_collection.update_one(
            {"_id": ObjectId(question_id)},
            {"$push": {"answers": str(result.inserted_id)}}
        )
        
        # Get the created answer
        created_answer = answers_collection.find_one({"_id": result.inserted_id})
        
        # Trigger notifications (with error handling)
        try:
            await notify_new_answer(question_id, str(result.inserted_id), str(current_user["_id"]))
            await notify_mentions(answer_data.content, str(current_user["_id"]), question_id, str(result.inserted_id))
        except Exception as e:
            # Continue without failing the answer creation
            pass
        
        # Return response
        return AnswerResponse(
            id=str(created_answer["_id"]),
            question_id=created_answer["question_id"],
            user_id=created_answer["user_id"],
            content=created_answer["content"],
            votes=created_answer["votes"],
            created_at=created_answer["created_at"],
            is_accepted=created_answer["is_accepted"],
            username=current_user["username"],
            user_role=current_user["role"]
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create answer. Please try again."
        )

@router.post("/ai-generate", response_model=AnswerResponse, status_code=status.HTTP_201_CREATED)
async def create_ai_answer(
    question_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Generate an AI answer for a question"""
    try:
        answers_collection = get_answers_collection()
        questions_collection = get_questions_collection()
        
        # Verify question exists
        try:
            question = questions_collection.find_one({"_id": ObjectId(question_id)})
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid question ID"
            )
        
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )
        
        # Check if user has permissions for AI answers
        if current_user["role"] not in ["admin", "user"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to generate AI answers"
            )
        
        # Generate AI answer
        question_text = f"{question['title']} - {question['description']}"
        print(f"DEBUG: Generating AI answer for question: {question_text[:100]}...")
        ai_content = generate_chatgpt_answer(question_text)
        
        if ai_content.startswith("Error:"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AI answer generation is currently unavailable. Please try again later."
            )
        
        # Create answer document
        answer_doc = {
            "question_id": question_id,
            "user_id": str(current_user["_id"]),
            "content": ai_content,
            "votes": 0,
            "is_accepted": False,
            "created_at": datetime.now(timezone.utc),
            "ai_generated": True,  # Flag to indicate AI-generated content
            "toxic_score": 0.0  # AI-generated content should be safe
        }
        
        # Insert answer
        result = answers_collection.insert_one(answer_doc)
        
        # Update question with answer ID
        questions_collection.update_one(
            {"_id": ObjectId(question_id)},
            {"$push": {"answers": str(result.inserted_id)}}
        )
        
        # Get the created answer
        created_answer = answers_collection.find_one({"_id": result.inserted_id})
        
        # Trigger notification for AI answer (with error handling)
        try:
            await notify_new_answer(question_id, str(result.inserted_id), str(current_user["_id"]))
        except Exception as e:
            # Continue without failing the answer creation
            pass
        
        # Return response
        return AnswerResponse(
            id=str(created_answer["_id"]),
            question_id=created_answer["question_id"],
            user_id=created_answer["user_id"],
            content=created_answer["content"],
            votes=created_answer["votes"],
            created_at=created_answer["created_at"],
            is_accepted=created_answer["is_accepted"],
            username=f"{current_user['username']} (AI-assisted)",
            user_role=current_user["role"]
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI answer. Please try again."
        )

@router.get("/question/{question_id}", response_model=List[AnswerResponse])
async def get_answers_for_question(question_id: str):
    """Get all answers for a specific question"""
    answers_collection = get_answers_collection()
    users_collection = get_users_collection()
    
    # Get answers for the question
    answers = list(answers_collection.find({"question_id": question_id})
                  .sort("is_accepted", -1)  # Accepted answers first
                  .sort("votes", -1)        # Then by votes
                  .sort("created_at", 1))   # Then by creation time
    
    # Get user info for each answer
    answer_responses = []
    for answer in answers:
        user = users_collection.find_one({"_id": ObjectId(answer["user_id"])})
        
        # Check if this is an AI-generated answer
        username = user["username"] if user else "Unknown"
        if answer.get("ai_generated", False):
            username = f"{username} (AI-assisted)"
        
        answer_responses.append(AnswerResponse(
            id=str(answer["_id"]),
            question_id=answer["question_id"],
            user_id=answer["user_id"],
            content=answer["content"],
            votes=answer["votes"],
            created_at=answer["created_at"],
            is_accepted=answer["is_accepted"],
            username=username,
            user_role=user["role"] if user else "guest"
        ))
    
    return answer_responses

@router.get("/{answer_id}", response_model=AnswerResponse)
async def get_answer(answer_id: str):
    """Get a specific answer by ID"""
    answers_collection = get_answers_collection()
    users_collection = get_users_collection()
    
    try:
        answer = answers_collection.find_one({"_id": ObjectId(answer_id)})
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid answer ID"
        )
    
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found"
        )
    
    # Get user info
    user = users_collection.find_one({"_id": ObjectId(answer["user_id"])})
    
    # Check if this is an AI-generated answer
    username = user["username"] if user else "Unknown"
    if answer.get("ai_generated", False):
        username = f"{username} (AI-assisted)"
    
    return AnswerResponse(
        id=str(answer["_id"]),
        question_id=answer["question_id"],
        user_id=answer["user_id"],
        content=answer["content"],
        votes=answer["votes"],
        created_at=answer["created_at"],
        is_accepted=answer["is_accepted"],
        username=username,
        user_role=user["role"] if user else "guest"
    )

@router.post("/{answer_id}/vote")
async def vote_answer(
    answer_id: str,
    vote_action: VoteAction,
    current_user: dict = Depends(get_current_user)
):
    """Vote on an answer (upvote/downvote/remove vote)"""
    answers_collection = get_answers_collection()
    
    try:
        answer = answers_collection.find_one({"_id": ObjectId(answer_id)})
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid answer ID"
        )
    
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found"
        )
    
    # Can't vote on your own answer
    if answer["user_id"] == str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot vote on your own answer"
        )
    
    # Update vote count based on action
    if vote_action.action == "upvote":
        answers_collection.update_one(
            {"_id": ObjectId(answer_id)},
            {"$inc": {"votes": 1}}
        )
    elif vote_action.action == "downvote":
        answers_collection.update_one(
            {"_id": ObjectId(answer_id)},
            {"$inc": {"votes": -1}}
        )
    # For "remove" action, we don't change the vote count
    
    # Get updated answer
    updated_answer = answers_collection.find_one({"_id": ObjectId(answer_id)})
    
    return {
        "message": f"Vote {vote_action.action} applied successfully",
        "new_vote_count": updated_answer["votes"]
    }

@router.post("/{answer_id}/accept")
async def accept_answer(
    answer_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Accept an answer (only question author can do this)"""
    answers_collection = get_answers_collection()
    questions_collection = get_questions_collection()
    
    try:
        answer = answers_collection.find_one({"_id": ObjectId(answer_id)})
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid answer ID"
        )
    
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found"
        )
    
    # Get the question
    question = questions_collection.find_one({"_id": ObjectId(answer["question_id"])})
    
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )
    
    # Check if current user is the question author
    if question["user_id"] != str(current_user["_id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the question author can accept answers"
        )
    
    # Remove acceptance from any previously accepted answer
    answers_collection.update_many(
        {"question_id": answer["question_id"]},
        {"$set": {"is_accepted": False}}
    )
    
    # Accept this answer
    answers_collection.update_one(
        {"_id": ObjectId(answer_id)},
        {"$set": {"is_accepted": True}}
    )
    
    # Update question with accepted answer ID
    questions_collection.update_one(
        {"_id": ObjectId(answer["question_id"])},
        {"$set": {"accepted_answer": answer_id}}
    )
    
    # Trigger notification for accepted answer
    await notify_accepted_answer(answer_id, str(current_user["_id"]))
    
    return {"message": "Answer accepted successfully"}

@router.delete("/{answer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_answer(
    answer_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an answer (only by the author or admin)"""
    answers_collection = get_answers_collection()
    questions_collection = get_questions_collection()
    
    try:
        answer = answers_collection.find_one({"_id": ObjectId(answer_id)})
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid answer ID"
        )
    
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found"
        )
    
    # Check if user is author or admin
    if answer["user_id"] != str(current_user["_id"]) and current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own answers"
        )
    
    # Remove answer from question's answers array
    questions_collection.update_one(
        {"_id": ObjectId(answer["question_id"])},
        {"$pull": {"answers": answer_id}}
    )
    
    # If this was the accepted answer, remove acceptance
    if answer["is_accepted"]:
        questions_collection.update_one(
            {"_id": ObjectId(answer["question_id"])},
            {"$set": {"accepted_answer": None}}
        )
    
    # Delete the answer
    answers_collection.delete_one({"_id": ObjectId(answer_id)}) 