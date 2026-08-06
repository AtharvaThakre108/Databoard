from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    # FastAPI dependency: yields a session per request, guarantees
    # .close() runs even on exception. Equivalent of Flask-SQLAlchemy's
    # global db.session, but explicit and safe under multiple workers.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()