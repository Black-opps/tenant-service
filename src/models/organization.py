"""
Organization (Tenant) model.
"""
from sqlalchemy import Column, String, DateTime, Boolean, JSON, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timedelta
import enum

from ..core.database import Base


class TenantTier(str, enum.Enum):
    """Tenant subscription tiers."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantStatus(str, enum.Enum):
    """Tenant status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Organization(Base):
    """Organization/Tenant model."""
    
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    tier = Column(Enum(TenantTier), default=TenantTier.TRIAL, nullable=False)
    status = Column(Enum(TenantStatus), default=TenantStatus.TRIAL, nullable=False)
    
    # Contact info
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50))
    address = Column(JSON)  # Structured address
    
    # Configuration
    settings = Column(JSON, default=dict)
    features = Column(JSON, default=dict)  # Enabled features
    
    # M-PESA Configuration
    paybill_numbers = Column(JSON, default=list)
    till_numbers = Column(JSON, default=list)
    business_shortcodes = Column(JSON, default=list)
    
    # Limits
    max_users = Column(Integer, default=1)
    max_transactions = Column(Integer, default=100)
    retention_days = Column(Integer, default=7)
    max_storage_mb = Column(Integer, default=100)
    
    # Billing
    subscription_id = Column(UUID(as_uuid=True), nullable=True)
    billing_email = Column(String(255))
    tax_id = Column(String(100))
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    trial_ends_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=14))
    activated_at = Column(DateTime, nullable=True)
    suspended_at = Column(DateTime, nullable=True)
    
    # Metadata
    metadata = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    
    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="organization", cascade="all, delete-orphan")
    invitations = relationship("Invitation", back_populates="organization", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Organization {self.name} ({self.tier.value})>"
    
    @property
    def is_active(self) -> bool:
        """Check if tenant is active."""
        return self.status == TenantStatus.ACTIVE
    
    @property
    def is_trial(self) -> bool:
        """Check if tenant is in trial."""
        return self.status == TenantStatus.TRIAL
    
    @property
    def trial_days_left(self) -> int:
        """Get days left in trial."""
        if not self.trial_ends_at:
            return 0
        delta = self.trial_ends_at - datetime.utcnow()
        return max(0, delta.days)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "tier": self.tier.value,
            "status": self.status.value,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "settings": self.settings,
            "features": self.features,
            "paybill_numbers": self.paybill_numbers,
            "max_users": self.max_users,
            "max_transactions": self.max_transactions,
            "retention_days": self.retention_days,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "trial_days_left": self.trial_days_left
        }