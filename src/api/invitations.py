"""
Invitation management endpoints.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/invitations", tags=["Invitations"])


@router.post("/")
async def create_invitation():
    """Create an invitation."""
    return {"message": "Invitation created"}


@router.get("/")
async def list_invitations():
    """List invitations."""
    return {"invitations": []}