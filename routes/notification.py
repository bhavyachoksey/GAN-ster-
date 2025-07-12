from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime, timezone
from bson import ObjectId
import re

from models.notification import NotificationResponse, NotificationStats, NotificationType
from routes.auth import get_current_user
from database import get_users_collection, get_questions_collection, get_answers_collection

router = APIRouter(prefix="/notifications", tags=["notifications"])

# Helper function to get notifications collection
def get_notifications_collection():
    from database import Database
    db = Database.get_database()
    return db.notifications

# Helper function to create notification
async def create_notification(
    user_id: str,
    from_user_id: str,
    notification_type: NotificationType,
    message: str,
    question_id: str = None,
    answer_id: str = None
):
    """Create a new notification"""
    notifications_collection = get_notifications_collection()
    
    notification_doc = {
        "user_id": user_id,
        "from_user_id": from_user_id,
        "type": notification_type.value,
        "message": message,
        "question_id": question_id,
        "answer_id": answer_id,
        "read": False,
        "created_at": datetime.now(timezone.utc)
    }
    
    # Don't create notification if user is notifying themselves
    if user_id != from_user_id:
        await notifications_collection.insert_one(notification_doc)

# Helper function to detect @mentions
def extract_mentions(text: str) -> List[str]:
    """Extract @username mentions from text"""
    mention_pattern = r'@(\w+)'
    mentions = re.findall(mention_pattern, text)
    return mentions

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = 20,
    unread_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for current user"""
    notifications_collection = get_notifications_collection()
    users_collection = get_users_collection()
    questions_collection = get_questions_collection()
    
    # Build query
    query = {"user_id": str(current_user["_id"])}
    if unread_only:
        query["read"] = False
    
    # Get notifications
    notifications = list(notifications_collection.find(query)
                        .sort("created_at", -1)
                        .limit(limit))
    
    notification_responses = []
    for notification in notifications:
        # Get sender info
        from_user = users_collection.find_one({"_id": ObjectId(notification["from_user_id"])})
        from_username = from_user["username"] if from_user else "Unknown"
        
        # Get question title if applicable
        question_title = None
        if notification.get("question_id"):
            question = questions_collection.find_one({"_id": ObjectId(notification["question_id"])})
            question_title = question["title"] if question else None
        
        notification_responses.append(NotificationResponse(
            id=str(notification["_id"]),
            type=notification["type"],
            message=notification["message"],
            question_id=notification.get("question_id"),
            answer_id=notification.get("answer_id"),
            read=notification["read"],
            created_at=notification["created_at"],
            from_username=from_username,
            question_title=question_title
        ))
    
    return notification_responses

@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    current_user: dict = Depends(get_current_user)
):
    """Get notification statistics for bell icon"""
    notifications_collection = get_notifications_collection()
    
    total_count = notifications_collection.count_documents({"user_id": str(current_user["_id"])})
    unread_count = notifications_collection.count_documents({
        "user_id": str(current_user["_id"]),
        "read": False
    })
    
    return NotificationStats(
        unread_count=unread_count,
        total_count=total_count
    )

@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a specific notification as read"""
    notifications_collection = get_notifications_collection()
    
    try:
        result = notifications_collection.update_one(
            {
                "_id": ObjectId(notification_id),
                "user_id": str(current_user["_id"])
            },
            {"$set": {"read": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        return {"message": "Notification marked as read"}
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid notification ID"
        )

@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: dict = Depends(get_current_user)
):
    """Mark all notifications as read for current user"""
    notifications_collection = get_notifications_collection()
    
    result = notifications_collection.update_many(
        {"user_id": str(current_user["_id"])},
        {"$set": {"read": True}}
    )
    
    return {
        "message": f"Marked {result.modified_count} notifications as read"
    }

# Notification trigger functions (called from other routes)
async def notify_new_answer(question_id: str, answer_id: str, answerer_id: str):
    """Notify question author when someone answers their question"""
    questions_collection = get_questions_collection()
    users_collection = get_users_collection()
    
    question = questions_collection.find_one({"_id": ObjectId(question_id)})
    if not question:
        return
    
    answerer = users_collection.find_one({"_id": ObjectId(answerer_id)})
    answerer_username = answerer["username"] if answerer else "Someone"
    
    message = f"{answerer_username} answered your question: {question['title']}"
    
    await create_notification(
        user_id=question["user_id"],
        from_user_id=answerer_id,
        notification_type=NotificationType.ANSWER,
        message=message,
        question_id=question_id,
        answer_id=answer_id
    )

async def notify_accepted_answer(answer_id: str, question_author_id: str):
    """Notify answer author when their answer is accepted"""
    answers_collection = get_answers_collection()
    questions_collection = get_questions_collection()
    users_collection = get_users_collection()
    
    answer = answers_collection.find_one({"_id": ObjectId(answer_id)})
    if not answer:
        return
    
    question = questions_collection.find_one({"_id": ObjectId(answer["question_id"])})
    if not question:
        return
    
    question_author = users_collection.find_one({"_id": ObjectId(question_author_id)})
    author_username = question_author["username"] if question_author else "Someone"
    
    message = f"{author_username} accepted your answer to: {question['title']}"
    
    await create_notification(
        user_id=answer["user_id"],
        from_user_id=question_author_id,
        notification_type=NotificationType.ACCEPTED_ANSWER,
        message=message,
        question_id=answer["question_id"],
        answer_id=answer_id
    )

async def notify_mentions(content: str, from_user_id: str, question_id: str = None, answer_id: str = None):
    """Notify users mentioned with @username in content"""
    mentions = extract_mentions(content)
    if not mentions:
        return
    
    users_collection = get_users_collection()
    from_user = users_collection.find_one({"_id": ObjectId(from_user_id)})
    from_username = from_user["username"] if from_user else "Someone"
    
    for username in mentions:
        # Find mentioned user
        mentioned_user = users_collection.find_one({"username": username})
        if not mentioned_user:
            continue
        
        message = f"{from_username} mentioned you in a post"
        
        await create_notification(
            user_id=str(mentioned_user["_id"]),
            from_user_id=from_user_id,
            notification_type=NotificationType.MENTION,
            message=message,
            question_id=question_id,
            answer_id=answer_id
        ) 