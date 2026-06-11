# apps/accounts/context_processors.py
from apps.notifications.models import Notification
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.teams.models import Team

def notifications_count(request):
    """Add unread notifications count to all templates"""
    if request.user.is_authenticated:
        return {
            'unread_notifications_count': Notification.objects.filter(
                user=request.user, 
                is_read=False
            ).count()
        }
    return {'unread_notifications_count': 0}

def user_role(request):
    """Add user role to all templates"""
    if request.user.is_authenticated:
        return {
            'is_super_admin': request.user.role == 'SUPER_ADMIN',
            'is_project_manager': request.user.role == 'PROJECT_MANAGER',
            'is_employee': request.user.role == 'EMPLOYEE',
            'user_role_display': request.user.get_role_display()
        }
    return {}

def system_stats(request):
    """Add system statistics to templates (for admin only)"""
    if request.user.is_authenticated and request.user.role == 'SUPER_ADMIN':
        from django.db.models import Count
        return {
            'global_stats': {
                'total_users': User.objects.count(),
                'total_projects': Project.objects.count(),
                'total_tasks': Task.objects.count(),
                'completed_tasks': Task.objects.filter(status='COMPLETED').count(),
            }
        }
    return {}

def current_year(request):
    """Add current year to all templates"""
    from datetime import datetime
    return {'current_year': datetime.now().year}

def site_settings(request):
    """Add site-wide settings to all templates"""
    from django.conf import settings
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'Project Management System'),
        'SITE_URL': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
    }

def user_teams(request):
    """Add user's teams to all templates"""
    if request.user.is_authenticated:
        teams = Team.objects.filter(members=request.user)
        return {'user_teams': teams}
    return {'user_teams': []}