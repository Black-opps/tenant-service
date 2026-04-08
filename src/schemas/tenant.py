from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class TenantTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class TenantBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    tier: TenantTier = TenantTier.TRIAL


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    settings: Optional[Dict] = None


class TenantUpgrade(BaseModel):
    tier: TenantTier


class TenantResponse(TenantBase):
    id: UUID
    slug: str
    status: TenantStatus
    settings: Dict
    features: Dict
    max_users: int
    max_transactions: int
    retention_days: int
    created_at: datetime
    trial_ends_at: Optional[datetime] = None
    trial_days_left: int

    class Config:
        orm_mode = True


class TenantListResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    tier: TenantTier
    status: TenantStatus
    email: EmailStr
    created_at: datetime


class TenantUsageResponse(BaseModel):
    tenant_id: UUID
    name: str
    tier: str
    status: str
    users: Dict
    transactions: Dict
    storage: Dict
    retention_days: int
    trial_days_left: int