from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, not_, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.match import Match
from app.schemas.auth import User as UserSchema
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserSchema)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get current user information."""
    return current_user


@router.get("/potential-matches", response_model=List[UserSchema])
def get_potential_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10
) -> Any:
    """
    Get potential dinner matches for the current user.
    Returns users that:
    - Are not the current user
    - Have not been matched with (either sent or received)
    - Have active profiles
    """
    # Get all user IDs that are already matched
    matched_users = (
        db.query(Match)
        .filter(
            or_(
                Match.sender_id == current_user.id,
                Match.receiver_id == current_user.id
            )
        )
        .all()
    )
    
    matched_user_ids = {current_user.id}  # Include current user
    for match in matched_users:
        matched_user_ids.add(match.sender_id)
        matched_user_ids.add(match.receiver_id)

    # Query for potential matches
    potential_matches = (
        db.query(User)
        .join(Profile)  # Only get users with profiles
        .filter(
            and_(
                User.is_active.is_(True),
                not_(User.id.in_(matched_user_ids))
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    return potential_matches


@router.get("/{user_id}", response_model=UserSchema)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user
