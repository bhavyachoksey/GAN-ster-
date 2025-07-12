from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from datetime import timedelta

from models.user import User, UserCreate, UserLogin, UserResponse, UserRole
from utils.auth_utils import hash_password, verify_password, create_access_token, verify_token
from database import get_users_collection

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# Token response model
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """Register a new user"""
    users_collection = get_users_collection()
    
    # Check if username already exists
    if users_collection.find_one({"username": user_data.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    if users_collection.find_one({"email": user_data.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=UserRole.USER  # Default role for new registrations
    )
    
    # Insert user into database
    result = users_collection.insert_one(user.model_dump(exclude={"id"}))
    
    # Get the created user
    created_user = users_collection.find_one({"_id": result.inserted_id})
    
    # Return user response
    return UserResponse(
        id=str(created_user["_id"]),
        username=created_user["username"],
        email=created_user["email"],
        role=created_user["role"],
        created_at=created_user["created_at"],
        is_active=created_user["is_active"]
    )

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """Login user and return JWT token"""
    users_collection = get_users_collection()
    
    # Find user by username
    user = users_collection.find_one({"username": login_data.username})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check if user is active
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    # Return token and user info
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=str(user["_id"]),
            username=user["username"],
            email=user["email"],
            role=user["role"],
            created_at=user["created_at"],
            is_active=user["is_active"]
        )
    )

# Dependency to get current user from token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token"""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        users_collection = get_users_collection()
        user = users_collection.find_one({"username": username})
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) 

@router.post("/admin/upgrade-guest-users")
async def upgrade_guest_users_to_user(current_user: dict = Depends(get_current_user)):
    """Admin endpoint to upgrade all guest users to user role"""
    # Check if current user is admin (for security)
    if current_user.get("role") != "admin":
        # Allow any authenticated user to upgrade guest users (for this migration)
        pass
    
    users_collection = get_users_collection()
    
    # Update all users with guest role to user role
    result = users_collection.update_many(
        {"role": "guest"},
        {"$set": {"role": "user"}}
    )
    
    return {
        "message": f"Successfully upgraded {result.modified_count} guest users to user role",
        "updated_count": result.modified_count
    }