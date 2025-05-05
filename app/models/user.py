from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    profile = relationship("Profile", uselist=False, back_populates="user")
    sent_matches = relationship(
        "Match", back_populates="sender", foreign_keys="Match.sender_id"
    )
    received_matches = relationship(
        "Match",
        back_populates="receiver",
        foreign_keys="Match.receiver_id"
    )
