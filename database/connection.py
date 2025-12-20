"""
Database Connection and Session Management
"""
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root - MUST happen before anything else
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path, override=True)

def get_database_url():
    """Get database URL from environment or Streamlit secrets"""
    url = None
    
    # Try Streamlit secrets first (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'DATABASE_URL' in st.secrets:
            url = st.secrets['DATABASE_URL']
    except:
        pass
    
    # Fall back to environment variable
    if not url:
        url = os.getenv('DATABASE_URL', '')
    
    # If no DATABASE_URL, use default
    if not url:
        return 'postgresql://user:password@localhost:5432/scenario_calc'
    
    # For Supabase pooler URLs with dots in username, create URL object properly
    # Format: postgresql://postgres.projectref:password@host:port/database
    if 'pooler.supabase.com' in url:
        # Parse manually to handle dot in username
        from urllib.parse import urlparse, unquote
        parsed = urlparse(url)
        
        # Use psycopg (psycopg3) driver instead of psycopg2 for Supabase
        # psycopg3 handles usernames with dots correctly
        return URL.create(
            drivername="postgresql+psycopg",  # Use psycopg3 driver
            username=unquote(parsed.username) if parsed.username else None,
            password=unquote(parsed.password) if parsed.password else None,
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path.lstrip('/') if parsed.path else 'postgres'
        )
    
    return url

# Create engine with fresh URL
_engine = None
_SessionLocal = None
_ScopedSession = None

def reset_engine():
    """Reset all cached engine/session objects - useful when .env changes"""
    global _engine, _SessionLocal, _ScopedSession
    if _engine:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
    _ScopedSession = None

def get_engine():
    """Get or create database engine (lazy initialization)"""
    global _engine
    if _engine is None:
        # Reload .env to get fresh values
        load_dotenv(env_path, override=True)
        
        db_url = get_database_url()
        
        # For psycopg3 with Supabase pooler, disable prepared statement caching
        # to avoid "prepared statement already exists" errors
        connect_args = {}
        if 'psycopg' in str(db_url):
            connect_args = {"prepare_threshold": None}
        
        _engine = create_engine(
            db_url, 
            pool_pre_ping=True, 
            pool_size=5, 
            max_overflow=10,
            connect_args=connect_args
        )
    return _engine

def get_session_factory():
    """Get or create session factory"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal

def get_scoped_session():
    """Get or create scoped session"""
    global _ScopedSession
    if _ScopedSession is None:
        _ScopedSession = scoped_session(get_session_factory())
    return _ScopedSession

# Legacy compatibility - expose engine as module-level variable
engine = property(lambda self: get_engine())

@contextmanager
def get_db_session():
    """Context manager for database sessions"""
    session = get_scoped_session()()
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
    return get_session_factory()()
