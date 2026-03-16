"""Management command to create database backup."""

from django.core.management.base import BaseCommand
from django.utils import timezone
from core.tasks import backup_database


class Command(BaseCommand):
    help = 'Create a database backup'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting database backup...')
        
        result = backup_database()
        
        if result.get('success'):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Backup created successfully: {result['file']} "
                    f"({result['size'] / 1024 / 1024:.2f} MB)"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"Backup failed: {result.get('error')}")
            )
