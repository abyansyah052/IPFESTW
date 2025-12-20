"""
Database Connection and Session Management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import os
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    """Get database URL from environment"""
    return os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/scenario_calc')

# Create engine
engine = create_engine(get_database_url(), pool_pre_ping=True, pool_size=5, max_overflow=10)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create scoped session for thread-safety
ScopedSession = scoped_session(SessionLocal)

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = ScopedSession()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_session():
    """Get a new database session"""
    return SessionLocal()
