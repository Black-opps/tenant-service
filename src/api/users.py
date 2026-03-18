"""
User management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..core.database import get_db
from ..core.security import get_current_user, require_permission
from ..services.user_manager import UserManager
from ..services.invitation_service import InvitationService
from ..models.user import User, UserRole, UserStatus
from ..schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    UserInvite,
    PasswordChange,
    UserStatsResponse
)

router = APIRouter(prefix="/tenants/{tenant_id}/users", tags=["users"])


@router.get("/", response_model=List[UserListResponse])
async def list_users(
    tenant_id: UUID = Path(..., description="Tenant UUID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List users in tenant.
    
    Users can list users in their own tenant.
    """
    # Check access
    if current_user.tenant_id != tenant_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    manager = UserManager(db)
    users = manager.list_users(
        tenant_id=tenant_id,
        skip=skip,
        limit=limit,
        role=role,
        status=status
    )
    
    return users


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    tenant_id: UUID,
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("create:users"))
):
    """
    Create a new user in tenant.
    
    Requires create:users permission.
    """
    # Check tenant access
    if current_user.tenant_id != tenant_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    manager = UserManager(db)
    user = manager.create_user(
        tenant_id=tenant_id,
        invited_by=current_user.id,
        **user_data.dict()
    )
    
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    tenant_id: UUID,
    user_id: UUID = Path(..., description="User UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user details.
    
    Users can access their own profile or require view:users permission.
    """
    # Check access
    if current_user.id != user_id:
        if current_user.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        if not current_user.has_permission("view:users"):
            raise HTTPException(status_code=403, detail="Permission denied")
    
    manager = UserManager(db)
    user = manager.get_user(user_id)
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    tenant_id: UUID,
    user_id: UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("update:users"))
):
    """
    Update user details.
    
    Requires update:users permission.
    """
    # Check tenant access
    if current_user.tenant_id != tenant_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    manager = UserManager(db)
    user = manager.update_user(user_id, **user_data.dict(exclude_unset=True))
    
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    tenant_id: UUID,
    user_id: UUID,
    hard_delete: bool = Query(False, description="Hard delete (permanent)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("delete:users"))
):
    """
    Delete a user.
    
    Requires delete:users permission.
    """
    # Check tenant access
    if current_user.tenant_id != tenant_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Prevent self-deletion
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    manager = UserManager(db)
    manager.delete_user(user_id, hard_delete=hard_delete)
    
    return None


@router.post("/invite", response_model=dict)
async def invite_user(
    tenant_id: UUID,
    invitation: UserInvite,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("invite:users"))
):
    """
    Invite a new user to the tenant.
    
    Sends an invitation email to the user.
    Requires invite:users permission.
    """
    # Check tenant access
    if current_user.tenant_id != tenant_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    service = InvitationService(db)
    inv = service.create_invitation(
        tenant_id=tenant_id,
        inviter_id=current_user.id,
        email=invitation.email,
        role=invitation.role,
        permissions=invitation.permissions
    )
    
    return {
        "message": f"Invitation sent to {invitation.email}",
        "invitation_id": inv.id
    }


@router.post("/{user_id}/password", status_code=204)
async def change_password(
    tenant_id: UUID,
    user_id: UUID,
    password_data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change user password.
    
    Users can change their own password.
    Admins can reset any password.
    """
    # Check access
    if current_user.id != user_id:
        if current_user.tenant_id != tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Admin reset
        manager = UserManager(db)
        manager.reset_password(user_id, password_data.new_password)
    else:
        # Self password change
        manager = UserManager(db)
        manager.change_password(
            user_id,
            password_data.old_password,
            password_data.new_password
        )
    
    return None


@router.get("/stats/overview", response_model=UserStatsResponse)
async def get_user_stats(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("view:users"))
):
    """
    Get user statistics for tenant.
    
    Requires view:users permission.
    """
    # Check tenant access
    if current_user.tenant_id != tenant_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    manager = UserManager(db)
    stats = manager.get_user_stats(tenant_id)
    
    return stats


@router.post("/{user_id}/enable-mfa")
async def enable_mfa(
    tenant_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enable MFA for user.
    
    Users can enable MFA for themselves.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only enable MFA for yourself")
    
    # Generate MFA secret
    import pyotp
    secret = pyotp.random_base32()
    
    # Store in user record
    manager = UserManager(db)
    manager.update_user(user_id, mfa_secret=secret, mfa_enabled=True)
    
    # Generate provisioning URI
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        current_user.email,
        issuer_name="M-PESA SaaS"
    )
    
    return {
        "secret": secret,
        "provisioning_uri": provisioning_uri
    }


@router.post("/{user_id}/disable-mfa")
async def disable_mfa(
    tenant_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Disable MFA for user.
    
    Users can disable MFA for themselves.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Can only disable MFA for yourself")
    
    manager = UserManager(db)
    manager.update_user(user_id, mfa_secret=None, mfa_enabled=False)
    
    return {"message": "MFA disabled"}