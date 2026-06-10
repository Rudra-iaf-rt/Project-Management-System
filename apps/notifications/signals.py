# apps/notifications/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.tasks.models import Task
from apps.projects.models import Project
from apps.files.models import ProjectFile
from .models import Notification

@receiver(post_save, sender=Task)
def task_notification(sender, instance, created, **kwargs):
    """Send notification when task is created or updated"""
    if created:
        Notification.objects.create(
            user=instance.assigned_to,
            title=f'New Task Assigned: {instance.title}',
            message=f'You have been assigned a new task: {instance.title} in project {instance.project.name}',
            notification_type='TASK_ASSIGNED',
            link=f'/tasks/{instance.id}/'
        )
    elif instance.status == 'COMPLETED' and not hasattr(instance, '_notification_sent'):
        Notification.objects.create(
            user=instance.assigned_by,
            title=f'Task Completed: {instance.title}',
            message=f'Task "{instance.title}" has been completed by {instance.assigned_to.get_full_name()}',
            notification_type='TASK_COMPLETED',
            link=f'/tasks/{instance.id}/'
        )
        instance._notification_sent = True

@receiver(post_save, sender=ProjectFile)
def file_notification(sender, instance, created, **kwargs):
    """Send notification when file is uploaded"""
    if created:
        # Notify project manager and team members
        users = [instance.project.project_manager] + list(instance.project.team_members.all())
        users = list(set(users))  # Remove duplicates
        
        for user in users:
            if user != instance.uploaded_by:  # Don't notify the uploader
                Notification.objects.create(
                    user=user,
                    title=f'New File Uploaded: {instance.filename}',
                    message=f'{instance.uploaded_by.get_full_name()} uploaded a new file to project {instance.project.name}',
                    notification_type='FILE_UPLOADED',
                    link=f'/files/'
                )