import io
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Avg
from openpyxl import Workbook
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from apps.projects.models import Project
from apps.tasks.models import Task
from apps.accounts.models import User

def get_dashboard_stats():
    """Get statistics for dashboard"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    stats = {
        'total_projects': Project.objects.count(),
        'active_projects': Project.objects.filter(status='IN_PROGRESS').count(),
        'completed_projects': Project.objects.filter(status='COMPLETED').count(),
        'total_tasks': Task.objects.count(),
        'completed_tasks': Task.objects.filter(status='COMPLETED').count(),
        'pending_tasks': Task.objects.filter(status='PENDING').count(),
        'overdue_tasks': Task.objects.filter(deadline__lt=timezone.now(), status__in=['PENDING', 'IN_PROGRESS']).count(),
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'new_projects_week': Project.objects.filter(created_at__gte=week_ago).count(),
        'new_tasks_week': Task.objects.filter(created_at__gte=week_ago).count(),
    }
    
    return stats

def generate_project_report_excel(user):
    """Generate Excel report of projects and tasks"""
    wb = Workbook()
    
    # Projects sheet
    ws_projects = wb.active
    ws_projects.title = "Projects"
    ws_projects.append(['Project Name', 'Status', 'Priority', 'Start Date', 'End Date', 
                       'Progress', 'Total Tasks', 'Completed Tasks', 'Budget'])
    
    # Filter by user role
    if user.role == 'SUPER_ADMIN':
        projects = Project.objects.all()
    elif user.role == 'PROJECT_MANAGER':
        projects = Project.objects.filter(project_manager=user)
    else:
        projects = Project.objects.filter(team_members=user)
        
    for project in projects:
        total_tasks = project.tasks.count()
        completed_tasks = project.tasks.filter(status='COMPLETED').count()
        
        ws_projects.append([
            project.name,
            project.get_status_display(),
            project.get_priority_display(),
            str(project.start_date),
            str(project.end_date),
            f"{project.progress}%",
            total_tasks,
            completed_tasks,
            f"${project.budget}"
        ])
    
    # Tasks sheet
    ws_tasks = wb.create_sheet("Tasks")
    ws_tasks.append(['Task Title', 'Project', 'Assigned To', 'Priority', 'Status', 
                    'Deadline', 'Estimated Hours', 'Actual Hours'])
    
    if user.role == 'SUPER_ADMIN':
        tasks = Task.objects.all()
    elif user.role == 'PROJECT_MANAGER':
        tasks = Task.objects.filter(project__project_manager=user)
    else:
        tasks = Task.objects.filter(assigned_to=user)
        
    for task in tasks:
        ws_tasks.append([
            task.title,
            task.project.name,
            task.assigned_to.username if task.assigned_to else 'Unassigned',
            task.get_priority_display(),
            task.get_status_display(),
            str(task.deadline),
            float(task.estimated_hours),
            float(task.actual_hours)
        ])
        
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

def generate_task_report_pdf(user):
    """Generate PDF report of tasks"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "Task Report")
    
    # Date
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 80, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Task summary
    y = height - 120
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Task Summary")
    
    y -= 20
    p.setFont("Helvetica", 10)
    
    if user.role == 'SUPER_ADMIN':
        tasks = Task.objects.all()
    elif user.role == 'PROJECT_MANAGER':
        tasks = Task.objects.filter(project__project_manager=user)
    else:
        tasks = Task.objects.filter(assigned_to=user)
        
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(status='COMPLETED').count()
    pending_tasks = tasks.filter(status='PENDING').count()
    in_progress_tasks = tasks.filter(status='IN_PROGRESS').count()
    
    p.drawString(50, y, f"Total Tasks: {total_tasks}")
    y -= 15
    p.drawString(50, y, f"Completed: {completed_tasks}")
    y -= 15
    p.drawString(50, y, f"Pending: {pending_tasks}")
    y -= 15
    p.drawString(50, y, f"In Progress: {in_progress_tasks}")
    
    # List top tasks
    y -= 30
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Recent Tasks")
    
    y -= 20
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y, "Title")
    p.drawString(300, y, "Status")
    p.drawString(400, y, "Deadline")
    
    y -= 15
    p.setFont("Helvetica", 9)
    recent_tasks = tasks.order_by('-created_at')[:20]
    
    for task in recent_tasks:
        if y < 50:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 9)
        
        p.drawString(50, y, task.title[:40] if len(task.title) > 40 else task.title)
        p.drawString(300, y, task.get_status_display())
        p.drawString(400, y, task.deadline.strftime('%Y-%m-%d') if task.deadline else 'No deadline')
        y -= 15
    
    p.save()
    buffer.seek(0)
    return buffer.getvalue()