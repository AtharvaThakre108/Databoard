from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    datasets = relationship("Dataset", back_populates="owner", cascade="all, delete-orphan")

    # No set_password()/check_password() here -- hashing lives in
    # core/security.py since we're rolling our own auth with passlib.
    # Keeps the ORM model a plain data shape.


class Dataset(Base):
    __tablename__ = "datasets"

    # Storage decision: rows/columns as JSON, not a dynamic table per
    # upload. Avoids sanitizing CSV headers into SQL identifiers; the
    # trade-off is no native SQL filtering on dataset contents, which
    # this spec's operations (preview/compute/plot) don't need anyway.
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    columns = Column(JSON, nullable=False, default=list)  # list[str] of CSV headers
    rows = Column(JSON, nullable=False, default=list)      # list[dict] of parsed CSV rows
    row_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    owner = relationship("User", back_populates="datasets")