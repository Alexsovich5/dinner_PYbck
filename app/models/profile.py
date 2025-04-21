from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.core.database import Base


class VerificationStatus(enum.Enum):
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    full_name = Column(String)
    bio = Column(String)
    cuisine_preferences = Column(String)
    dietary_restrictions = Column(String)
    location = Column(String)
    avatar_url = Column(String, nullable=True)
    
    # New fields for profile photo management
    profile_photos = Column(String, nullable=True)  # JSON string containing multiple photo URLs
    
    # New fields for verification
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime, nullable=True)
    verification_method = Column(String, nullable=True)
    
    # New detailed preferences
    cooking_level = Column(String, nullable=True)  # beginner, intermediate, expert
    preferred_dining_time = Column(String, nullable=True)  # morning, afternoon, evening
    preferred_meal_types = Column(String, nullable=True)  # homemade, restaurant, both
    preferred_group_size = Column(Integer, nullable=True)
    food_allergies = Column(String, nullable=True)
    special_diets = Column(String, nullable=True)  # kosher, halal, vegan, etc.
    favorite_cuisines = Column(String, nullable=True)  # JSON string of ranked cuisines
    price_range = Column(String, nullable=True)  # budget, mid-range, high-end
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user = relationship("User", back_populates="profile")