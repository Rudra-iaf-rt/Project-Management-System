# management/commands/cleanup_old_files.py
import os
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.files.models import ProjectFile

class Command(BaseCommand):
    help = 'Delete old files that are no longer needed'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to keep files (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        threshold_date = datetime.now() - timedelta(days=days)
        
        # Get old files
        old_files = ProjectFile.objects.filter(uploaded_at__lt=threshold_date)
        
        if dry_run:
            self.stdout.write(f"Found {old_files.count()} files older than {days} days:")
            for file in old_files:
                self.stdout.write(f"  - {file.filename} (uploaded: {file.uploaded_at.date()})")
            return
        
        # Delete files
        deleted_count = 0
        for file in old_files:
            try:
                # Delete physical file
                if os.path.isfile(file.file.path):
                    os.remove(file.file.path)
                
                # Delete database record
                file.delete()
                deleted_count += 1
                self.stdout.write(f"Deleted: {file.filename}")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error deleting {file.filename}: {str(e)}"))
        
        self.stdout.write(
            self.style.SUCCESS(f"Successfully deleted {deleted_count} old files")
        )