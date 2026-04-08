from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INVITED = "invited"
    DISABLED = "disabled"


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: UserRole = UserRole.VIEWER


class UserCreate(UserBase):
    password: Optional[str] = None


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class UserInvite(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.VIEWER
    permissions: Optional[List[str]] = []


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class UserResponse(UserBase):
    id: UUID
    tenant_id: UUID
    status: UserStatus
    permissions: List[str]
    mfa_enabled: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    verified: bool
    preferences: dict
    full_name: str

    class Config:
        orm_mode = True


class UserListResponse(BaseModel):
    id: UUID
    email: EmailStr
    first_name: str
    last_name: str
    full_name: str
    role: UserRole
    status: UserStatus
    created_at: datetime


class UserStatsResponse(BaseModel):
    total: int
    by_role: dict
    by_status: dict
    active: int
    invited: int