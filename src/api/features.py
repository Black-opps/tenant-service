"""
Feature flag management endpoints.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/features", tags=["Features"])


@router.get("/")
async def list_features():
    """List all available features."""
    return {
        "features": [
            "advanced_analytics",
            "api_access",
            "webhooks",
            "custom_reports",
            "multi_user",
            "audit_logs",
            "white_label",
            "priority_support"
        ]
    }