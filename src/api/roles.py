"""
Role management endpoints.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("/")
async def list_roles():
    """List all roles."""
    return {"roles": ["admin", "manager", "analyst", "viewer"]}