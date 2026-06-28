import uuid
from django.db import models
from apps.accounts.models import User
from apps.projects.models import Project
from apps.teams.models import Team

class Meeting(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    meeting_code = models.CharField(max_length=20, unique=True, db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField(db_index=True)
    duration_minutes = models.PositiveIntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')
    
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_meetings')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='meetings')
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='meetings')
    
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_time']
        
    def __str__(self):
        return f"{self.title} ({self.meeting_code})"

class MeetingParticipant(models.Model):
    ROLE_CHOICES = [
        ('HOST', 'Host'),
        ('PARTICIPANT', 'Participant'),
    ]
    
    STATE_CHOICES = [
        ('WAITING', 'In Waiting Room'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('LEFT', 'Left'),
    ]
    
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meeting_participations')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='PARTICIPANT')
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='WAITING')
    
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    hand_raised = models.BooleanField(default=False)
    camera_on = models.BooleanField(default=False)
    mic_on = models.BooleanField(default=False)
    screen_sharing = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('meeting', 'user')
        
    def __str__(self):
        return f"{self.user.username} in {self.meeting.title}"

class MeetingSettings(models.Model):
    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name='settings')
    waiting_room_enabled = models.BooleanField(default=True)
    lock_share_screen = models.BooleanField(default=False)
    lock_chat = models.BooleanField(default=False)
    mute_on_entry = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Settings for {self.meeting.title}"

class MeetingChat(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='chats')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meeting_chats')
    message = models.TextField(blank=True)
    file = models.FileField(upload_to='meeting_attachments/', null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
        
    def __str__(self):
        return f"{self.user.username}: {self.message[:30]}"

class MeetingRecording(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name='recordings')
    file = models.FileField(upload_to='meeting_recordings/')
    duration_seconds = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Recording for {self.meeting.title} ({self.created_at})"
