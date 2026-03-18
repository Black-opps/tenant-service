from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract tenant from API key or JWT
        api_key = request.headers.get("X-API-Key")
        
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API key")
        
        # Get tenant from service
        tenant = await get_tenant_by_api_key(api_key)
        
        if not tenant:
            raise HTTPException(status_code=403, detail="Invalid tenant")
        
        if tenant.status != TenantStatus.ACTIVE:
            raise HTTPException(status_code=403, detail="Tenant not active")
        
        # Add tenant to request state
        request.state.tenant = tenant
        
        # Add to logging context
        structlog.contextvars.bind_contextvars(
            tenant_id=str(tenant.id),
            tenant_tier=tenant.tier
        )
        
        response = await call_next(request)
        return response
