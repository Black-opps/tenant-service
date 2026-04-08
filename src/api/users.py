"""
User management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid

from ..core.database import get_db, Tenant, User

router = APIRouter(prefix="/tenants/{tenant_id}/users", tags=["Users"])


class UserCreate(BaseModel):
    email: str
    full_name: str
    role: str = "viewer"


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    tenant_id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: str


@router.get("/", response_model=List[UserResponse])
async def list_users(tenant_id: str, db: Session = Depends(get_db)):
    """List users in a tenant."""
    # Check if tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    users = db.query(User).filter(User.tenant_id == tenant_id).all()
    
    # Convert to dict with string dates
    return [
        {
            "id": u.id,
            "tenant_id": u.tenant_id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None
        }
        for u in users
    ]


@router.post("/", response_model=UserResponse)
async def create_user(tenant_id: str, user: UserCreate, db: Session = Depends(get_db)):
    """Create a user in a tenant."""
    # Check if tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Check if user already exists
    existing = db.query(User).filter(
        User.tenant_id == tenant_id,
        User.email == user.email
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists in this tenant")
    
    db_user = User(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return {
        "id": db_user.id,
        "tenant_id": db_user.tenant_id,
        "email": db_user.email,
        "full_name": db_user.full_name,
        "role": db_user.role,
        "is_active": db_user.is_active,
        "created_at": db_user.created_at.isoformat() if db_user.created_at else None
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(tenant_id: str, user_id: str, db: Session = Depends(get_db)):
    """Get a user by ID."""
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(tenant_id: str, user_id: str, user: UserUpdate, db: Session = Depends(get_db)):
    """Update a user."""
    db_user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant_id
    ).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user.dict(exclude_unset=True).items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    
    return {
        "id": db_user.id,
        "tenant_id": db_user.tenant_id,
        "email": db_user.email,
        "full_name": db_user.full_name,
        "role": db_user.role,
        "is_active": db_user.is_active,
        "created_at": db_user.created_at.isoformat() if db_user.created_at else None
    }


@router.delete("/{user_id}")
async def delete_user(tenant_id: str, user_id: str, db: Session = Depends(get_db)):
    """Delete a user."""
    user = db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant_id
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}