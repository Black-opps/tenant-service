"""
Invitation model for inviting users to tenant.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timedelta
import enum

from ..core.database import Base
from .user import UserRole


class InvitationStatus(str, enum.Enum):
    """Invitation status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Invitation(Base):
    """Invitation model."""
    
    __tablename__ = "invitations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    email = Column(String(255), nullable=False, index=True)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING, nullable=False)
    
    # Optional custom permissions
    permissions = Column(JSON, default=list)
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    accepted_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="invitations")
    inviter = relationship("User", foreign_keys=[invited_by])
    
    def __repr__(self):
        return f"<Invitation {self.email} ({self.status.value})>"
    
    @property
    def is_valid(self) -> bool:
        """Check if invitation is valid."""
        return (
            self.status == InvitationStatus.PENDING and
            self.expires_at > datetime.utcnow()
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if invitation is expired."""
        return self.expires_at <= datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "email": self.email,
            "role": self.role.value,
            "status": self.status.value,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_valid": self.is_valid
        }