import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database URL from environment variables (default: local SQLite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tips.db")

# Extra connection arguments required for SQLite when using multiple threads
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith(
    "sqlite") else {}

# Create the SQLAlchemy engine (the main DB connection object)
engine = create_engine(
    DATABASE_URL,
    future=True,      # Enables SQLAlchemy 2.0 style behavior
    echo=False,       # Set to True to log all SQL queries in the console
    connect_args=connect_args
)

# Create a factory for database sessions
SessionLocal = sessionmaker(
    bind=engine,        # Bind sessions to the engine
    autoflush=False,    # Disable automatic flush before each query
    autocommit=False,   # Transactions must be committed manually
    future=True         # Use SQLAlchemy 2.0 style API
)

# Dependency for FastAPI routes: provides a session per request


def get_db():
    db = SessionLocal()
    try:
        yield db         # Provide the database session to the request
    finally:
        db.close()       # Always close the session after the request
