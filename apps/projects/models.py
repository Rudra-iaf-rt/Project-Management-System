from django.db import models
from apps.accounts.models import User
from datetime import date

class Project(models.Model):
    PRIORITY_CHOICES = [
        ('HIGH', '🔴 High'),
        ('MEDIUM', '🟡 Medium'),
        ('LOW', '🟢 Low'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', '🔴 Pending'),
        ('IN_PROGRESS', '🟡 In Progress'),
        ('COMPLETED', '🟢 Completed'),
        ('ON_HOLD', '⚫ On Hold'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    project_code = models.CharField(max_length=20, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    project_manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='managed_projects')
    team_members = models.ManyToManyField(User, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def progress(self):
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = self.tasks.filter(status='COMPLETED').count()
        return int((completed_tasks / total_tasks) * 100)
    
    @property
    def days_remaining(self):
        delta = self.end_date - date.today()
        return delta.days
    
    class Meta:
        ordering = ['-created_at']