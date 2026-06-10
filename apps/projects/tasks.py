# apps/projects/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.notifications.models import Notification

@shared_task
def check_deadline_reminders():
    """Send deadline reminders for tasks due soon"""
    today = timezone.now()
    reminder_days = [1, 3, 7]  # Send reminders 1, 3, and 7 days before deadline
    
    for days in reminder_days:
        deadline_range_start = today + timedelta(days=days)
        deadline_range_end = deadline_range_start + timedelta(days=1)
        
        tasks = Task.objects.filter(
            deadline__range=(deadline_range_start, deadline_range_end),
            status__in=['PENDING', 'IN_PROGRESS']
        )
        
        for task in tasks:
            # Create notification for assigned user
            Notification.objects.create(
                user=task.assigned_to,
                title=f'Task Deadline Reminder: {task.title}',
                message=f'Task "{task.title}" is due in {days} day(s)',
                notification_type='DEADLINE_REMINDER',
                link=f'/tasks/{task.id}/'
            )
            
            # Send email reminder
            if task.assigned_to.email:
                html_message = render_to_string('email/deadline_reminder.html', {
                    'user': task.assigned_to,
                    'tasks': [task],
                    'site_url': settings.SITE_URL
                })
                send_mail(
                    f'Task Deadline Reminder: {task.title}',
                    strip_tags(html_message),
                    settings.DEFAULT_FROM_EMAIL,
                    [task.assigned_to.email],
                    html_message=html_message,
                    fail_silently=True
                )
    
    return f"Sent reminders for {tasks.count()} tasks"

@shared_task
def update_project_progress():
    """Update project progress based on task completion"""
    projects = Project.objects.all()
    for project in projects:
        total_tasks = project.tasks.count()
        if total_tasks > 0:
            completed_tasks = project.tasks.filter(status='COMPLETED').count()
            progress = int((completed_tasks / total_tasks) * 100)
            
            # Update project status based on progress
            if progress == 100:
                project.status = 'COMPLETED'
            elif progress > 0 and project.status == 'PENDING':
                project.status = 'IN_PROGRESS'
            
            project.save()
    
    return f"Updated progress for {projects.count()} projects"

@shared_task
def generate_weekly_project_report():
    """Generate and send weekly project report to managers"""
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    one_week_ago = datetime.now() - timedelta(days=7)
    
    # Get project managers
    managers = User.objects.filter(role='PROJECT_MANAGER')
    
    for manager in managers:
        projects = Project.objects.filter(project_manager=manager)
        
        if projects.exists():
            stats = {
                'total_projects': projects.count(),
                'new_projects': projects.filter(created_at__gte=one_week_ago).count(),
                'completed_projects': projects.filter(status='COMPLETED').count(),
                'active_projects': projects.filter(status='IN_PROGRESS').count(),
                'total_tasks': Task.objects.filter(project__in=projects).count(),
                'completed_tasks': Task.objects.filter(project__in=projects, status='COMPLETED').count(),
            }
            
            html_message = render_to_string('email/weekly_report.html', {
                'user': manager,
                'stats': stats,
                'projects': projects[:5],
                'site_url': settings.SITE_URL
            })
            
            send_mail(
                'Weekly Project Report',
                strip_tags(html_message),
                settings.DEFAULT_FROM_EMAIL,
                [manager.email],
                html_message=html_message,
                fail_silently=True
            )
    
    return f"Sent weekly reports to {managers.count()} managers"