"""
User model for tenant service.
"""
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum
from sqlalchemy import Integer, UniqueConstraint
from sqlalchemy.types import JSON   # or from sqlalchemy.dialects.postgresql import JSONB if using PG JSONB

from ..core.database import Base
from ..core.security import get_password_hash


class UserRole(str, enum.Enum):
    """User roles within tenant."""
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API = "api"  # Service account


class UserStatus(str, enum.Enum):
    """User status."""
    ACTIVE = "active"
    INVITED = "invited"
    DISABLED = "disabled"
    DELETED = "deleted"


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Basic info
    email = Column(String(255), nullable=False, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    # Authentication
    password_hash = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.INVITED, nullable=False)
    
    # Permissions (overrides role if needed)
    permissions = Column(JSON, default=list)
    
    # Security
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(255), nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(50), nullable=True)
    login_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    invited_by = Column(UUID(as_uuid=True), nullable=True)
    invited_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    
    # Preferences
    preferences = Column(JSON, default=dict)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'email', name='uq_user_tenant_email'),
    )
    
    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"
    
    @property
    def full_name(self) -> str:
        """Get full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_active(self) -> bool:
        """Check if user is active."""
        return self.status == UserStatus.ACTIVE
    
    def set_password(self, password: str):
        """Set password hash."""
        self.password_hash = get_password_hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify password."""
        from ..core.security import verify_password
        return verify_password(password, self.password_hash)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "role": self.role.value,
            "status": self.status.value,
            "permissions": self.permissions,
            "mfa_enabled": self.mfa_enabled,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "verified": self.verified_at is not None,
            "preferences": self.preferences
        }