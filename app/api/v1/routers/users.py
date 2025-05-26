from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, not_, or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.match import Match, MatchStatus  # Added MatchStatus import
from app.schemas.auth import User as UserSchema
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserSchema)
def get_current_user_info(current_user: User = Depends(get_current_user)) -> Any:
    """Get current user information."""
    return current_user


def _calculate_cuisine_score(user_preferences: str, match_preferences: str) -> float:
    """Calculate cuisine preference compatibility score"""
    if not user_preferences or not match_preferences:
        return 0

    user_cuisines = set(c.strip().lower() for c in user_preferences.split(","))
    match_cuisines = set(c.strip().lower() for c in match_preferences.split(","))
    common_cuisines = user_cuisines.intersection(match_cuisines)
    denominator = max(len(user_cuisines), len(match_cuisines))
    score = (len(common_cuisines) / denominator) * 30
    return score


def _calculate_location_score(user_location: str, match_location: str) -> float:
    """Calculate location compatibility score"""
    if not user_location or not match_location:
        return 0
    return 25 if user_location.lower() == match_location.lower() else 0


def _calculate_dietary_score(user_restrictions: str, match_restrictions: str) -> float:
    """Calculate dietary restrictions compatibility score"""
    if not user_restrictions or not match_restrictions:
        return 0
    return 25 if user_restrictions.lower() == match_restrictions.lower() else 0


def _calculate_success_rate_score(db: Session, user_id: int) -> float:
    """Calculate match success rate score"""
    user_matches = (
        db.query(Match)
        .filter(
            or_(Match.sender_id == user_id, Match.receiver_id == user_id),
            Match.status == MatchStatus.ACCEPTED,
        )
        .count()
    )
    total_matches = (
        db.query(Match)
        .filter(or_(Match.sender_id == user_id, Match.receiver_id == user_id))
        .count()
    )
    return (user_matches / total_matches) * 20 if total_matches > 0 else 0


def _get_matched_user_ids(db: Session, current_user_id: int) -> set:
    """Get set of user IDs that are already matched"""
    matched_users = (
        db.query(Match)
        .filter(
            or_(
                Match.sender_id == current_user_id, Match.receiver_id == current_user_id
            )
        )
        .all()
    )

    matched_ids = {current_user_id}
    for match in matched_users:
        matched_ids.add(match.sender_id)
        matched_ids.add(match.receiver_id)
    return matched_ids


@router.get("/potential-matches", response_model=List[UserSchema])
def get_potential_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 10,
) -> Any:
    """
    Get potential dinner matches for the current user.
    Returns users that:
    - Are not the current user
    - Have not been matched with (either sent or received)
    - Have active profiles
    - Are ranked by compatibility based on:
        - Cuisine preference overlap (30%)
        - Location proximity (25%)
        - Dietary restrictions compatibility (25%)
        - Match history success rate (20%)
    """
    if not current_user.profile:
        return []

    matched_user_ids = _get_matched_user_ids(db, current_user.id)

    # Query for potential matches with their profiles
    potential_matches = (
        db.query(User, Profile)
        .join(Profile)
        .filter(and_(User.is_active.is_(True), not_(User.id.in_(matched_user_ids))))
        .all()
    )

    # Calculate compatibility scores
    scored_matches = []
    for user, profile in potential_matches:
        score = sum(
            [
                _calculate_cuisine_score(
                    current_user.profile.cuisine_preferences,
                    profile.cuisine_preferences,
                ),
                _calculate_location_score(
                    current_user.profile.location, profile.location
                ),
                _calculate_dietary_score(
                    current_user.profile.dietary_restrictions,
                    profile.dietary_restrictions,
                ),
                _calculate_success_rate_score(db, user.id),
            ]
        )
        scored_matches.append((user, score))

    # Sort by compatibility score and paginate
    scored_matches.sort(key=lambda x: x[1], reverse=True)
    return [match[0] for match in scored_matches[skip : skip + limit]]


@router.get("/{user_id}", response_model=UserSchema)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user
