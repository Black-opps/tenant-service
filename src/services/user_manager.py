"""
User management service.
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from datetime import datetime
import logging
from uuid import UUID

from ..models.user import User, UserRole, UserStatus
from ..models.organization import Organization
from ..models.invitation import Invitation, InvitationStatus
from ..core.exceptions import UserNotFoundError, UserAlreadyExistsError, PermissionDeniedError
from ..core.security import get_password_hash, generate_invitation_token
from ..services.tenant_manager import TenantManager

logger = logging.getLogger(__name__)


class UserManager:
    """Manager for user operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.tenant_manager = TenantManager(db)
    
    def create_user(
        self,
        tenant_id: UUID,
        email: str,
        first_name: str,
        last_name: str,
        role: UserRole = UserRole.VIEWER,
        password: Optional[str] = None,
        invited_by: Optional[UUID] = None,
        **kwargs
    ) -> User:
        """
        Create a new user.
        
        Args:
            tenant_id: Tenant UUID
            email: User email
            first_name: First name
            last_name: Last name
            role: User role
            password: Optional password (if not provided, user will need to set via invitation)
            invited_by: Who invited this user
            **kwargs: Additional fields
            
        Returns:
            Created user
            
        Raises:
            UserAlreadyExistsError: If user exists
            TenantLimitExceededError: If tenant user limit reached
        """
        # Check tenant limit
        self.tenant_manager.check_tenant_limit(tenant_id, "users")
        
        # Check if user exists
        existing = self.db.query(User).filter(
            User.tenant_id == tenant_id,
            User.email == email
        ).first()
        
        if existing:
            raise UserAlreadyExistsError(email)
        
        # Create user
        user = User(
            tenant_id=tenant_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            status=UserStatus.ACTIVE if password else UserStatus.INVITED,
            invited_by=invited_by,
            invited_at=datetime.utcnow() if not password else None,
            **kwargs
        )
        
        if password:
            user.set_password(password)
            user.verified_at = datetime.utcnow()
        
        self.db.add(user)
        self.db.flush()
        
        logger.info(f"Created user: {user.email} for tenant {tenant_id}")
        
        return user
    
    def get_user(self, user_id: UUID) -> User:
        """
        Get user by ID.
        
        Args:
            user_id: User UUID
            
        Returns:
            User
            
        Raises:
            UserNotFoundError: If user doesn't exist
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise UserNotFoundError(str(user_id))
        
        return user
    
    def get_user_by_email(self, tenant_id: UUID, email: str) -> Optional[User]:
        """Get user by email within tenant."""
        return self.db.query(User).filter(
            User.tenant_id == tenant_id,
            User.email == email
        ).first()
    
    def update_user(self, user_id: UUID, **kwargs) -> User:
        """
        Update user.
        
        Args:
            user_id: User UUID
            **kwargs: Fields to update
            
        Returns:
            Updated user
        """
        user = self.get_user(user_id)
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Updated user: {user_id}")
        
        return user
    
    def delete_user(self, user_id: UUID, hard_delete: bool = False):
        """
        Delete user.
        
        Args:
            user_id: User UUID
            hard_delete: If True, remove from database
        """
        user = self.get_user(user_id)
        
        if hard_delete:
            self.db.delete(user)
            logger.info(f"Hard deleted user: {user_id}")
        else:
            user.status = UserStatus.DELETED
            user.deleted_at = datetime.utcnow()
            logger.info(f"Soft deleted user: {user_id}")
        
        self.db.commit()
    
    def list_users(
        self,
        tenant_id: UUID,
        skip: int = 0,
        limit: int = 100,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None
    ) -> List[User]:
        """List users in tenant."""
        query = self.db.query(User).filter(User.tenant_id == tenant_id)
        
        if role:
            query = query.filter(User.role == role)
        
        if status:
            query = query.filter(User.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user by email and password.
        
        Args:
            email: User email
            password: Plain password
            
        Returns:
            User if authentication successful
        """
        user = self.db.query(User).filter(User.email == email).first()
        
        if not user:
            return None
        
        if not user.verify_password(password):
            return None
        
        if user.status != UserStatus.ACTIVE:
            return None
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        user.login_count += 1
        self.db.commit()
        
        return user
    
    def change_password(self, user_id: UUID, old_password: str, new_password: str) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User UUID
            old_password: Current password
            new_password: New password
            
        Returns:
            True if successful
            
        Raises:
            PermissionDeniedError: If old password is incorrect
        """
        user = self.get_user(user_id)
        
        if not user.verify_password(old_password):
            raise PermissionDeniedError("Invalid current password")
        
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Password changed for user: {user_id}")
        
        return True
    
    def reset_password(self, user_id: UUID, new_password: str):
        """Reset user password (admin function)."""
        user = self.get_user(user_id)
        user.set_password(new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Password reset for user: {user_id}")
    
    def update_last_login(self, user_id: UUID, ip_address: str = None):
        """Update last login timestamp."""
        user = self.get_user(user_id)
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip_address
        user.login_count += 1
        self.db.commit()
    
    def check_permission(self, user_id: UUID, required_permission: str) -> bool:
        """
        Check if user has specific permission.
        
        Args:
            user_id: User UUID
            required_permission: Permission to check
            
        Returns:
            True if user has permission
        """
        user = self.get_user(user_id)
        
        # Admin has all permissions
        if user.role == UserRole.ADMIN:
            return True
        
        # Check role-based permissions
        from ..models.role import SYSTEM_ROLES
        
        role_permissions = SYSTEM_ROLES.get(user.role.value, {}).get("permissions", [])
        
        # Check custom permissions
        all_permissions = role_permissions + user.permissions
        
        return required_permission in all_permissions
    
    def get_user_stats(self, tenant_id: UUID) -> Dict:
        """Get user statistics for tenant."""
        total = self.db.query(User).filter(User.tenant_id == tenant_id).count()
        
        by_role = {}
        for role in UserRole:
            count = self.db.query(User).filter(
                User.tenant_id == tenant_id,
                User.role == role
            ).count()
            if count > 0:
                by_role[role.value] = count
        
        by_status = {}
        for status in UserStatus:
            count = self.db.query(User).filter(
                User.tenant_id == tenant_id,
                User.status == status
            ).count()
            if count > 0:
                by_status[status.value] = count
        
        return {
            "total": total,
            "by_role": by_role,
            "by_status": by_status,
            "active": by_status.get(UserStatus.ACTIVE.value, 0),
            "invited": by_status.get(UserStatus.INVITED.value, 0)
        }