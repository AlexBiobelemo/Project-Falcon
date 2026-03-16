"""Management command to add staff assignments and shifts."""

import random
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.management.base import BaseCommand

from core.models import (
    Flight, Staff, StaffAssignment, StaffRole,
    Shift, StaffShiftAssignment,
)


class Command(BaseCommand):
    """Command to add staff assignments and shifts."""

    help = "Add staff assignments and shift schedules"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("ADDING STAFF ASSIGNMENTS AND SHIFTS"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write()

        # Create staff assignments for flights
        self.stdout.write("[1/2] Creating staff assignments...")
        flights = list(Flight.objects.all()[:200])
        staff_list = list(Staff.objects.filter(
            role__in=[StaffRole.GROUND_CREW.value, StaffRole.SECURITY.value, StaffRole.CLEANING.value]
        )[:50])

        count = 0
        for flight in flights:
            for staff in staff_list[:3]:
                try:
                    StaffAssignment.objects.get_or_create(
                        staff=staff,
                        flight=flight,
                        defaults={'assignment_type': staff.role}
                    )
                    count += 1
                except Exception:
                    pass

        self.stdout.write(f"    Created {count} staff assignments.")
        self.stdout.write(f"    Total: {StaffAssignment.objects.count()}")

        # Create shifts
        self.stdout.write("[2/2] Creating shifts and assignments...")
        shifts_data = [
            {'name': 'Morning Shift', 'start': '06:00', 'end': '14:00'},
            {'name': 'Afternoon Shift', 'start': '14:00', 'end': '22:00'},
            {'name': 'Night Shift', 'start': '22:00', 'end': '06:00'},
        ]

        for s in shifts_data:
            Shift.objects.get_or_create(
                name=s['name'],
                defaults={
                    'start_time': datetime.strptime(s['start'], '%H:%M').time(),
                    'end_time': datetime.strptime(s['end'], '%H:%M').time(),
                    'min_staff': 5,
                    'max_staff': 20,
                    'is_active': True
                }
            )

        self.stdout.write(f"    Created {Shift.objects.count()} shifts")

        # Create shift assignments for next 14 days
        staff_all = list(Staff.objects.all()[:30])
        shifts = list(Shift.objects.all())
        count = 0

        for day in range(14):
            shift_date = (timezone.now() + timedelta(days=day)).date()
            for shift in shifts:
                for staff in staff_all[:8]:
                    try:
                        StaffShiftAssignment.objects.get_or_create(
                            staff=staff,
                            shift=shift,
                            date=shift_date,
                            defaults={'status': StaffShiftAssignment.AssignmentStatus.SCHEDULED}
                        )
                        count += 1
                    except Exception:
                        pass

        self.stdout.write(f"    Created {count} shift assignments.")
        self.stdout.write(f"    Total: {StaffShiftAssignment.objects.count()}")

        self.stdout.write()
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("COMPLETE"))
        self.stdout.write(self.style.SUCCESS("=" * 50))
