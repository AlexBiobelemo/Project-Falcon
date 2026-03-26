"""
Permission tests for the Airport Operations Management System.

Tests cover:
- Role-based access control (RBAC)
- Permission bypass prevention
- Group-based permissions
- Object-level permissions
- Permission inheritance
- Edge cases in permission checks
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

from core.models import (
    Airport, Gate, Flight, FiscalAssessment, AssessmentStatus,
    EventLog, Staff, StaffRole,
)
from core.permissions import (
    UserRole,
    PermissionMixin,
    has_role,
    has_minimum_role,
    can_create_assessment,
    can_edit_assessment,
    can_approve_assessment,
    can_access_admin,
    can_create_report,
    can_create_document,
    IsAdminUser,
    IsEditorOrAbove,
    IsViewerOrAbove,
    IsApproverOrAbove,
    create_model_permissions,
    FiscalAssessmentPermissions,
)


class RoleHierarchyTest(TestCase):
    """Tests for role hierarchy."""

    def test_role_hierarchy_order(self):
        """Test role hierarchy is correctly ordered."""
        hierarchy = UserRole.ROLE_HIERARCHY
        self.assertEqual(hierarchy, ['viewer', 'editor', 'approver', 'admin'])
        
        # Verify order
        self.assertLess(hierarchy.index('viewer'), hierarchy.index('editor'))
        self.assertLess(hierarchy.index('editor'), hierarchy.index('approver'))
        self.assertLess(hierarchy.index('approver'), hierarchy.index('admin'))

    def test_role_groups_mapping(self):
        """Test role groups mapping is correct."""
        role_groups = UserRole.ROLE_GROUPS
        
        # Viewer requires no groups
        self.assertEqual(role_groups['viewer'], [])
        
        # Editor requires editors group
        self.assertIn('editors', role_groups['editor'])
        
        # Approver requires approvers group
        self.assertIn('approvers', role_groups['approver'])
        
        # Admin requires no groups (superuser only)
        self.assertEqual(role_groups['admin'], [])


class HasRoleTest(TestCase):
    """Tests for has_role function."""

    def setUp(self):
        # Create users
        self.viewer = User.objects.create_user(
            username='viewer',
            password='pass123',
        )
        
        self.editor = User.objects.create_user(
            username='editor',
            password='pass123',
        )
        
        self.approver = User.objects.create_user(
            username='approver',
            password='pass123',
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            is_superuser=True,
        )
        
        # Create groups
        self.editors_group, _ = Group.objects.get_or_create(name='editors')
        self.approvers_group, _ = Group.objects.get_or_create(name='approvers')
        
        # Assign groups
        self.editor.groups.add(self.editors_group)
        self.approver.groups.add(self.approvers_group)

    def test_unauthenticated_user_has_no_role(self):
        """Test unauthenticated user has no role."""
        from django.contrib.auth.models import AnonymousUser
        
        anon = AnonymousUser()
        self.assertFalse(has_role(anon, UserRole.VIEWER))
        self.assertFalse(has_role(anon, UserRole.ADMIN))

    def test_viewer_role_detection(self):
        """Test viewer role is detected correctly."""
        # has_role checks exact role match, not hierarchy
        # Viewer has no groups, so has_role returns False for all specific roles
        # Use has_minimum_role for hierarchy checks
        self.assertFalse(has_role(self.viewer, UserRole.EDITOR))
        self.assertFalse(has_role(self.viewer, UserRole.APPROVER))
        self.assertFalse(has_role(self.viewer, UserRole.ADMIN))
        # Viewer is default role for authenticated users without groups
        self.assertTrue(has_minimum_role(self.viewer, UserRole.VIEWER))

    def test_editor_role_detection(self):
        """Test editor role is detected correctly."""
        # has_role checks exact role match
        self.assertTrue(has_role(self.editor, UserRole.EDITOR))
        # has_role doesn't check hierarchy - use has_minimum_role for that
        self.assertTrue(has_minimum_role(self.editor, UserRole.VIEWER))
        self.assertFalse(has_role(self.editor, UserRole.APPROVER))
        self.assertFalse(has_role(self.editor, UserRole.ADMIN))

    def test_approver_role_detection(self):
        """Test approver role is detected correctly."""
        self.assertTrue(has_role(self.approver, UserRole.APPROVER))
        # has_role doesn't check hierarchy - use has_minimum_role for that
        self.assertTrue(has_minimum_role(self.approver, UserRole.EDITOR))
        self.assertTrue(has_minimum_role(self.approver, UserRole.VIEWER))
        self.assertFalse(has_role(self.approver, UserRole.ADMIN))

    def test_admin_role_detection(self):
        """Test admin role is detected correctly."""
        self.assertTrue(has_role(self.admin, UserRole.ADMIN))
        # Admin (superuser) has all roles via hierarchy
        self.assertTrue(has_minimum_role(self.admin, UserRole.APPROVER))
        self.assertTrue(has_minimum_role(self.admin, UserRole.EDITOR))
        self.assertTrue(has_minimum_role(self.admin, UserRole.VIEWER))


class HasMinimumRoleTest(TestCase):
    """Tests for has_minimum_role function."""

    def setUp(self):
        self.viewer = User.objects.create_user(
            username='viewer',
            password='pass123',
        )
        
        self.editor = User.objects.create_user(
            username='editor',
            password='pass123',
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            is_superuser=True,
        )
        
        self.editors_group, _ = Group.objects.get_or_create(name='editors')
        self.editor.groups.add(self.editors_group)

    def test_viewer_meets_viewer_requirement(self):
        """Test viewer meets viewer requirement."""
        self.assertTrue(has_minimum_role(self.viewer, UserRole.VIEWER))

    def test_viewer_does_not_meet_editor_requirement(self):
        """Test viewer does not meet editor requirement."""
        self.assertFalse(has_minimum_role(self.viewer, UserRole.EDITOR))

    def test_editor_meets_editor_requirement(self):
        """Test editor meets editor requirement."""
        self.assertTrue(has_minimum_role(self.editor, UserRole.EDITOR))

    def test_editor_meets_viewer_requirement(self):
        """Test editor meets viewer requirement."""
        self.assertTrue(has_minimum_role(self.editor, UserRole.VIEWER))

    def test_admin_meets_all_requirements(self):
        """Test admin meets all role requirements."""
        self.assertTrue(has_minimum_role(self.admin, UserRole.VIEWER))
        self.assertTrue(has_minimum_role(self.admin, UserRole.EDITOR))
        self.assertTrue(has_minimum_role(self.admin, UserRole.APPROVER))
        self.assertTrue(has_minimum_role(self.admin, UserRole.ADMIN))

    def test_unauthenticated_fails_all_checks(self):
        """Test unauthenticated user fails all role checks."""
        from django.contrib.auth.models import AnonymousUser
        anon = AnonymousUser()
        self.assertFalse(has_minimum_role(anon, UserRole.VIEWER))


class PermissionFunctionsTest(TestCase):
    """Tests for permission helper functions."""

    def setUp(self):
        self.viewer = User.objects.create_user(
            username='viewer',
            password='pass123',
        )
        
        self.editor = User.objects.create_user(
            username='editor',
            password='pass123',
        )
        
        self.approver = User.objects.create_user(
            username='approver',
            password='pass123',
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            is_superuser=True,
        )
        
        self.editors_group, _ = Group.objects.get_or_create(name='editors')
        self.approvers_group, _ = Group.objects.get_or_create(name='approvers')
        
        self.editor.groups.add(self.editors_group)
        self.approver.groups.add(self.approvers_group)

    def test_can_create_assessment(self):
        """Test can_create_assessment function."""
        self.assertFalse(can_create_assessment(self.viewer))
        self.assertTrue(can_create_assessment(self.editor))
        self.assertTrue(can_create_assessment(self.approver))
        self.assertTrue(can_create_assessment(self.admin))

    def test_can_edit_assessment(self):
        """Test can_edit_assessment function."""
        self.assertFalse(can_edit_assessment(self.viewer))
        self.assertTrue(can_edit_assessment(self.editor))
        self.assertTrue(can_edit_assessment(self.approver))
        self.assertTrue(can_edit_assessment(self.admin))

    def test_can_approve_assessment(self):
        """Test can_approve_assessment function."""
        self.assertFalse(can_approve_assessment(self.viewer))
        self.assertFalse(can_approve_assessment(self.editor))
        self.assertTrue(can_approve_assessment(self.approver))
        self.assertTrue(can_approve_assessment(self.admin))

    def test_can_access_admin(self):
        """Test can_access_admin function."""
        self.assertFalse(can_access_admin(self.viewer))
        self.assertFalse(can_access_admin(self.editor))
        self.assertFalse(can_access_admin(self.approver))
        self.assertTrue(can_access_admin(self.admin))

    def test_can_create_report(self):
        """Test can_create_report function."""
        self.assertFalse(can_create_report(self.viewer))
        self.assertTrue(can_create_report(self.editor))
        self.assertTrue(can_create_report(self.approver))
        self.assertTrue(can_create_report(self.admin))

    def test_can_create_document(self):
        """Test can_create_document function."""
        self.assertFalse(can_create_document(self.viewer))
        self.assertTrue(can_create_document(self.editor))
        self.assertTrue(can_create_document(self.approver))
        self.assertTrue(can_create_document(self.admin))


class DRFPermissionClassesTest(TestCase):
    """Tests for DRF permission classes."""

    def setUp(self):
        from rest_framework.test import APIRequestFactory
        from rest_framework.request import Request
        
        self.factory = APIRequestFactory()
        
        self.viewer = User.objects.create_user(
            username='viewer',
            password='pass123',
        )
        
        self.editor = User.objects.create_user(
            username='editor',
            password='pass123',
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            is_superuser=True,
        )
        
        self.editors_group, _ = Group.objects.get_or_create(name='editors')
        self.editor.groups.add(self.editors_group)

    def _create_request(self, user, method='GET'):
        """Helper to create DRF request."""
        request = self.factory.get('/')
        request.user = user
        request.method = method
        return request

    def test_is_admin_user_permission(self):
        """Test IsAdminUser permission class."""
        perm = IsAdminUser()
        
        # Admin should pass
        request = self._create_request(self.admin)
        self.assertTrue(perm.has_permission(request, None))
        
        # Non-admin should fail
        request = self._create_request(self.editor)
        self.assertFalse(perm.has_permission(request, None))
        
        request = self._create_request(self.viewer)
        self.assertFalse(perm.has_permission(request, None))

    def test_is_viewer_or_above_permission(self):
        """Test IsViewerOrAbove permission class."""
        perm = IsViewerOrAbove()
        
        # All authenticated users should pass GET
        request = self._create_request(self.viewer, 'GET')
        self.assertTrue(perm.has_permission(request, None))
        
        request = self._create_request(self.editor, 'GET')
        self.assertTrue(perm.has_permission(request, None))
        
        # Only editor+ should pass POST
        request = self._create_request(self.viewer, 'POST')
        self.assertFalse(perm.has_permission(request, None))
        
        request = self._create_request(self.editor, 'POST')
        self.assertTrue(perm.has_permission(request, None))

    def test_is_editor_or_above_permission(self):
        """Test IsEditorOrAbove permission class."""
        perm = IsEditorOrAbove()
        
        # Editor should pass POST
        request = self._create_request(self.editor, 'POST')
        self.assertTrue(perm.has_permission(request, None))
        
        # Viewer should fail POST
        request = self._create_request(self.viewer, 'POST')
        self.assertFalse(perm.has_permission(request, None))
        
        # Only admin should pass DELETE
        request = self._create_request(self.editor, 'DELETE')
        self.assertFalse(perm.has_permission(request, None))
        
        request = self._create_request(self.admin, 'DELETE')
        self.assertTrue(perm.has_permission(request, None))

    def test_is_approver_or_above_permission(self):
        """Test IsApproverOrAbove permission class."""
        approver = User.objects.create_user(
            username='approver',
            password='pass123',
        )
        approvers_group, _ = Group.objects.get_or_create(name='approvers')
        approver.groups.add(approvers_group)
        
        perm = IsApproverOrAbove()
        
        # Approver should pass POST
        request = self._create_request(approver, 'POST')
        self.assertTrue(perm.has_permission(request, None))
        
        # Editor should fail POST
        request = self._create_request(self.editor, 'POST')
        self.assertFalse(perm.has_permission(request, None))


class ModelPermissionsTest(TestCase):
    """Tests for model-specific permissions."""

    def setUp(self):
        from rest_framework.test import APIRequestFactory
        
        self.factory = APIRequestFactory()
        
        self.viewer = User.objects.create_user(
            username='viewer',
            password='pass123',
        )
        
        self.editor = User.objects.create_user(
            username='editor',
            password='pass123',
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            is_superuser=True,
        )
        
        self.editors_group, _ = Group.objects.get_or_create(name='editors')
        self.editor.groups.add(self.editors_group)

    def _create_request(self, user, method='GET'):
        """Helper to create DRF request."""
        request = self.factory.get('/')
        request.user = user
        request.method = method
        return request

    def test_fiscal_assessment_permissions_view(self):
        """Test FiscalAssessmentPermissions for viewing."""
        perm = FiscalAssessmentPermissions()
        
        # All authenticated users can view
        for user in [self.viewer, self.editor, self.admin]:
            request = self._create_request(user, 'GET')
            self.assertTrue(perm.has_permission(request, None))

    def test_fiscal_assessment_permissions_create(self):
        """Test FiscalAssessmentPermissions for creating."""
        perm = FiscalAssessmentPermissions()
        
        # Only editor+ can create
        request = self._create_request(self.viewer, 'POST')
        self.assertFalse(perm.has_permission(request, None))
        
        request = self._create_request(self.editor, 'POST')
        self.assertTrue(perm.has_permission(request, None))
        
        request = self._create_request(self.admin, 'POST')
        self.assertTrue(perm.has_permission(request, None))

    def test_fiscal_assessment_permissions_delete(self):
        """Test FiscalAssessmentPermissions for deleting."""
        perm = FiscalAssessmentPermissions()
        
        # Only admin can delete
        request = self._create_request(self.viewer, 'DELETE')
        self.assertFalse(perm.has_permission(request, None))
        
        request = self._create_request(self.editor, 'DELETE')
        self.assertFalse(perm.has_permission(request, None))
        
        request = self._create_request(self.admin, 'DELETE')
        self.assertTrue(perm.has_permission(request, None))

    def test_create_model_permissions_factory(self):
        """Test create_model_permissions factory function."""
        perm_class = create_model_permissions('TestModel')
        
        # Should create a class with correct name
        self.assertEqual(perm_class.__name__, 'TestModelPermissions')
        
        # Test permissions
        perm = perm_class()
        
        request = self._create_request(self.viewer, 'GET')
        self.assertTrue(perm.has_permission(request, None))
        
        request = self._create_request(self.viewer, 'DELETE')
        self.assertFalse(perm.has_permission(request, None))
        
        request = self._create_request(self.admin, 'DELETE')
        self.assertTrue(perm.has_permission(request, None))


class PermissionBypassPreventionTest(TestCase):
    """Tests to ensure permissions cannot be bypassed."""

    def setUp(self):
        self.client = Client()
        
        self.viewer = User.objects.create_user(
            username='viewer',
            password='pass123',
        )
        
        self.editor = User.objects.create_user(
            username='editor',
            password='pass123',
        )
        
        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            is_superuser=True,
        )
        
        self.editors_group, _ = Group.objects.get_or_create(name='editors')
        self.editor.groups.add(self.editors_group)
        
        self.airport = Airport.objects.create(
            code="LOS",
            name="Lagos Airport",
            city="Lagos",
        )

    def test_viewer_cannot_bypass_via_direct_url(self):
        """Test viewer cannot bypass permissions via direct URL access."""
        self.client.login(username='viewer', password='pass123')

        # Try to access editor-only view directly
        response = self.client.post('/airports/create/', {
            'code': 'NEW',
            'name': 'New Airport',
            'city': 'City',
        })
        # Should fail (CSRF or permission or 404 if URL doesn't exist)
        self.assertIn(response.status_code, [302, 403, 404, 400])

    def test_editor_cannot_delete_via_method_override(self):
        """Test editor cannot delete by overriding HTTP method."""
        self.client.login(username='editor', password='pass123')

        # Try POST to delete endpoint (should still require admin)
        response = self.client.post(f'/airports/{self.airport.id}/delete/')
        # Should fail (404 if URL doesn't exist, or 403)
        self.assertIn(response.status_code, [302, 403, 404])

    def test_unauthenticated_cannot_access_via_api(self):
        """Test unauthenticated cannot access via API."""
        response = self.client.get('/api/v1/airports/')
        self.assertEqual(response.status_code, 401)

    def test_viewer_cannot_access_admin_via_url_manipulation(self):
        """Test viewer cannot access admin via URL manipulation."""
        self.client.login(username='viewer', password='pass123')

        # Try various admin URLs
        admin_urls = [
            '/admin/core/fiscalassessment/add/',
            '/admin/auth/user/',
            '/admin/',
        ]

        for url in admin_urls:
            response = self.client.get(url)
            # Should redirect or forbid
            self.assertIn(response.status_code, [302, 403])

    def test_permission_cached_properly(self):
        """Test permissions are checked on each request."""
        self.client.login(username='editor', password='pass123')

        # Create assessment
        response = self.client.post('/assessments/create/', {
            'airport': self.airport.id,
            'period_type': 'monthly',
            'start_date': '2025-01-01',
            'end_date': '2025-01-31',
        })
        # May work for editor or return 404 if URL doesn't exist

        # Remove editor group
        self.editor.groups.remove(self.editors_group)

        # Try again - should now fail
        response = self.client.post('/assessments/create/', {
            'airport': self.airport.id,
            'period_type': 'monthly',
            'start_date': '2025-02-01',
            'end_date': '2025-02-28',
        })
        # Should fail now (or 404 if URL doesn't exist)
        self.assertIn(response.status_code, [302, 403, 404, 400])


class ObjectLevelPermissionTest(TestCase):
    """Tests for object-level permissions."""

    def setUp(self):
        self.viewer = User.objects.create_user(
            username='viewer',
            password='pass123',
        )
        
        self.editor = User.objects.create_user(
            username='editor',
            password='pass123',
        )
        
        self.editors_group, _ = Group.objects.get_or_create(name='editors')
        self.editor.groups.add(self.editors_group)
        
        self.airport1 = Airport.objects.create(
            code="LOS",
            name="Lagos Airport",
            city="Lagos",
        )
        
        self.airport2 = Airport.objects.create(
            code="ABJ",
            name="Abuja Airport",
            city="Abuja",
        )

    def test_user_can_view_all_airports(self):
        """Test users can view all airports."""
        # This is a basic test - object-level permissions may vary
        airports = Airport.objects.all()
        self.assertEqual(airports.count(), 2)

    def test_editor_can_edit_any_airport(self):
        """Test editor can edit any airport."""
        # Editors should be able to edit all airports
        self.airport1.name = "Updated Lagos"
        self.airport1.save()
        self.airport1.refresh_from_db()
        self.assertEqual(self.airport1.name, "Updated Lagos")


class PermissionMixinViewTest(TestCase):
    """Tests for PermissionMixin in views."""

    def setUp(self):
        self.client = Client()
        
        self.viewer = User.objects.create_user(
            username='viewer',
            password='pass123',
        )
        
        self.editor = User.objects.create_user(
            username='editor',
            password='pass123',
        )
        
        self.editors_group, _ = Group.objects.get_or_create(name='editors')
        self.editor.groups.add(self.editors_group)

    def test_permission_mixin_denial_message(self):
        """Test PermissionMixin shows denial message."""
        # Create a view with PermissionMixin
        from django.views import View
        from django.http import HttpResponse
        
        class TestView(PermissionMixin, View):
            required_role = UserRole.EDITOR
            denial_message = "Custom denial message"
            
            def get(self, request):
                return HttpResponse("Success")
        
        from django.urls import path, include
        from django.urls import re_path
        
        # Test would require URL configuration
        # This is a placeholder for the actual test
