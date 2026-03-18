"""
Tenant management service.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import logging
from uuid import UUID

from ..models.organization import Organization, TenantTier, TenantStatus
from ..models.user import User, UserRole, UserStatus
from ..models.feature import Feature, FeatureName, FEATURE_TIER_MATRIX
from ..core.exceptions import (
    TenantNotFoundError, TenantAlreadyExistsError,
    TenantLimitExceededError, TenantInactiveError
)
from ..core.security import generate_org_slug
from ..core.database import TenantCache
from ..services.user_manager import UserManager

logger = logging.getLogger(__name__)


class TenantManager:
    """Manager for tenant operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_manager = UserManager(db)
        self.cache = TenantCache()
    
    def create_tenant(
        self,
        name: str,
        email: str,
        phone: Optional[str] = None,
        tier: TenantTier = TenantTier.TRIAL,
        **kwargs
    ) -> Organization:
        """
        Create a new tenant organization.
        
        Args:
            name: Organization name
            email: Admin email
            phone: Contact phone
            tier: Subscription tier
            **kwargs: Additional fields
            
        Returns:
            Created organization
        """
        # Check if tenant already exists
        existing = self.db.query(Organization).filter(
            or_(
                Organization.email == email,
                Organization.slug == generate_org_slug(name)
            )
        ).first()
        
        if existing:
            raise TenantAlreadyExistsError(email)
        
        # Create tenant
        tenant = Organization(
            name=name,
            slug=generate_org_slug(name),
            email=email,
            phone=phone,
            tier=tier,
            status=TenantStatus.TRIAL if tier == TenantTier.TRIAL else TenantStatus.ACTIVE,
            trial_ends_at=datetime.utcnow() + timedelta(days=14) if tier == TenantTier.TRIAL else None,
            **kwargs
        )
        
        # Set limits based on tier
        self._apply_tier_limits(tenant)
        
        self.db.add(tenant)
        self.db.flush()
        
        # Create default roles
        self._create_default_roles(tenant.id)
        
        # Enable default features
        self._enable_default_features(tenant.id, tier)
        
        logger.info(f"Created tenant: {tenant.name} ({tenant.id})")
        
        return tenant
    
    def get_tenant(self, tenant_id: UUID) -> Organization:
        """
        Get tenant by ID.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Organization
            
        Raises:
            TenantNotFoundError: If tenant doesn't exist
        """
        # Try cache first
        cached = self.cache.get_tenant(str(tenant_id))
        if cached:
            # Convert cached dict to Organization (simplified)
            return cached
        
        tenant = self.db.query(Organization).filter(
            Organization.id == tenant_id
        ).first()
        
        if not tenant:
            raise TenantNotFoundError(str(tenant_id))
        
        # Cache for next time
        self.cache.set_tenant(str(tenant_id), tenant.to_dict())
        
        return tenant
    
    def get_tenant_by_slug(self, slug: str) -> Optional[Organization]:
        """Get tenant by slug."""
        return self.db.query(Organization).filter(
            Organization.slug == slug
        ).first()
    
    def get_tenant_by_email(self, email: str) -> Optional[Organization]:
        """Get tenant by email."""
        return self.db.query(Organization).filter(
            Organization.email == email
        ).first()
    
    def update_tenant(self, tenant_id: UUID, **kwargs) -> Organization:
        """
        Update tenant.
        
        Args:
            tenant_id: Tenant UUID
            **kwargs: Fields to update
            
        Returns:
            Updated organization
        """
        tenant = self.get_tenant(tenant_id)
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(tenant, key) and value is not None:
                setattr(tenant, key, value)
        
        tenant.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Invalidate cache
        self.cache.invalidate_tenant(str(tenant_id))
        
        logger.info(f"Updated tenant: {tenant.id}")
        
        return tenant
    
    def delete_tenant(self, tenant_id: UUID, soft_delete: bool = True):
        """
        Delete tenant.
        
        Args:
            tenant_id: Tenant UUID
            soft_delete: If True, mark as deleted instead of removing
        """
        tenant = self.get_tenant(tenant_id)
        
        if soft_delete:
            tenant.status = TenantStatus.CANCELLED
            tenant.deleted_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Soft deleted tenant: {tenant_id}")
        else:
            self.db.delete(tenant)
            self.db.commit()
            logger.info(f"Hard deleted tenant: {tenant_id}")
        
        # Invalidate cache
        self.cache.invalidate_tenant(str(tenant_id))
    
    def upgrade_tenant_tier(self, tenant_id: UUID, new_tier: TenantTier) -> Organization:
        """
        Upgrade tenant to new tier.
        
        Args:
            tenant_id: Tenant UUID
            new_tier: New subscription tier
            
        Returns:
            Updated organization
        """
        tenant = self.get_tenant(tenant_id)
        
        old_tier = tenant.tier
        tenant.tier = new_tier
        tenant.status = TenantStatus.ACTIVE
        
        # Update limits for new tier
        self._apply_tier_limits(tenant)
        
        # Update features
        self._update_features_for_tier(tenant_id, new_tier)
        
        self.db.commit()
        self.cache.invalidate_tenant(str(tenant_id))
        
        logger.info(f"Upgraded tenant {tenant_id} from {old_tier} to {new_tier}")
        
        return tenant
    
    def suspend_tenant(self, tenant_id: UUID, reason: str = None):
        """Suspend tenant."""
        tenant = self.get_tenant(tenant_id)
        tenant.status = TenantStatus.SUSPENDED
        tenant.suspended_at = datetime.utcnow()
        tenant.metadata["suspension_reason"] = reason
        
        self.db.commit()
        self.cache.invalidate_tenant(str(tenant_id))
        
        logger.warning(f"Suspended tenant: {tenant_id} - {reason}")
    
    def activate_tenant(self, tenant_id: UUID):
        """Activate suspended tenant."""
        tenant = self.get_tenant(tenant_id)
        tenant.status = TenantStatus.ACTIVE
        tenant.suspended_at = None
        tenant.activated_at = datetime.utcnow()
        
        self.db.commit()
        self.cache.invalidate_tenant(str(tenant_id))
        
        logger.info(f"Activated tenant: {tenant_id}")
    
    def check_tenant_limit(
        self,
        tenant_id: UUID,
        limit_type: str,
        increment: int = 1
    ) -> bool:
        """
        Check if tenant has reached a limit.
        
        Args:
            tenant_id: Tenant UUID
            limit_type: Type of limit (users, transactions, storage)
            increment: Amount to increment
            
        Returns:
            True if under limit, False if exceeded
            
        Raises:
            TenantLimitExceededError: If limit exceeded
        """
        tenant = self.get_tenant(tenant_id)
        
        if tenant.status != TenantStatus.ACTIVE:
            raise TenantInactiveError(str(tenant_id))
        
        current = getattr(tenant, f"current_{limit_type}", 0)
        max_allowed = getattr(tenant, f"max_{limit_type}", 0)
        
        if current + increment > max_allowed:
            raise TenantLimitExceededError(limit_type, current + increment, max_allowed)
        
        return True
    
    def get_tenant_usage(self, tenant_id: UUID) -> Dict:
        """
        Get tenant usage statistics.
        
        Args:
            tenant_id: Tenant UUID
            
        Returns:
            Usage statistics dictionary
        """
        tenant = self.get_tenant(tenant_id)
        
        # Count users
        user_count = self.db.query(User).filter(
            User.tenant_id == tenant_id,
            User.status == UserStatus.ACTIVE
        ).count()
        
        # TODO: Get transaction count from analytics service
        transaction_count = 0
        
        return {
            "tenant_id": str(tenant_id),
            "name": tenant.name,
            "tier": tenant.tier.value,
            "status": tenant.status.value,
            "users": {
                "current": user_count,
                "limit": tenant.max_users,
                "percentage": (user_count / tenant.max_users) * 100 if tenant.max_users else 0
            },
            "transactions": {
                "current": transaction_count,
                "limit": tenant.max_transactions,
                "percentage": (transaction_count / tenant.max_transactions) * 100 if tenant.max_transactions else 0
            },
            "storage": {
                "current_mb": 0,
                "limit_mb": tenant.max_storage_mb,
                "percentage": 0
            },
            "retention_days": tenant.retention_days,
            "trial_days_left": tenant.trial_days_left
        }
    
    def list_tenants(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[TenantStatus] = None,
        tier: Optional[TenantTier] = None
    ) -> List[Organization]:
        """List tenants with filters."""
        query = self.db.query(Organization)
        
        if status:
            query = query.filter(Organization.status == status)
        
        if tier:
            query = query.filter(Organization.tier == tier)
        
        return query.offset(skip).limit(limit).all()
    
    def _apply_tier_limits(self, tenant: Organization):
        """Apply limits based on tier."""
        limits = {
            TenantTier.FREE: {
                "max_users": 1,
                "max_transactions": 100,
                "retention_days": 7,
                "max_storage_mb": 100
            },
            TenantTier.STARTER: {
                "max_users": 3,
                "max_transactions": 5000,
                "retention_days": 30,
                "max_storage_mb": 500
            },
            TenantTier.PROFESSIONAL: {
                "max_users": 10,
                "max_transactions": 50000,
                "retention_days": 365,
                "max_storage_mb": 2000
            },
            TenantTier.ENTERPRISE: {
                "max_users": 999,
                "max_transactions": 999999,
                "retention_days": 2555,  # 7 years
                "max_storage_mb": 10000
            }
        }
        
        tier_limits = limits.get(tenant.tier, limits[TenantTier.FREE])
        
        tenant.max_users = tier_limits["max_users"]
        tenant.max_transactions = tier_limits["max_transactions"]
        tenant.retention_days = tier_limits["retention_days"]
        tenant.max_storage_mb = tier_limits["max_storage_mb"]
    
    def _create_default_roles(self, tenant_id: UUID):
        """Create default roles for new tenant."""
        from ..models.role import Role, SYSTEM_ROLES
        
        for role_key, role_data in SYSTEM_ROLES.items():
            role = Role(
                tenant_id=tenant_id,
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
                is_default=(role_key == "viewer"),
                is_system=True
            )
            self.db.add(role)
        
        self.db.flush()
    
    def _enable_default_features(self, tenant_id: UUID, tier: TenantTier):
        """Enable features based on tier."""
        from ..models.feature import Feature, FeatureName, FEATURE_TIER_MATRIX
        
        for feature_name, allowed_tiers in FEATURE_TIER_MATRIX.items():
            if tier.value in allowed_tiers:
                feature = Feature(
                    tenant_id=tenant_id,
                    name=feature_name,
                    enabled=True
                )
                self.db.add(feature)
        
        self.db.flush()
    
    def _update_features_for_tier(self, tenant_id: UUID, new_tier: TenantTier):
        """Update features when tier changes."""
        from ..models.feature import Feature, FeatureName, FEATURE_TIER_MATRIX
        
        # Get current features
        current_features = self.db.query(Feature).filter(
            Feature.tenant_id == tenant_id
        ).all()
        
        current_feature_names = {f.name for f in current_features}
        
        # Add new features for new tier
        for feature_name, allowed_tiers in FEATURE_TIER_MATRIX.items():
            if new_tier.value in allowed_tiers:
                if feature_name not in current_feature_names:
                    feature = Feature(
                        tenant_id=tenant_id,
                        name=feature_name,
                        enabled=True
                    )
                    self.db.add(feature)
                else:
                    # Update existing feature
                    self.db.query(Feature).filter(
                        Feature.tenant_id == tenant_id,
                        Feature.name == feature_name
                    ).update({"enabled": True})
        
        self.db.flush()