"""
Tenant management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import re

from ..core.database import get_db, Tenant

router = APIRouter(prefix="/tenants", tags=["Tenants"])


# Request/Response Models
class TenantCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    tier: str = "free"


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    tier: Optional[str] = None
    status: Optional[str] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    email: str
    phone: Optional[str]
    tier: str
    status: str
    max_users: int
    max_transactions: int
    created_at: str


def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from name."""
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


@router.post("/", response_model=TenantResponse)
async def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    """Create a new tenant."""
    slug = generate_slug(tenant.name)
    
    # Check if slug exists
    existing = db.query(Tenant).filter(Tenant.slug == slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tenant with similar name already exists")
    
    db_tenant = Tenant(
        name=tenant.name,
        slug=slug,
        email=tenant.email,
        phone=tenant.phone,
        tier=tenant.tier
    )
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    
    # Convert to dict with string dates
    return {
        "id": db_tenant.id,
        "name": db_tenant.name,
        "slug": db_tenant.slug,
        "email": db_tenant.email,
        "phone": db_tenant.phone,
        "tier": db_tenant.tier,
        "status": db_tenant.status,
        "max_users": db_tenant.max_users,
        "max_transactions": db_tenant.max_transactions,
        "created_at": db_tenant.created_at.isoformat() if db_tenant.created_at else None
    }

@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all tenants."""
    tenants = db.query(Tenant).offset(skip).limit(limit).all()
    
    # Convert to dict with string dates
    return [
        {
            "id": t.id,
            "name": t.name,
            "slug": t.slug,
            "email": t.email,
            "phone": t.phone,
            "tier": t.tier,
            "status": t.status,
            "max_users": t.max_users,
            "max_transactions": t.max_transactions,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in tenants
    ]


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """Get tenant by ID."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "email": tenant.email,
        "phone": tenant.phone,
        "tier": tenant.tier,
        "status": tenant.status,
        "max_users": tenant.max_users,
        "max_transactions": tenant.max_transactions,
        "created_at": tenant.created_at.isoformat() if tenant.created_at else None
    }


@router.get("/slug/{slug}", response_model=TenantResponse)
async def get_tenant_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get tenant by slug."""
    tenant = db.query(Tenant).filter(Tenant.slug == slug).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "email": tenant.email,
        "phone": tenant.phone,
        "tier": tenant.tier,
        "status": tenant.status,
        "max_users": tenant.max_users,
        "max_transactions": tenant.max_transactions,
        "created_at": tenant.created_at.isoformat() if tenant.created_at else None
    }


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, tenant: TenantUpdate, db: Session = Depends(get_db)):
    """Update tenant."""
    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    for key, value in tenant.dict(exclude_unset=True).items():
        setattr(db_tenant, key, value)
    
    db.commit()
    db.refresh(db_tenant)
    
    return {
        "id": db_tenant.id,
        "name": db_tenant.name,
        "slug": db_tenant.slug,
        "email": db_tenant.email,
        "phone": db_tenant.phone,
        "tier": db_tenant.tier,
        "status": db_tenant.status,
        "max_users": db_tenant.max_users,
        "max_transactions": db_tenant.max_transactions,
        "created_at": db_tenant.created_at.isoformat() if db_tenant.created_at else None
    }


@router.delete("/{tenant_id}")
async def delete_tenant(tenant_id: str, db: Session = Depends(get_db)):
    """Delete tenant."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    db.delete(tenant)
    db.commit()
    return {"message": "Tenant deleted"}