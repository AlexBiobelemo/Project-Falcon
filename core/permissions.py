"""Permission system for the Airport Operations Management System.

This module implements a least-privilege access control system where:
- New users have minimal permissions by default (view-only access)
- Admin features are restricted to superusers only
- Specific features require specific permissions/groups
- Role and permission bypass is prevented by enforcing checks at all levels

User Roles:
- Viewer: Can only view data (default for new users)
- Editor: Can create and edit data (requires 'editors' group)
- Approver: Can approve assessments (requires 'approvers' group)
- Admin: Full access (superusers only)

CRITICAL SECURITY: All sensitive operations (create, update, delete, approve)
MUST enforce role-based permissions. Users cannot bypass their assigned roles.
"""

import logging
from typing import Any, List, Optional
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model

# Import DRF permissions for API use
from rest_framework import permissions

logger = logging.getLogger(__name__)


class UserRole:
    """User role constants for the application."""
    
    VIEWER = 'viewer'
    EDITOR = 'editor'
    APPROVER = 'approver'
    ADMIN = 'admin'
    
    # Role hierarchy (higher index = more privileges)
    ROLE_HIERARCHY = [VIEWER, EDITOR, APPROVER, ADMIN]
    
    # Required groups for each role
    ROLE_GROUPS = {
        VIEWER: [],  # No group required - default for all authenticated users
        EDITOR: ['editors'],
        APPROVER: ['approvers'],
        ADMIN: [],  # Superuser only
    }


class PermissionMixin(LoginRequiredMixin):
    """Mixin that provides role-based access control for views.
    
    Usage:
        class MyView(PermissionMixin, View):
            required_role = UserRole.EDITOR
            # or
            required_permissions = ['core.add_fiscalassessment']
    """
    
    # Minimum role required to access this view
    required_role: Optional[str] = None
    
    # Alternative: specific permissions required
    required_permissions: List[str] = []
    
    # If True, only superusers can access
    require_superuser: bool = False
    
    # Custom denial message
    denial_message: str = "You don't have permission to access this page."
    
    def dispatch(self, request, *args, **kwargs):
        """Check permissions before processing the request."""
        # First check login (LoginRequiredMixin)
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        # Check superuser requirement
        if self.require_superuser:
            if not request.user.is_superuser:
                return self.handle_permission_denied(request)
        
        # Check role requirement
        if self.required_role:
            if not self._has_required_role(request.user):
                return self.handle_permission_denied(request)
        
        # Check specific permissions
        if self.required_permissions:
            if not self._has_required_permissions(request.user):
                return self.handle_permission_denied(request)
        
        return super().dispatch(request, *args, **kwargs)
    
    def _has_required_role(self, user) -> bool:
        """Check if user has the required role."""
        if self.required_role == UserRole.ADMIN:
            return user.is_superuser
        
        # Get user's effective role
        user_role = self._get_user_role(user)
        
        # Check if user's role meets the requirement
        if user_role is None:
            return False
        
        try:
            required_idx = UserRole.ROLE_HIERARCHY.index(self.required_role)
            user_idx = UserRole.ROLE_HIERARCHY.index(user_role)
            return user_idx >= required_idx
        except ValueError:
            return False
    
    def _has_required_permissions(self, user) -> bool:
        """Check if user has all required permissions."""
        for perm in self.required_permissions:
            if not user.has_perm(perm):
                return False
        return True
    
    def _get_user_role(self, user) -> Optional[str]:
        """Determine the user's effective role based on groups and superuser status."""
        # Superusers have admin role
        if user.is_superuser:
            return UserRole.ADMIN
        
        # Check group memberships
        group_names = [g.name for g in user.groups.all()]
        
        # Check from highest to lowest role
        for role in reversed(UserRole.ROLE_HIERARCHY):
            required_groups = UserRole.ROLE_GROUPS.get(role, [])
            if required_groups:
                if any(g in group_names for g in required_groups):
                    return role
        
        # Default role for authenticated users
        return UserRole.VIEWER
    
    def handle_permission_denied(self, request, *args, **kwargs):
        """Handle permission denied scenario."""
        from django.shortcuts import render
        from django.http import HttpResponseForbidden
        
        if self.denial_message:
            # Return a proper error page
            return HttpResponseForbidden(self.denial_message)
        else:
            # Redirect to home or dashboard
            from django.shortcuts import redirect
            return redirect('core:dashboard')


class RoleRequiredMixin(PermissionMixin):
    """Simplified mixin that only requires a specific role."""
    
    def __init__(self, *args, **kwargs):
        # Set require_superuser based on role
        if getattr(self, 'required_role', None) == UserRole.ADMIN:
            self.require_superuser = True
        super().__init__(*args, **kwargs)


def has_role(user, role: str) -> bool:
    """Check if user has a specific role.
    
    Args:
        user: Django user instance
        role: Role constant from UserRole
    
    Returns:
        True if user has the role, False otherwise
    """
    if not user.is_authenticated:
        return False
    
    if role == UserRole.ADMIN:
        return user.is_superuser
    
    group_names = [g.name for g in user.groups.all()]
    required_groups = UserRole.ROLE_GROUPS.get(role, [])
    
    return any(g in group_names for g in required_groups)


def has_minimum_role(user, role: str) -> bool:
    """Check if user has at minimum the specified role.
    
    Args:
        user: Django user instance
        role: Role constant from UserRole
    
    Returns:
        True if user's role meets or exceeds the requirement
    """
    if not user.is_authenticated:
        return False
    
    # Superusers always pass
    if user.is_superuser:
        return True
    
    group_names = [g.name for g in user.groups.all()]
    
    # Find the highest role the user has
    user_role = None
    for r in reversed(UserRole.ROLE_HIERARCHY):
        required_groups = UserRole.ROLE_GROUPS.get(r, [])
        if required_groups:
            if any(g in group_names for g in required_groups):
                user_role = r
                break
    
    # Default to viewer if no groups
    if user_role is None:
        user_role = UserRole.VIEWER
    
    # Compare hierarchy positions
    try:
        required_idx = UserRole.ROLE_HIERARCHY.index(role)
        user_idx = UserRole.ROLE_HIERARCHY.index(user_role)
        return user_idx >= required_idx
    except ValueError:
        return False


def can_create_assessment(user) -> bool:
    """Check if user can create fiscal assessments."""
    return has_minimum_role(user, UserRole.EDITOR)


def can_edit_assessment(user) -> bool:
    """Check if user can edit fiscal assessments."""
    return has_minimum_role(user, UserRole.EDITOR)


def can_approve_assessment(user) -> bool:
    """Check if user can approve fiscal assessments."""
    return has_minimum_role(user, UserRole.APPROVER)


def can_access_admin(user) -> bool:
    """Check if user can access the Django admin panel."""
    return user.is_superuser


def can_create_report(user) -> bool:
    """Check if user can create reports."""
    return has_minimum_role(user, UserRole.EDITOR)


def can_create_document(user) -> bool:
    """Check if user can create documents."""
    return has_minimum_role(user, UserRole.EDITOR)


class BaseRolePermission(permissions.BasePermission):
    """Base class for role-based permissions that prevents bypass attacks.
    
    CRITICAL: This class enforces that users can ONLY perform actions
    allowed by their assigned role. There is NO way to bypass this check.
    """
    
    # Define required role for each HTTP method
    # None means the method is not allowed
    ROLE_REQUIREMENTS = {
        'GET': None,  # Will be set in subclass
        'HEAD': None,
        'OPTIONS': None,
        'POST': None,
        'PUT': None,
        'PATCH': None,
        'DELETE': None,
    }
    
    def _get_user_role(self, user):
        """Determine the user's effective role based on groups and superuser status."""
        if not user.is_authenticated:
            return None
        
        # Superusers have admin role - cannot be bypassed
        if user.is_superuser:
            return UserRole.ADMIN
        
        # Check group memberships
        group_names = [g.name for g in user.groups.all()]
        
        # Check from highest to lowest role
        for role in reversed(UserRole.ROLE_HIERARCHY):
            required_groups = UserRole.ROLE_GROUPS.get(role, [])
            if required_groups:
                if any(g in group_names for g in required_groups):
                    return role
        
        # Default role for authenticated users
        return UserRole.VIEWER
    
    def _has_minimum_role(self, user, required_role):
        """Check if user has at minimum the specified role."""
        if not user.is_authenticated:
            return False
        
        # Superusers always pass - this cannot be bypassed
        if user.is_superuser:
            return True
        
        user_role = self._get_user_role(user)
        if user_role is None:
            return False
        
        try:
            required_idx = UserRole.ROLE_HIERARCHY.index(required_role)
            user_idx = UserRole.ROLE_HIERARCHY.index(user_role)
            return user_idx >= required_idx
        except ValueError:
            return False
    
    def has_permission(self, request, view):
        """Check if user has permission for this request."""
        # Must be authenticated
        if not request.user.is_authenticated:
            return False
        
        # Get the HTTP method
        method = request.method
        
        # Get required role for this method
        required_role = self.ROLE_REQUIREMENTS.get(method)
        
        # If no role requirement defined, deny by default
        if required_role is None:
            logger.warning(
                f"SECURITY: No role requirement defined for {method} "
                f"in {self.__class__.__name__}. Denying by default."
            )
            return False
        
        # Check if user has required role
        has_role = self._has_minimum_role(request.user, required_role)
        
        if not has_role:
            logger.warning(
                f"SECURITY: User {request.user.username} attempted to perform "
                f"{method} but lacks required role {required_role}. "
                f"User's effective role: {self._get_user_role(request.user)}"
            )
        
        return has_role


class IsAdminUser(BaseRolePermission):
    """Permission that requires admin (superuser) role.
    
    This is the HIGHEST level of permission - only superusers can access.
    Cannot be bypassed by any means.
    """
    
    ROLE_REQUIREMENTS = {
        'GET': UserRole.ADMIN,
        'HEAD': UserRole.ADMIN,
        'OPTIONS': UserRole.ADMIN,
        'POST': UserRole.ADMIN,
        'PUT': UserRole.ADMIN,
        'PATCH': UserRole.ADMIN,
        'DELETE': UserRole.ADMIN,
    }


class IsEditorOrAbove(BaseRolePermission):
    """Permission that requires editor role or above (approver, admin).
    
    Allows create, update operations but NOT delete or approve.
    """
    
    ROLE_REQUIREMENTS = {
        'GET': UserRole.VIEWER,      # Anyone authenticated can view
        'HEAD': UserRole.VIEWER,
        'OPTIONS': UserRole.VIEWER,
        'POST': UserRole.EDITOR,      # Create requires editor
        'PUT': UserRole.EDITOR,       # Update requires editor
        'PATCH': UserRole.EDITOR,
        'DELETE': UserRole.ADMIN,    # Delete requires admin 
    }


class IsApproverOrAbove(BaseRolePermission):
    """Permission that requires approver role or above (admin).
    
    This is specifically for approval operations which are highly sensitive.
    """
    
    ROLE_REQUIREMENTS = {
        'GET': UserRole.VIEWER,
        'HEAD': UserRole.VIEWER,
        'OPTIONS': UserRole.VIEWER,
        'POST': UserRole.APPROVER,   # Approval requires approver
        'PUT': UserRole.APPROVER,
        'PATCH': UserRole.APPROVER,
        'DELETE': UserRole.ADMIN,
    }


class IsViewerOrAbove(BaseRolePermission):
    """Permission that requires at minimum viewer role.
    
    This is the default for read-only operations.
    """
    
    ROLE_REQUIREMENTS = {
        'GET': UserRole.VIEWER,
        'HEAD': UserRole.VIEWER,
        'OPTIONS': UserRole.VIEWER,
        'POST': UserRole.EDITOR,     # Create requires editor
        'PUT': UserRole.EDITOR,      # Update requires editor
        'PATCH': UserRole.EDITOR,
        'DELETE': UserRole.ADMIN,    # Delete requires admin
    }



# FACTORY FUNCTION - Generates model-specific permission classes dynamically

def create_model_permissions(model_name, app_label='core'):
    """Factory function to create a permission class for a specific model.
    
    This generates a permission class that follows the standard pattern:
    - View: Any authenticated user (viewer role)
    - Create: Editor role required
    - Update: Editor role required
    - Delete: Admin (superuser) ONLY - cannot be bypassed
    
    Args:
        model_name: Name of the model (e.g., 'FiscalAssessment', 'Report')
        app_label: Django app label (default: 'core')
    
    Returns:
        A dynamically created permission class
    
    Usage:
        FiscalAssessmentPermissions = create_model_permissions('FiscalAssessment')
        ReportPermissions = create_model_permissions('Report')
    """
    
    class DynamicModelPermissions(BaseRolePermission):
        """Permission class for {} operations.
        
        Auto-generated by factory. Standard pattern:
        - View: Any authenticated user
        - Create: Editor role required
        - Update: Editor role required
        - Delete: Admin (superuser) ONLY
        """.format(model_name)
        
        def has_permission(self, request, view):
            """Check if user has permission for this request."""
            if not request.user.is_authenticated:
                return False
            
            method = request.method
            
            # DELETE always requires admin - CRITICAL SECURITY
            if method == 'DELETE':
                if not request.user.is_superuser:
                    logger.warning(
                        f"SECURITY: User {request.user.username} attempted DELETE "
                        f"on {model_name} but is not admin."
                    )
                    return False
                return True
            
            # Create requires editor
            if method == 'POST':
                return self._has_minimum_role(request.user, UserRole.EDITOR)
            
            # Update requires editor
            if method in ('PUT', 'PATCH'):
                return self._has_minimum_role(request.user, UserRole.EDITOR)
            
            # View allows any authenticated user
            if method in ('GET', 'HEAD', 'OPTIONS'):
                return True
            
            return False
    
    # Set a descriptive name for the class
    DynamicModelPermissions.__name__ = f'{model_name}Permissions'
    
    return DynamicModelPermissions


# Generated permission classes using the factory

FiscalAssessmentPermissions = create_model_permissions('FiscalAssessment')
ReportPermissions = create_model_permissions('Report')
DocumentPermissions = create_model_permissions('Document')
AirportPermissions = create_model_permissions('Airport')
FlightPermissions = create_model_permissions('Flight')
GatePermissions = create_model_permissions('Gate')
StaffPermissions = create_model_permissions('Staff')
MaintenanceLogPermissions = create_model_permissions('MaintenanceLog')
IncidentReportPermissions = create_model_permissions('IncidentReport')
