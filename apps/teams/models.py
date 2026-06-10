from django.db import models
from apps.accounts.models import User

class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    team_lead = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_teams')
    members = models.ManyToManyField(User, related_name='teams')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def member_count(self):
        return self.members.count()
    
    class Meta:
        ordering = ['name']

class TeamRole(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='roles')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)  # Manager, Developer, Tester, Designer
    
    class Meta:
        unique_together = ['team', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.role} in {self.team.name}"