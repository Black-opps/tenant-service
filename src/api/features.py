from fastapi import APIRouter, HTTPException, Depends
from typing import List
from uuid import UUID

router = APIRouter(prefix="/tenants/{tenant_id}/features", tags=["features"])

@router.get("/")
async def list_features(tenant_id: UUID):
    """List all features for tenant"""
    return {"tenant_id": tenant_id}

@router.post("/{feature_name}/enable")
async def enable_feature(tenant_id: UUID, feature_name: str):
    """Enable feature for tenant"""
    return {"tenant_id": tenant_id, "feature": feature_name}

@router.post("/{feature_name}/disable")
async def disable_feature(tenant_id: UUID, feature_name: str):
    """Disable feature for tenant"""
    return {"tenant_id": tenant_id, "feature": feature_name}

@router.get("/limits")
async def get_limits(tenant_id: UUID):
    """Get tenant limits"""
    return {"tenant_id": tenant_id}
