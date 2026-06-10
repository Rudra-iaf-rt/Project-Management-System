from django.db import models
from apps.accounts.models import User

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('TASK_ASSIGNED', 'Task Assigned'),
        ('TASK_UPDATED', 'Task Updated'),
        ('TASK_COMPLETED', 'Task Completed'),
        ('DEADLINE_REMINDER', 'Deadline Reminder'),
        ('PROJECT_UPDATED', 'Project Updated'),
        ('FILE_UPLOADED', 'File Uploaded'),
        ('TEAM_MESSAGE', 'Team Message'),
        ('COMMENT_ADDED', 'Comment Added'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    class Meta:
        ordering = ['-created_at']