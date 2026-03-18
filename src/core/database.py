"""
Database configuration and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import redis
import json
from contextlib import contextmanager
import logging

from .config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy setup
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,
    pool_pre_ping=True,
    echo=settings.DEBUG
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5
)


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session():
    """Context manager for database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class TenantCache:
    """Redis cache for tenant data."""
    
    @staticmethod
    def get_tenant(tenant_id: str):
        """Get tenant from cache."""
        data = redis_client.get(f"tenant:{tenant_id}")
        return json.loads(data) if data else None
    
    @staticmethod
    def set_tenant(tenant_id: str, tenant_data: dict):
        """Set tenant in cache."""
        redis_client.setex(
            f"tenant:{tenant_id}",
            settings.REDIS_TTL,
            json.dumps(tenant_data, default=str)
        )
    
    @staticmethod
    def invalidate_tenant(tenant_id: str):
        """Invalidate tenant cache."""
        redis_client.delete(f"tenant:{tenant_id}")
    
    @staticmethod
    def get_api_key(key_hash: str):
        """Get API key data from cache."""
        data = redis_client.get(f"apikey:{key_hash}")
        return json.loads(data) if data else None
    
    @staticmethod
    def set_api_key(key_hash: str, key_data: dict):
        """Set API key in cache."""
        redis_client.setex(
            f"apikey:{key_hash}",
            settings.REDIS_TTL,
            json.dumps(key_data, default=str)
        )