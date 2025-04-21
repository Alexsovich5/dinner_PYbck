from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.models.profile import Profile
from app.schemas.profile import (
    ProfileCreate,
    ProfileUpdate,
    Profile as ProfileSchema,
    ProfilePhoto,
    VerificationRequest,
    VerificationStatus
)
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.services.storage import upload_file, delete_file

# Error messages
PROFILE_NOT_FOUND = "Profile not found"
PROFILE_EXISTS = "Profile already exists for this user"
INVALID_FILE_TYPE = "Invalid file type. Only images are allowed"
MAX_PHOTOS_REACHED = "Maximum number of photos reached"

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.post("", response_model=ProfileSchema)
def create_profile(
    profile_in: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Create new profile for current user."""
    if current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=PROFILE_EXISTS
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
    """Get current user's profile."""
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=PROFILE_NOT_FOUND
        )
    return current_user.profile


@router.put("/me", response_model=ProfileSchema)
def update_my_profile(
    profile_in: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Update current user's profile."""
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=PROFILE_NOT_FOUND
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
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get profile by user ID."""
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=PROFILE_NOT_FOUND
        )
    return profile


@router.post("/photos", response_model=ProfilePhoto)
async def upload_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Upload a new profile photo."""
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=PROFILE_NOT_FOUND
        )
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_FILE_TYPE
        )
    
    # Check photo limit
    current_photos = current_user.profile.profile_photos or []
    if len(current_photos) >= 5:  # Maximum 5 photos per profile
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=MAX_PHOTOS_REACHED
        )
    
    # Upload file and get URL
    file_url = await upload_file(file, f"profiles/{current_user.id}")
    
    # Update profile
    photos = current_user.profile.profile_photos or []
    photos.append(file_url)
    current_user.profile.profile_photos = photos
    
    db.commit()
    db.refresh(current_user.profile)
    
    return ProfilePhoto(url=file_url)


@router.delete("/photos/{photo_url:path}")
async def delete_photo(
    photo_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Delete a profile photo."""
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=PROFILE_NOT_FOUND
        )
    
    # Remove photo from profile
    photos = current_user.profile.profile_photos or []
    if photo_url not in photos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    photos.remove(photo_url)
    current_user.profile.profile_photos = photos
    
    # Delete from storage
    await delete_file(photo_url)
    
    db.commit()
    return {"message": "Photo deleted successfully"}


@router.post("/verify", response_model=ProfileSchema)
async def request_verification(
    verification: VerificationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Request profile verification."""
    if not current_user.profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=PROFILE_NOT_FOUND
        )
    
    # Update verification status
    current_user.profile.verification_status = VerificationStatus.PENDING
    current_user.profile.verification_method = verification.verification_method
    
    if verification.verification_document:
        current_user.profile.verification_document_url = verification.verification_document
    
    db.commit()
    db.refresh(current_user.profile)
    
    return current_user.profile


@router.put("/verify/{user_id}/approve")
async def approve_verification(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """Approve a user's verification request (admin only)."""
    # TODO: Add admin check
    
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=PROFILE_NOT_FOUND
        )
    
    profile.verification_status = VerificationStatus.VERIFIED
    profile.is_verified = True
    profile.verification_date = datetime.utcnow()
    
    db.commit()
    return {"message": "Profile verification approved"}
