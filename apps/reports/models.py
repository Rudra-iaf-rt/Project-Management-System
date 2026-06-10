from django.db import models
from apps.accounts.models import User
from apps.projects.models import Project
from apps.tasks.models import Task

class Report(models.Model):
    REPORT_TYPES = [
        ('PROJECT', 'Project Report'),
        ('TASK', 'Task Report'),
        ('EMPLOYEE', 'Employee Report'),
        ('TEAM', 'Team Report'),
    ]
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    filters = models.JSONField(default=dict)
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.created_at}"