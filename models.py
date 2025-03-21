from sqlalchemy import Column, Integer, String, TIMESTAMP, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    registered_at = Column(TIMESTAMP, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    links = relationship("Link", back_populates="user")


class Link(Base):
    __tablename__ = "Links"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    long_url = Column(String, nullable=False)
    short_url = Column(String, nullable=False)
    created_at = Column(TIMESTAMP)

    user = relationship("User", back_populates="links")
