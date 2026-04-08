"""
Tier to feature mapping for SaaS subscription plans.
"""
from typing import List, Dict

# Tier feature mapping
TIER_FEATURES: Dict[str, List[str]] = {
    "free": [
        "basic_dashboard",
        "view_transactions"
    ],
    "starter": [
        "basic_dashboard",
        "view_transactions",
        "export_csv",
        "basic_reports"
    ],
    "professional": [
        "basic_dashboard",
        "view_transactions",
        "export_csv",
        "export_pdf",
        "advanced_reports",
        "api_access",
        "custom_reports",
        "real_time_analytics"
    ],
    "enterprise": [
        "basic_dashboard",
        "view_transactions",
        "export_csv",
        "export_pdf",
        "advanced_reports",
        "api_access",
        "custom_reports",
        "real_time_analytics",
        "webhooks",
        "sla_guarantee",
        "audit_logs",
        "white_label"
    ]
}

# Feature descriptions for documentation
FEATURE_DESCRIPTIONS = {
    "basic_dashboard": "Access to basic analytics dashboard",
    "view_transactions": "View transaction history",
    "export_csv": "Export data as CSV",
    "export_pdf": "Export reports as PDF",
    "basic_reports": "Standard report templates",
    "advanced_reports": "Custom report builder",
    "api_access": "REST API access",
    "custom_reports": "Create custom reports",
    "real_time_analytics": "Real-time data updates",
    "webhooks": "Webhook notifications",
    "sla_guarantee": "99.9% uptime guarantee",
    "audit_logs": "Compliance audit trails",
    "white_label": "Custom branding"
}

def get_features_for_tier(tier: str) -> List[str]:
    """Get all features for a given tier."""
    return TIER_FEATURES.get(tier, TIER_FEATURES.get("free", []))

def tenant_has_feature(tier: str, feature: str) -> bool:
    """Check if a tier has a specific feature."""
    return feature in get_features_for_tier(tier)

def get_all_tiers() -> List[str]:
    """Get all available tiers."""
    return list(TIER_FEATURES.keys())
