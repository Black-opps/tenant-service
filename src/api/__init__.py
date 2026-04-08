"""
API module for tenant service.
"""
from .tenants import router as tenants_router
from .users import router as users_router
from .roles import router as roles_router
from .features import router as features_router
from .invitations import router as invitations_router

__all__ = [
    "tenants_router",
    "users_router",
    "roles_router",
    "features_router",
    "invitations_router"
]