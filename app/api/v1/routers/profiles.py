from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.core.database import get_db
from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileUpdate, Profile as ProfileSchema
from app.api.v1.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/profiles", tags=["profiles"])

@router.post("", response_model=ProfileSchema)
def create_profile(
    profile_in: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create new profile for current user.
    """
    # Check if profile already exists
    if current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists for this user"
        )

    profile = Profile(**profile_in.dict(), user_id=current_user.id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

@router.get("/me", response_model=ProfileSchema)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user's profile.
    """
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return current_user.profile

@router.put("/me", response_model=ProfileSchema)
def update_my_profile(
    profile_in: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update current user's profile.
    """
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    for field, value in profile_in.dict(exclude_unset=True).items():
        setattr(current_user.profile, field, value)
    
    db.commit()
    db.refresh(current_user.profile)
    return current_user.profile

@router.get("/{user_id}", response_model=ProfileSchema)
def get_profile(
    user_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get profile by user ID.
    """
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    return profile