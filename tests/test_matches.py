import pytest
from fastapi import status
from datetime import datetime, timedelta

def test_create_match(client, test_user, db_session):
    """Test creating a match request"""
    # First create another user to match with
    from app.models.user import User
    from app.core.security import get_password_hash
    
    other_user = User(
        email="other@example.com",
        username="otheruser",
        hashed_password=get_password_hash("testpass"),
        is_active=True
    )
    db_session.add(other_user)
    db_session.commit()

    # Create match request
    proposed_date = datetime.utcnow() + timedelta(days=1)
    response = client.post(
        "/api/v1/matches",
        headers={"Authorization": f"Bearer {test_user['access_token']}"},
        json={
            "recipient_id": other_user.id,
            "restaurant_preference": "Italian Restaurant",
            "proposed_date": proposed_date.isoformat()
        }
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["recipient_id"] == other_user.id
    assert data["restaurant_preference"] == "Italian Restaurant"
    assert data["status"] == "pending"

def test_get_matches(client, test_user):
    """Test getting user's matches"""
    response = client.get(
        "/api/v1/matches/me",
        headers={"Authorization": f"Bearer {test_user['access_token']}"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)

def test_invalid_match_self(client, test_user):
    """Test that user cannot match with themselves"""
    response = client.post(
        "/api/v1/matches",
        headers={"Authorization": f"Bearer {test_user['access_token']}"},
        json={
            "recipient_id": test_user["user_id"],
            "restaurant_preference": "Italian Restaurant"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_update_match_status(client, test_user, db_session):
    """Test updating match status"""
    # Create another user and a match
    from app.models.user import User
    from app.models.match import Match
    from app.core.security import get_password_hash
    
    other_user = User(
        email="matcher@example.com",
        username="matcher",
        hashed_password=get_password_hash("testpass"),
        is_active=True
    )
    db_session.add(other_user)
    db_session.commit()

    match = Match(
        sender_id=other_user.id,
        receiver_id=test_user["user_id"],
        status="pending"
    )
    db_session.add(match)
    db_session.commit()

    # Update match status
    response = client.put(
        f"/api/v1/matches/{match.id}",
        headers={"Authorization": f"Bearer {test_user['access_token']}"},
        json={
            "status": "accepted",
            "restaurant_preference": "Updated Restaurant"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "accepted"