"""
Tenant API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..core.database import get_db
from ..core.security import get_current_user, require_permission
from ..services.tenant_manager import TenantManager
from ..models.organization import TenantTier, TenantStatus
from ..models.user import User
from ..schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
    TenantUpgrade,
    TenantUsageResponse
)

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("/", response_model=TenantResponse, status_code=201)
async def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new tenant organization.
    
    This endpoint creates a new tenant with trial status.
    Only super admins can create tenants.
    """
    # Check permission
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Only super admins can create tenants")
    
    manager = TenantManager(db)
    tenant = manager.create_tenant(**tenant_data.dict())
    
    return tenant


@router.get("/", response_model=List[TenantListResponse])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[TenantStatus] = None,
    tier: Optional[TenantTier] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all tenants with optional filters.
    
    Only super admins can list all tenants.
    """
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Only super admins can list all tenants")
    
    manager = TenantManager(db)
    tenants = manager.list_tenants(skip=skip, limit=limit, status=status, tier=tier)
    
    return tenants


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID = Path(..., description="Tenant UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get tenant details by ID.
    
    Users can only access their own tenant unless super admin.
    """
    # Check access
    if current_user.tenant_id != tenant_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    manager = TenantManager(db)
    tenant = manager.get_tenant(tenant_id)
    
    return tenant


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    tenant_data: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update tenant details.
    
    Only tenant admins or super admins can update.
    """
    # Check permission
    if current_user.tenant_id != tenant_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if current_user.role != "admin" and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    manager = TenantManager(db)
    tenant = manager.update_tenant(tenant_id, **tenant_data.dict(exclude_unset=True))
    
    return tenant


@router.delete("/{tenant_id}", status_code=204)
async def delete_tenant(
    tenant_id: UUID,
    hard_delete: bool = Query(False, description="Hard delete (permanent)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a tenant.
    
    Only super admins can delete tenants.
    Hard delete permanently removes data.
    """
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Only super admins can delete tenants")
    
    manager = TenantManager(db)
    manager.delete_tenant(tenant_id, soft_delete=not hard_delete)
    
    return None


@router.post("/{tenant_id}/upgrade", response_model=TenantResponse)
async def upgrade_tenant(
    tenant_id: UUID,
    upgrade_data: TenantUpgrade,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upgrade tenant to a new tier.
    
    Only tenant admins or super admins can upgrade.
    """
    # Check permission
    if current_user.tenant_id != tenant_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if current_user.role != "admin" and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    manager = TenantManager(db)
    tenant = manager.upgrade_tenant_tier(tenant_id, upgrade_data.tier)
    
    return tenant


@router.post("/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: UUID,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Suspend a tenant.
    
    Only super admins can suspend tenants.
    """
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Only super admins can suspend tenants")
    
    manager = TenantManager(db)
    manager.suspend_tenant(tenant_id, reason)
    
    return {"message": "Tenant suspended successfully"}


@router.post("/{tenant_id}/activate")
async def activate_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Activate a suspended tenant.
    
    Only super admins can activate tenants.
    """
    if not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Only super admins can activate tenants")
    
    manager = TenantManager(db)
    manager.activate_tenant(tenant_id)
    
    return {"message": "Tenant activated successfully"}


@router.get("/{tenant_id}/usage", response_model=TenantUsageResponse)
async def get_tenant_usage(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get tenant usage statistics.
    
    Users can only access their own tenant's usage.
    """
    # Check access
    if current_user.tenant_id != tenant_id and not current_user.is_super_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    manager = TenantManager(db)
    usage = manager.get_tenant_usage(tenant_id)
    
    return usage


@router.get("/by-slug/{slug}", response_model=TenantResponse)
async def get_tenant_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Get tenant by slug (public info).
    
    Public endpoint for tenant lookup by slug.
    """
    manager = TenantManager(db)
    tenant = manager.get_tenant_by_slug(slug)
    
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return tenant