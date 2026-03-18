"""
Invitation service for inviting users.
"""
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
import logging
from uuid import UUID

from ..models.invitation import Invitation, InvitationStatus
from ..models.user import UserRole, User
from ..core.exceptions import InvalidInvitationError, UserAlreadyExistsError
from ..core.security import generate_invitation_token
from ..services.user_manager import UserManager
from ..services.email_service import EmailService

logger = logging.getLogger(__name__)


class InvitationService:
    """Service for managing user invitations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_manager = UserManager(db)
        self.email_service = EmailService()
    
    def create_invitation(
        self,
        tenant_id: UUID,
        inviter_id: UUID,
        email: str,
        role: UserRole = UserRole.VIEWER,
        permissions: Optional[List[str]] = None
    ) -> Invitation:
        """
        Create a new invitation.
        
        Args:
            tenant_id: Tenant UUID
            inviter_id: User sending invitation
            email: Invitee email
            role: Role to assign
            permissions: Custom permissions
            
        Returns:
            Created invitation
        """
        # Check if user already exists
        existing_user = self.user_manager.get_user_by_email(tenant_id, email)
        if existing_user:
            raise UserAlreadyExistsError(email)
        
        # Check for pending invitation
        existing = self.db.query(Invitation).filter(
            Invitation.tenant_id == tenant_id,
            Invitation.email == email,
            Invitation.status == InvitationStatus.PENDING
        ).first()
        
        if existing:
            # Resend existing invitation
            return self.resend_invitation(existing.id)
        
        # Create new invitation
        invitation = Invitation(
            tenant_id=tenant_id,
            invited_by=inviter_id,
            email=email,
            role=role,
            permissions=permissions or [],
            token=generate_invitation_token()
        )
        
        self.db.add(invitation)
        self.db.flush()
        
        # Send email
        self.email_service.send_invitation_email(
            to_email=email,
            inviter_name=self._get_user_name(inviter_id),
            organization_name=self._get_org_name(tenant_id),
            invitation_token=invitation.token,
            role=role.value
        )
        
        logger.info(f"Created invitation for {email} to tenant {tenant_id}")
        
        return invitation
    
    def accept_invitation(self, token: str, password: str, first_name: str, last_name: str) -> User:
        """
        Accept invitation and create user.
        
        Args:
            token: Invitation token
            password: User password
            first_name: First name
            last_name: Last name
            
        Returns:
            Created user
            
        Raises:
            InvalidInvitationError: If invitation invalid
        """
        invitation = self.db.query(Invitation).filter(
            Invitation.token == token
        ).first()
        
        if not invitation or not invitation.is_valid:
            raise InvalidInvitationError()
        
        # Create user
        user = self.user_manager.create_user(
            tenant_id=invitation.tenant_id,
            email=invitation.email,
            first_name=first_name,
            last_name=last_name,
            role=invitation.role,
            password=password,
            invited_by=invitation.invited_by,
            permissions=invitation.permissions
        )
        
        # Update invitation
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Invitation accepted for {invitation.email}")
        
        return user
    
    def cancel_invitation(self, invitation_id: UUID):
        """Cancel pending invitation."""
        invitation = self.db.query(Invitation).filter(
            Invitation.id == invitation_id
        ).first()
        
        if invitation and invitation.status == InvitationStatus.PENDING:
            invitation.status = InvitationStatus.CANCELLED
            self.db.commit()
            logger.info(f"Cancelled invitation: {invitation_id}")
    
    def resend_invitation(self, invitation_id: UUID) -> Invitation:
        """Resend invitation email."""
        invitation = self.db.query(Invitation).filter(
            Invitation.id == invitation_id
        ).first()
        
        if not invitation or invitation.status != InvitationStatus.PENDING:
            raise InvalidInvitationError()
        
        # Update expiry
        invitation.expires_at = datetime.utcnow() + timedelta(days=7)
        self.db.commit()
        
        # Resend email
        self.email_service.send_invitation_email(
            to_email=invitation.email,
            inviter_name=self._get_user_name(invitation.invited_by),
            organization_name=self._get_org_name(invitation.tenant_id),
            invitation_token=invitation.token,
            role=invitation.role.value
        )
        
        logger.info(f"Resent invitation: {invitation_id}")
        
        return invitation
    
    def get_pending_invitations(self, tenant_id: UUID) -> List[Invitation]:
        """Get all pending invitations for tenant."""
        return self.db.query(Invitation).filter(
            Invitation.tenant_id == tenant_id,
            Invitation.status == InvitationStatus.PENDING
        ).all()
    
    def cleanup_expired(self):
        """Clean up expired invitations."""
        expired = self.db.query(Invitation).filter(
            Invitation.expires_at < datetime.utcnow(),
            Invitation.status == InvitationStatus.PENDING
        ).all()
        
        for invitation in expired:
            invitation.status = InvitationStatus.EXPIRED
        
        self.db.commit()
        
        logger.info(f"Cleaned up {len(expired)} expired invitations")
    
    def _get_user_name(self, user_id: UUID) -> str:
        """Get user full name."""
        user = self.db.query(User).filter(User.id == user_id).first()
        return user.full_name if user else "A user"
    
    def _get_org_name(self, tenant_id: UUID) -> str:
        """Get organization name."""
        from ..models.organization import Organization
        org = self.db.query(Organization).filter(Organization.id == tenant_id).first()
        return org.name if org else "the organization"