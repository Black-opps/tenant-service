"""
Custom exceptions for tenant service.
"""
from fastapi import HTTPException, status


class TenantException(HTTPException):
    """Base tenant exception."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class TenantNotFoundError(TenantException):
    """Tenant not found."""
    def __init__(self, tenant_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with id {tenant_id} not found"
        )


class UserNotFoundError(TenantException):
    """User not found."""
    def __init__(self, user_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )


class RoleNotFoundError(TenantException):
    """Role not found."""
    def __init__(self, role_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id {role_id} not found"
        )


class TenantAlreadyExistsError(TenantException):
    """Tenant already exists."""
    def __init__(self, email: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tenant with email {email} already exists"
        )


class UserAlreadyExistsError(TenantException):
    """User already exists."""
    def __init__(self, email: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {email} already exists in this tenant"
        )


class InvalidInvitationError(TenantException):
    """Invalid invitation."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation"
        )


class TenantLimitExceededError(TenantException):
    """Tenant limit exceeded."""
    def __init__(self, limit_type: str, current: int, max_allowed: int):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{limit_type} limit exceeded: {current}/{max_allowed}"
        )


class PermissionDeniedError(TenantException):
    """Permission denied."""
    def __init__(self, required_permission: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Required: {required_permission}"
        )


class TenantInactiveError(TenantException):
    """Tenant is inactive."""
    def __init__(self, tenant_id: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant {tenant_id} is inactive or suspended"
        )