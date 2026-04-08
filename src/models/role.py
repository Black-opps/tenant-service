"""
Role and permissions models.
"""
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
import enum

from ..core.database import Base
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Boolean, UniqueConstraint


class Permission(str, enum.Enum):
    """System permissions."""
    # Transaction permissions
    VIEW_TRANSACTIONS = "view:transactions"
    EXPORT_TRANSACTIONS = "export:transactions"
    DELETE_TRANSACTIONS = "delete:transactions"
    
    # Analytics permissions
    VIEW_ANALYTICS = "view:analytics"
    CREATE_REPORTS = "create:reports"
    EXPORT_REPORTS = "export:reports"
    SCHEDULE_REPORTS = "schedule:reports"
    
    # User management
    VIEW_USERS = "view:users"
    CREATE_USERS = "create:users"
    UPDATE_USERS = "update:users"
    DELETE_USERS = "delete:users"
    INVITE_USERS = "invite:users"
    
    # Role management
    VIEW_ROLES = "view:roles"
    CREATE_ROLES = "create:roles"
    UPDATE_ROLES = "update:roles"
    DELETE_ROLES = "delete:roles"
    
    # Billing
    VIEW_BILLING = "view:billing"
    MANAGE_BILLING = "manage:billing"
    VIEW_INVOICES = "view:invoices"
    
    # API
    MANAGE_API_KEYS = "manage:api_keys"
    VIEW_API_KEYS = "view:api_keys"
    CREATE_WEBHOOKS = "create:webhooks"
    
    # Settings
    VIEW_SETTINGS = "view:settings"
    MANAGE_SETTINGS = "manage:settings"
    
    # Audit
    VIEW_AUDIT_LOGS = "view:audit_logs"
    EXPORT_AUDIT_LOGS = "export:audit_logs"
    
    # Admin
    ADMIN_ALL = "admin:all"


class Role(Base):
    """Role model."""
    
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    permissions = Column(JSON, default=list)  # List of permission strings
    
    is_default = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)  # Cannot be modified
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="roles")
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'name', name='uq_role_tenant_name'),
    )
    
    def __repr__(self):
        return f"<Role {self.name}>"
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has specific permission."""
        return permission in self.permissions
    
    def has_any_permission(self, permissions: list) -> bool:
        """Check if role has any of the permissions."""
        return any(p in self.permissions for p in permissions)
    
    def has_all_permissions(self, permissions: list) -> bool:
        """Check if role has all permissions."""
        return all(p in self.permissions for p in permissions)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
            "is_default": self.is_default,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


# Predefined system roles
SYSTEM_ROLES = {
    "admin": {
        "name": "Admin",
        "description": "Full access to all features",
        "permissions": [p.value for p in Permission]
    },
    "manager": {
        "name": "Manager",
        "description": "Can manage users and view all data",
        "permissions": [
            Permission.VIEW_TRANSACTIONS.value,
            Permission.VIEW_ANALYTICS.value,
            Permission.CREATE_REPORTS.value,
            Permission.VIEW_USERS.value,
            Permission.CREATE_USERS.value,
            Permission.UPDATE_USERS.value,
            Permission.VIEW_BILLING.value,
            Permission.VIEW_SETTINGS.value
        ]
    },
    "analyst": {
        "name": "Analyst",
        "description": "Can view and analyze data",
        "permissions": [
            Permission.VIEW_TRANSACTIONS.value,
            Permission.VIEW_ANALYTICS.value,
            Permission.CREATE_REPORTS.value,
            Permission.EXPORT_REPORTS.value
        ]
    },
    "viewer": {
        "name": "Viewer",
        "description": "Read-only access",
        "permissions": [
            Permission.VIEW_TRANSACTIONS.value,
            Permission.VIEW_ANALYTICS.value
        ]
    }
}