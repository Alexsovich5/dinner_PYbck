import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.core.database import get_db
from app.main import app  # Assuming your FastAPI app instance is here
from app.models.user import User
from app.models.profile import Profile
from app.models.match import Match, MatchStatus
from app.api.v1.deps import get_current_user

client = TestClient(app)

# Fixtures for mock DB and current user
@pytest.fixture
def mock_db_session():
    db = MagicMock(spec=Session)
    # Add more specific mock behaviors if needed, e.g., db.query(...).filter(...).all()
    return db

@pytest.fixture
def mock_current_user():
    user = User(id=1, email="test@example.com", is_active=True, profile=None)
    # Add a profile to the user for most tests
    user.profile = Profile(
        user_id=1,
        bio="Test bio",
        cuisine_preferences="Italian,Mexican",
        location="Test City",
        dietary_restrictions="None"
    )
    return user

# Override dependencies
def override_get_db():
    mock_db = MagicMock(spec=Session)
    try:
        yield mock_db
    finally:
        pass # No actual commit/rollback needed for mock

def override_get_current_user():
    user = User(id=1, email="test@example.com", is_active=True, profile=None)
    user.profile = Profile(
        user_id=1,
        bio="Test bio",
        cuisine_preferences="Italian,Mexican",
        location="Test City",
        dietary_restrictions="None"
    )
    return user

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


# Test cases will be added here

def test_get_potential_matches_no_profile(mock_db_session, mock_current_user):
    # Arrange
    mock_current_user.profile = None # Ensure user has no profile for this test
    
    # Override get_current_user for this specific test case
    def override_get_current_user_no_profile():
        return mock_current_user

    app.dependency_overrides[get_current_user] = override_get_current_user_no_profile

    # Act
    response = client.get("/api/v1/users/potential-matches")

    # Assert
    assert response.status_code == 200
    assert response.json() == []

    # Clean up dependency override
    app.dependency_overrides[get_current_user] = override_get_current_user


def test_get_potential_matches_no_potential_matches(mock_db_session, mock_current_user):
    # Arrange
    # Mock _get_matched_user_ids to simulate all users are already matched or current user
    with patch('app.api.v1.routers.users._get_matched_user_ids', return_value={1, 2, 3}):
        # Mock db.query to return no users
        mock_db_session.query.return_value.join.return_value.filter.return_value.all.return_value = []

        app.dependency_overrides[get_db] = lambda: mock_db_session
        app.dependency_overrides[get_current_user] = lambda: mock_current_user

        # Act
        response = client.get("/api/v1/users/potential-matches")

        # Assert
        assert response.status_code == 200
        assert response.json() == []

    # Clean up dependency override
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user


def test_get_potential_matches_exclude_already_matched(mock_db_session, mock_current_user):
    # Arrange
    user2_profile = Profile(user_id=2, cuisine_preferences="Indian", location="Test City", dietary_restrictions="None")
    user2 = User(id=2, email="user2@example.com", is_active=True, profile=user2_profile)

    user3_profile = Profile(user_id=3, cuisine_preferences="Italian", location="Test City", dietary_restrictions="Vegan")
    user3 = User(id=3, email="user3@example.com", is_active=True, profile=user3_profile) # Potential match

    # User 2 is already matched with current_user (user_id=1)
    # _get_matched_user_ids will return {1, 2} effectively
    with patch('app.api.v1.routers.users._get_matched_user_ids', return_value={mock_current_user.id, user2.id}):
        # Mock db.query to return user3 (potential) and user2 (already matched)
        # The filter `not_(User.id.in_(matched_user_ids))` in the actual code should exclude user2
        mock_db_session.query.return_value.join.return_value.filter.return_value.all.return_value = [
            (user3, user3.profile),
            (user2, user2.profile) # This user should be filtered out by the `not_in` clause
        ]
        # Mock scoring functions to return some score
        with patch('app.api.v1.routers.users._calculate_cuisine_score', return_value=10), \
             patch('app.api.v1.routers.users._calculate_location_score', return_value=10), \
             patch('app.api.v1.routers.users._calculate_dietary_score', return_value=10), \
             patch('app.api.v1.routers.users._calculate_success_rate_score', return_value=5):

            app.dependency_overrides[get_db] = lambda: mock_db_session
            app.dependency_overrides[get_current_user] = lambda: mock_current_user

            # Act
            response = client.get("/api/v1/users/potential-matches")

            # Assert
            assert response.status_code == 200
            response_data = response.json()
            assert len(response_data) == 1
            assert response_data[0]["id"] == user3.id # Only user3 should be returned

    # Clean up dependency override
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user


def test_get_potential_matches_exclude_inactive_profiles(mock_db_session, mock_current_user):
    # Arrange
    user_active_profile = Profile(user_id=2, cuisine_preferences="Indian", location="Test City", dietary_restrictions="None")
    user_active = User(id=2, email="active@example.com", is_active=True, profile=user_active_profile)

    user_inactive_profile = Profile(user_id=3, cuisine_preferences="Italian", location="Test City", dietary_restrictions="Vegan")
    user_inactive = User(id=3, email="inactive@example.com", is_active=False, profile=user_inactive_profile) # Inactive

    with patch('app.api.v1.routers.users._get_matched_user_ids', return_value={mock_current_user.id}):
        # db.query().all() in the endpoint should filter out user_inactive
        mock_db_session.query.return_value.join.return_value.filter.return_value.all.return_value = [
            (user_active, user_active.profile),
            (user_inactive, user_inactive.profile) # This user has is_active=False
        ]
        with patch('app.api.v1.routers.users._calculate_cuisine_score', return_value=10), \
             patch('app.api.v1.routers.users._calculate_location_score', return_value=10), \
             patch('app.api.v1.routers.users._calculate_dietary_score', return_value=10), \
             patch('app.api.v1.routers.users._calculate_success_rate_score', return_value=5):

            app.dependency_overrides[get_db] = lambda: mock_db_session
            app.dependency_overrides[get_current_user] = lambda: mock_current_user

            # Act
            response = client.get("/api/v1/users/potential-matches")

            # Assert
            assert response.status_code == 200
            response_data = response.json()
            assert len(response_data) == 1
            assert response_data[0]["id"] == user_active.id # Only active user should be returned

    # Clean up dependency override
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user


def test_get_potential_matches_exclude_current_user(mock_db_session, mock_current_user):
    # Arrange
    # _get_matched_user_ids is mocked to include current_user.id by default in its logic.
    # The main query `not_(User.id.in_(matched_user_ids))` handles this.
    # We'll add another potential user to ensure the list isn't empty for other reasons.
    user2_profile = Profile(user_id=2, cuisine_preferences="Indian", location="Test City", dietary_restrictions="None")
    user2 = User(id=2, email="user2@example.com", is_active=True, profile=user2_profile)

    # Even if current_user (id=1) was somehow in the query result,
    # _get_matched_user_ids should ensure it's filtered out.
    # Here we assume the db query might return the current user, to test the filter.
    with patch('app.api.v1.routers.users._get_matched_user_ids', return_value={mock_current_user.id}):
        mock_db_session.query.return_value.join.return_value.filter.return_value.all.return_value = [
            (mock_current_user, mock_current_user.profile), # Current user
            (user2, user2.profile) # Potential match
        ]
        with patch('app.api.v1.routers.users._calculate_cuisine_score', return_value=10), \
             patch('app.api.v1.routers.users._calculate_location_score', return_value=10), \
             patch('app.api.v1.routers.users._calculate_dietary_score', return_value=10), \
             patch('app.api.v1.routers.users._calculate_success_rate_score', return_value=5):

            app.dependency_overrides[get_db] = lambda: mock_db_session
            app.dependency_overrides[get_current_user] = lambda: mock_current_user

            # Act
            response = client.get("/api/v1/users/potential-matches")

            # Assert
            assert response.status_code == 200
            response_data = response.json()
            assert len(response_data) == 1
            assert response_data[0]["id"] == user2.id # Current user should not be in results

    # Clean up dependency override
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user


def test_get_potential_matches_pagination(mock_db_session, mock_current_user):
    # Arrange
    users_data = []
    for i in range(2, 15): # Create 13 potential matches (user_id 2 to 14)
        profile = Profile(user_id=i, cuisine_preferences="Italian", location="Test City", dietary_restrictions="None")
        user = User(id=i, email=f"user{i}@example.com", is_active=True, profile=profile)
        users_data.append((user, profile))

    with patch('app.api.v1.routers.users._get_matched_user_ids', return_value={mock_current_user.id}):
        mock_db_session.query.return_value.join.return_value.filter.return_value.all.return_value = users_data
        
        # Mock scoring to assign descending scores, making user2 highest, user3 next, etc.
        # This makes the sorting predictable for pagination.
        def mock_score_side_effect(db_sess, user_id_val):
            return 20 - user_id_val # Higher score for lower ID

        with patch('app.api.v1.routers.users._calculate_cuisine_score', return_value=5), \
             patch('app.api.v1.routers.users._calculate_location_score', return_value=5), \
             patch('app.api.v1.routers.users._calculate_dietary_score', return_value=5), \
             patch('app.api.v1.routers.users._calculate_success_rate_score', side_effect=mock_score_side_effect):

            app.dependency_overrides[get_db] = lambda: mock_db_session
            app.dependency_overrides[get_current_user] = lambda: mock_current_user

            # Act: Get first page (limit 5)
            response_page1 = client.get("/api/v1/users/potential-matches?skip=0&limit=5")
            data_page1 = response_page1.json()

            # Assert: Page 1
            assert response_page1.status_code == 200
            assert len(data_page1) == 5
            assert data_page1[0]["id"] == 2 # Highest score due to mock_score_side_effect
            assert data_page1[4]["id"] == 6

            # Act: Get second page (skip 5, limit 5)
            response_page2 = client.get("/api/v1/users/potential-matches?skip=5&limit=5")
            data_page2 = response_page2.json()

            # Assert: Page 2
            assert response_page2.status_code == 200
            assert len(data_page2) == 5
            assert data_page2[0]["id"] == 7
            assert data_page2[4]["id"] == 11

            # Act: Get last page (should have 3 items)
            response_page3 = client.get("/api/v1/users/potential-matches?skip=10&limit=5")
            data_page3 = response_page3.json()

            # Assert: Page 3
            assert response_page3.status_code == 200
            assert len(data_page3) == 3 # Remaining users
            assert data_page3[0]["id"] == 12
            assert data_page3[2]["id"] == 14
            
    # Clean up dependency override
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
