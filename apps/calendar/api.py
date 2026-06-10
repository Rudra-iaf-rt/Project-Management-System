# apps/calendar/api.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from datetime import datetime
from apps.tasks.models import Task
from apps.projects.models import Project
from apps.tasks.serializers import TaskSerializer

class CalendarEventViewSet(viewsets.ViewSet):
    """
    API endpoint for calendar events (tasks and project milestones)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get all events for FullCalendar"""
        start_str = request.query_params.get('start')
        end_str = request.query_params.get('end')
        
        start = datetime.fromisoformat(start_str.replace('Z', '+00:00')) if start_str else None
        end = datetime.fromisoformat(end_str.replace('Z', '+00:00')) if end_str else None
        
        events = []
        
        # Get tasks
        tasks = Task.objects.filter(assigned_to=request.user)
        if start and end:
            tasks = tasks.filter(deadline__range=(start, end))
        
        for task in tasks:
            events.append({
                'id': f'task_{task.id}',
                'title': task.title,
                'start': task.deadline.isoformat(),
                'end': (task.deadline + timedelta(hours=1)).isoformat(),
                'url': f'/tasks/{task.id}/',
                'backgroundColor': self._get_priority_color(task.priority),
                'borderColor': self._get_priority_color(task.priority),
                'extendedProps': {
                    'type': 'task',
                    'priority': task.priority,
                    'status': task.status,
                    'is_overdue': task.is_overdue
                }
            })
        
        # Get project deadlines (for manager)
        if request.user.role in ['SUPER_ADMIN', 'PROJECT_MANAGER']:
            projects = Project.objects.filter(project_manager=request.user)
            if start and end:
                projects = projects.filter(end_date__range=(start.date(), end.date()))
            
            for project in projects:
                events.append({
                    'id': f'project_{project.id}',
                    'title': f'📁 {project.name} - Due',
                    'start': project.end_date.isoformat(),
                    'allDay': True,
                    'url': f'/projects/{project.id}/',
                    'backgroundColor': '#6c757d',
                    'borderColor': '#6c757d',
                    'extendedProps': {
                        'type': 'project_deadline',
                        'progress': project.progress
                    }
                })
        
        return Response(events)
    
    def _get_priority_color(self, priority):
        return {
            'HIGH': '#dc3545',
            'MEDIUM': '#ffc107',
            'LOW': '#28a745'
        }.get(priority, '#17a2b8')
    
    @action(detail=False, methods=['post'], url_path='quick-task')
    def quick_task(self, request):
        """Quick create task from calendar"""
        from apps.projects.models import Project
        
        title = request.data.get('title')
        project_id = request.data.get('project_id')
        deadline = request.data.get('deadline')
        priority = request.data.get('priority', 'MEDIUM')
        
        if not title or not project_id or not deadline:
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            project = Project.objects.get(id=project_id)
            task = Task.objects.create(
                title=title,
                project=project,
                assigned_to=request.user,
                assigned_by=request.user,
                deadline=datetime.fromisoformat(deadline.replace('Z', '+00:00')),
                priority=priority,
                status='PENDING'
            )
            serializer = TaskSerializer(task)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)