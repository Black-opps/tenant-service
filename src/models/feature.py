"""
Feature flag models for tenant service.
"""
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum
from sqlalchemy import Integer, UniqueConstraint
from sqlalchemy.types import JSON   # or from sqlalchemy.dialects.postgresql import JSONB if using PG JSONB
from ..core.database import Base


class FeatureName(str, enum.Enum):
    """Available features."""
    ADVANCED_ANALYTICS = "advanced_analytics"
    API_ACCESS = "api_access"
    WEBHOOKS = "webhooks"
    CUSTOM_REPORTS = "custom_reports"
    DATA_EXPORT = "data_export"
    MULTI_USER = "multi_user"
    AUDIT_LOGS = "audit_logs"
    SLA = "sla"
    WHITE_LABEL = "white_label"
    PRIORITY_SUPPORT = "priority_support"
    REAL_TIME_ALERTS = "real_time_alerts"
    DATA_RETENTION_1Y = "data_retention_1y"
    DATA_RETENTION_7Y = "data_retention_7y"


class Feature(Base):
    """Feature flag model."""
    
    __tablename__ = "features"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=False)
    config = Column(JSON, default=dict)  # Feature-specific configuration
    
    # Limits for this feature
    limits = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_feature_tenant_name'),
    )
    
    def __repr__(self):
        return f"<Feature {self.name}: {self.enabled}>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "name": self.name,
            "enabled": self.enabled,
            "config": self.config,
            "limits": self.limits,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


# Feature definitions with tier access
FEATURE_TIER_MATRIX = {
    FeatureName.ADVANCED_ANALYTICS.value: ["professional", "enterprise"],
    FeatureName.API_ACCESS.value: ["professional", "enterprise"],
    FeatureName.WEBHOOKS.value: ["professional", "enterprise"],
    FeatureName.CUSTOM_REPORTS.value: ["starter", "professional", "enterprise"],
    FeatureName.DATA_EXPORT.value: ["starter", "professional", "enterprise"],
    FeatureName.MULTI_USER.value: ["starter", "professional", "enterprise"],
    FeatureName.AUDIT_LOGS.value: ["professional", "enterprise"],
    FeatureName.SLA.value: ["enterprise"],
    FeatureName.WHITE_LABEL.value: ["enterprise"],
    FeatureName.PRIORITY_SUPPORT.value: ["professional", "enterprise"],
    FeatureName.REAL_TIME_ALERTS.value: ["professional", "enterprise"],
    FeatureName.DATA_RETENTION_1Y.value: ["professional", "enterprise"],
    FeatureName.DATA_RETENTION_7Y.value: ["enterprise"],
}