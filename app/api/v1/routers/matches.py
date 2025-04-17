from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List

from app.core.database import get_db
from app.models.match import Match, MatchStatus
from app.schemas.match import MatchCreate, MatchUpdate, Match as MatchSchema
from app.api.v1.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/matches", tags=["matches"])

@router.post("", response_model=MatchSchema)
def create_match(
    match_in: MatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Create a new match request.
    """
    # Check if match already exists
    existing_match = db.query(Match).filter(
        Match.initiator_id == current_user.id,
        Match.recipient_id == match_in.recipient_id,
        Match.status == MatchStatus.PENDING
    ).first()

    if existing_match:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A pending match request already exists"
        )

    match = Match(
        **match_in.dict(),
        initiator_id=current_user.id,
        status=MatchStatus.PENDING
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match

@router.get("/sent", response_model=List[MatchSchema])
def get_sent_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all matches initiated by current user.
    """
    return db.query(Match).filter(Match.initiator_id == current_user.id).all()

@router.get("/received", response_model=List[MatchSchema])
def get_received_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get all matches received by current user.
    """
    return db.query(Match).filter(Match.recipient_id == current_user.id).all()

@router.put("/{match_id}", response_model=MatchSchema)
def update_match_status(
    match_id: int,
    match_update: MatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update match status (accept/reject) and optional details.
    """
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )

    # Only recipient can update match status
    if match.recipient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this match"
        )

    # Update match status and details
    for field, value in match_update.dict(exclude_unset=True).items():
        setattr(match, field, value)

    db.commit()
    db.refresh(match)
    return match