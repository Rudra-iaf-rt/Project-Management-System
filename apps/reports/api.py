# apps/reports/api.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from django.utils import timezone
from .models import Report
from .serializers import ReportSerializer
from .utils import generate_project_report_excel, generate_task_report_pdf
from apps.accounts.permissions import IsSuperAdmin, IsProjectManager

class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for reports
    """
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.role == 'SUPER_ADMIN':
            return Report.objects.all()
        return Report.objects.filter(generated_by=self.request.user)
    
    @action(detail=False, methods=['post'], url_path='project')
    def generate_project_report(self, request):
        """Generate project report and return Excel file"""
        excel_file = generate_project_report_excel(request.user)
        response = HttpResponse(
            excel_file,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="project_report.xlsx"'
        return response
    
    @action(detail=False, methods=['post'], url_path='task')
    def generate_task_report(self, request):
        """Generate task report and return PDF"""
        pdf_file = generate_task_report_pdf(request.user)
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="task_report.pdf"'
        return response
    
    @action(detail=False, methods=['get'], url_path='dashboard-stats')
    def dashboard_stats(self, request):
        """Get dashboard statistics for current user"""
        from django.db.models import Count, Q
        from apps.projects.models import Project
        from apps.tasks.models import Task
        
        if request.user.role == 'SUPER_ADMIN':
            projects = Project.objects.all()
            tasks = Task.objects.all()
        elif request.user.role == 'PROJECT_MANAGER':
            projects = Project.objects.filter(project_manager=request.user)
            tasks = Task.objects.filter(project__in=projects)
        else:
            projects = Project.objects.filter(team_members=request.user)
            tasks = Task.objects.filter(assigned_to=request.user)
        
        stats = {
            'total_projects': projects.count(),
            'active_projects': projects.filter(status='IN_PROGRESS').count(),
            'completed_projects': projects.filter(status='COMPLETED').count(),
            'total_tasks': tasks.count(),
            'completed_tasks': tasks.filter(status='COMPLETED').count(),
            'pending_tasks': tasks.filter(status='PENDING').count(),
            'in_progress_tasks': tasks.filter(status='IN_PROGRESS').count(),
            'overdue_tasks': tasks.filter(
                status__in=['PENDING', 'IN_PROGRESS'], 
                deadline__lt=timezone.now()
            ).count(),
        }
        return Response(stats)