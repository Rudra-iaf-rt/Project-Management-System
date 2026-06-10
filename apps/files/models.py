from django.db import models
from apps.projects.models import Project
from apps.accounts.models import User

class ProjectFile(models.Model):
    FILE_TYPES = [
        ('DOCUMENT', 'Document'),
        ('IMAGE', 'Image'),
        ('PDF', 'PDF'),
        ('ARCHIVE', 'Archive'),
        ('OTHER', 'Other'),
    ]
    
    file = models.FileField(upload_to='project_files/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default='OTHER')
    file_size = models.BigIntegerField(help_text="Size in bytes")
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    download_count = models.IntegerField(default=0)
    
    def __str__(self):
        return self.filename
    
    def get_file_extension(self):
        return self.filename.split('.')[-1].upper() if '.' in self.filename else 'UNKNOWN'
    
    def get_file_size_display(self):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    class Meta:
        ordering = ['-uploaded_at']