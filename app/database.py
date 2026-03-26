"""
Database setup and session management.

Using SQLite for simplicity - no external DB server needed.
The db file gets created in the project root when you run the import script.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# figure out where the db file should live
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "bank_data.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # needed for SQLite + FastAPI
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Makes sure the connection is properly closed after each request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
