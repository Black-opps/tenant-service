"""
Feature management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict

from ..core.database import get_db
from ..core.database import Tenant
from ..services.feature_service import FeatureService

router = APIRouter(prefix="/api/v1", tags=["Features"])


@router.get("/features")
async def get_all_features():
    """
    Get all available features with descriptions.
    """
    return {
        "features": FeatureService.get_all_features(),
        "count": len(FeatureService.get_all_features())
    }


@router.get("/tiers")
async def get_all_tiers():
    """
    Get all available subscription tiers.
    """
    return {
        "tiers": FeatureService.get_tiers(),
        "summary": FeatureService.get_tier_summary()
    }


@router.get("/tenants/{tenant_id}/features")
async def get_tenant_features(
    tenant_id: str,
    db: Session = Depends(get_db)
):
    """
    Get features available to a specific tenant based on their tier.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    features = FeatureService.get_tenant_features(tenant.tier)
    
    return {
        "tenant_id": tenant_id,
        "tenant_name": tenant.name,
        "tier": tenant.tier,
        "features": features,
        "feature_count": len(features)
    }


@router.get("/tenants/{tenant_id}/features/{feature_name}/check")
async def check_feature_access(
    tenant_id: str,
    feature_name: str,
    db: Session = Depends(get_db)
):
    """
    Check if a tenant has access to a specific feature.
    Useful for API Gateway authorization.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    has_access = FeatureService.check_feature_access(tenant.tier, feature_name)
    
    return {
        "tenant_id": tenant_id,
        "feature": feature_name,
        "has_access": has_access,
        "tier": tenant.tier
    }


@router.get("/tiers/{tier}/features")
async def get_tier_features(tier: str):
    """
    Get features for a specific subscription tier.
    """
    tiers = FeatureService.get_tiers()
    if tier not in tiers:
        raise HTTPException(status_code=404, detail=f"Tier '{tier}' not found")
    
    features = FeatureService.get_tenant_features(tier)
    
    return {
        "tier": tier,
        "features": features,
        "feature_count": len(features)
    }
