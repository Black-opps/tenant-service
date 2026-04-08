"""
Feature service for tenant capability management.
"""
from typing import List, Dict
from ..core.features import get_features_for_tier, tenant_has_feature, FEATURE_DESCRIPTIONS, get_all_tiers


class FeatureService:
    """Service for managing tenant features and capabilities."""
    
    @staticmethod
    def get_tenant_features(tier: str) -> List[str]:
        """Get all features available to a tenant tier."""
        return get_features_for_tier(tier)
    
    @staticmethod
    def check_feature_access(tier: str, feature: str) -> bool:
        """Check if a tier has access to a specific feature."""
        return tenant_has_feature(tier, feature)
    
    @staticmethod
    def get_feature_description(feature: str) -> str:
        """Get description of a feature."""
        return FEATURE_DESCRIPTIONS.get(feature, "Feature description not available")
    
    @staticmethod
    def get_all_features() -> Dict[str, str]:
        """Get all available features with descriptions."""
        return FEATURE_DESCRIPTIONS
    
    @staticmethod
    def get_tiers() -> List[str]:
        """Get all available subscription tiers."""
        return get_all_tiers()
    
    @staticmethod
    def get_tier_summary() -> Dict:
        """Get summary of all tiers and their features."""
        return {
            tier: {
                "features": get_features_for_tier(tier),
                "feature_count": len(get_features_for_tier(tier))
            }
            for tier in get_all_tiers()
        }
