from django.apps import AppConfig
from django.db import connection


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """Initialize the app when Django starts.
        
        This automatically sets up the default user groups and permissions
        if they don't already exist. This ensures the least-privilege
        permission system works out of the box without manual setup.
        """
        # Import signals to register them
        import core.signals  # noqa: F401
        
        # Only run during migrations or when tables exist
        if connection.schema_editor() is None:
            # We're in a running server, not in migration mode
            self._setup_groups_and_permissions()

    def _setup_groups_and_permissions(self):
        """Set up default groups and permissions automatically."""
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

        # Track if any groups were created (for logging)
        created_groups = []

        # Define content types mapping
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

        # Create editors group
        editors_group, editors_created = Group.objects.get_or_create(name='editors')
        if editors_created:
            created_groups.append('editors')

        # Create approvers group
        approvers_group, approvers_created = Group.objects.get_or_create(name='approvers')
        if approvers_created:
            created_groups.append('approvers')

        # Assign permissions to editors group if newly created
        if editors_created:
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
                editors_group.permissions.add(perm)

        # If either group was created, log the setup
        if created_groups:
            import logging
            logger = logging.getLogger('django')
            logger.info(
                f"Core app: Automatically created permission groups: {', '.join(created_groups)}. "
                f"Users will have VIEWER role by default (least privilege)."
            )
