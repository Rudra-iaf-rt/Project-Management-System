from django.db.models import Count, Sum, Avg
from apps.projects.models import Project, Task
from apps.accounts.models import User
from datetime import datetime, timedelta

def get_dashboard_stats():
    """Get statistics for dashboard"""
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    stats = {
        'total_projects': Project.objects.count(),
        'active_projects': Project.objects.filter(status='IN_PROGRESS').count(),
        'completed_projects': Project.objects.filter(status='COMPLETED').count(),
        'total_tasks': Task.objects.count(),
        'completed_tasks': Task.objects.filter(status='COMPLETED').count(),
        'pending_tasks': Task.objects.filter(status='PENDING').count(),
        'overdue_tasks': Task.objects.filter(deadline__lt=datetime.now(), status__in=['PENDING', 'IN_PROGRESS']).count(),
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'new_projects_week': Project.objects.filter(created_at__gte=week_ago).count(),
        'new_tasks_week': Task.objects.filter(created_at__gte=week_ago).count(),
    }
    
    return stats