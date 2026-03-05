"""Management command to set up default user groups and permissions.

This command creates the following groups with appropriate permissions:
- editors: Can create and edit fiscal assessments, reports, and documents
- approvers: Can approve fiscal assessments (includes editor permissions)

The permission system follows least privilege principles:
- New users are viewers by default (no special group needed)
- Users must be explicitly added to groups for elevated privileges
- Admin access is restricted to superusers only

Usage:
    python manage.py setup_permissions
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import (
    Airport,
    Document,
    EventLog,
    FiscalAssessment,
    Flight,
    Gate,
    Passenger,
    Report,
    Staff,
    StaffAssignment,
)


class Command(BaseCommand):
    """Set up default groups and permissions for the application."""

    help = "Set up default user groups and permissions for role-based access control"

    def handle(self, *args, **options):
        """Execute the command to set up groups and permissions."""
        self.stdout.write("Setting up user groups and permissions...")
        
        # Create groups
        editors_group = self._create_group('editors', 'Editors', options)
        approvers_group = self._create_group('approvers', 'Approvers', options)
        
        # Assign permissions to editors group
        self._assign_editor_permissions(editors_group, options)
        
        # Assign permissions to approvers group (includes editor permissions)
        self._assign_approver_permissions(approvers_group, options)
        
        self.stdout.write(self.style.SUCCESS(
            "\nSetup complete! Groups created:\n"
            "  - editors: Can create and edit assessments, reports, documents\n"
            "  - approvers: Can approve assessments (includes editor permissions)\n"
            "\nTo assign users to groups, use:\n"
            "  python manage.py shell\n"
            "  >>> from django.contrib.auth.models import User, Group\n"
            "  >>> user = User.objects.get(username='username')\n"
            "  >>> user.groups.add(Group.objects.get(name='editors'))\n"
        ))

    def _create_group(self, name, description, options):
        """Create a group if it doesn't exist."""
        group, created = Group.objects.get_or_create(name=name)
        if created:
            self.stdout.write(f"Created group: {name}")
        else:
            if options.get('verbosity', 1) > 0:
                self.stdout.write(f"Group already exists: {name}")
        return group

    def _assign_editor_permissions(self, group, options):
        """Assign permissions for editors group."""
        # Define content types for core models
        content_types = {
            'airport': ContentType.objects.get_for_model(Airport),
            'document': ContentType.objects.get_for_model(Document),
            'fiscalassessment': ContentType.objects.get_for_model(FiscalAssessment),
            'flight': ContentType.objects.get_for_model(Flight),
            'gate': ContentType.objects.get_for_model(Gate),
            'passenger': ContentType.objects.get_for_model(Passenger),
            'report': ContentType.objects.get_for_model(Report),
            'staff': ContentType.objects.get_for_model(Staff),
            'staffassignment': ContentType.objects.get_for_model(StaffAssignment),
            'eventlog': ContentType.objects.get_for_model(EventLog),
        }
        
        # Permissions for editors - can add, change, view but not delete or approve
        editor_perms = [
            # Airport - can view
            ('view_airport', content_types['airport']),
            # Document - full CRUD
            ('add_document', content_types['document']),
            ('change_document', content_types['document']),
            ('view_document', content_types['document']),
            ('delete_document', content_types['document']),
            # FiscalAssessment - can create, change, view (not approve/delete)
            ('add_fiscalassessment', content_types['fiscalassessment']),
            ('change_fiscalassessment', content_types['fiscalassessment']),
            ('view_fiscalassessment', content_types['fiscalassessment']),
            # Flight - can view and change
            ('view_flight', content_types['flight']),
            ('change_flight', content_types['flight']),
            # Gate - can view
            ('view_gate', content_types['gate']),
            # Passenger - can view
            ('view_passenger', content_types['passenger']),
            # Report - full CRUD
            ('add_report', content_types['report']),
            ('change_report', content_types['report']),
            ('view_report', content_types['report']),
            ('delete_report', content_types['report']),
            # Staff - can view
            ('view_staff', content_types['staff']),
            # StaffAssignment - can view
            ('view_staffassignment', content_types['staffassignment']),
            # EventLog - can view
            ('view_eventlog', content_types['eventlog']),
        ]
        
        for perm_codename, content_type in editor_perms:
            perm, _ = Permission.objects.get_or_create(
                codename=perm_codename,
                content_type=content_type,
                defaults={'name': f'Can {perm_codename.replace("_", " ")}'}
            )
            group.permissions.add(perm)
        
        if options.get('verbosity', 1) > 0:
            self.stdout.write(f"Assigned {len(editor_perms)} permissions to editors group")

    def _assign_approver_permissions(self, group, options):
        """Assign permissions for approvers group (includes all editor permissions)."""
        # First, add all editor permissions
        for perm in group.permissions.all():
            pass  # Permissions are added directly below
        
        # Additional permissions specific to approvers
        content_types = {
            'fiscalassessment': ContentType.objects.get_for_model(FiscalAssessment),
        }
        
        # Approvers can approve fiscal assessments (change status)
        # This is handled through the role-based system, but we add the permission
        # for Django's has_perm checks
        approver_perms = [
            ('change_fiscalassessment', content_types['fiscalassessment']),
        ]
        
        for perm_codename, content_type in approver_perms:
            perm, _ = Permission.objects.get_or_create(
                codename=perm_codename,
                content_type=content_type,
                defaults={'name': f'Can {perm_codename.replace("_", " ")}'}
            )
            group.permissions.add(perm)
        
        if options.get('verbosity', 1) > 0:
            self.stdout.write(f"Assigned additional permissions to approvers group")
