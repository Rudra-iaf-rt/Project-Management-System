from django.db import models
from apps.accounts.models import User
from apps.teams.models import Team

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"
    
    class Meta:
        ordering = ['timestamp']