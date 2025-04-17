from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import User as UserSchema
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserSchema)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user information.
    """
    return current_user

@router.get("/potential-matches", response_model=List[UserSchema])
def get_potential_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get potential matches for the current user.
    This endpoint will return users that:
    1. Are not the current user
    2. Have not been matched with yet
    """
    # Get all users except current user
    potential_matches = (
        db.query(User)
        .filter(User.id != current_user.id)
        .filter(User.is_active == True)
        .all()
    )
    
    return potential_matches

@router.get("/{user_id}", response_model=UserSchema)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get user by ID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user