from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User
from app.models.profile import Profile

def init_db(db: Session) -> None:
    # Create test user if it doesn't exist
    user = db.query(User).filter(User.email == "test@example.com").first()
    if not user:
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create test profile
        profile = Profile(
            user_id=user.id,
            full_name="Test User",
            bio="A test user profile",
            cuisine_preferences="Italian, Japanese",
            dietary_restrictions="None",
            location="New York"
        )
        db.add(profile)
        db.commit()