# apps/tasks/api.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .models import Task
from .serializers import TaskSerializer
from apps.notifications.models import Notification

class TaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing tasks
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority', 'project', 'assigned_to']
    search_fields = ['title', 'description']
    ordering_fields = ['deadline', 'created_at', 'priority', 'status']
    ordering = ['-priority', 'deadline']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return Task.objects.all()
        elif user.role == 'PROJECT_MANAGER':
            return Task.objects.filter(project__project_manager=user)
        else:
            return Task.objects.filter(assigned_to=user)
    
    def perform_create(self, serializer):
        task = serializer.save(assigned_by=self.request.user)
        # Create notification for assigned user
        Notification.objects.create(
            user=task.assigned_to,
            title=f'New Task Assigned: {task.title}',
            message=f'You have been assigned a new task in project {task.project.name}',
            notification_type='TASK_ASSIGNED',
            link=f'/tasks/{task.id}/'
        )
        return task
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update task status"""
        task = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response({'error': 'status is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = task.status
        task.status = new_status
        
        if new_status == 'COMPLETED':
            task.completed_at = timezone.now()
        
        task.save()
        
        # Create notification for status change
        if old_status != new_status:
            Notification.objects.create(
                user=task.assigned_to,
                title=f'Task Status Updated: {task.title}',
                message=f'Task status changed from {old_status} to {new_status}',
                notification_type='TASK_UPDATED',
                link=f'/tasks/{task.id}/'
            )
        
        return Response({'success': True, 'status': new_status})
    
    @action(detail=True, methods=['post'])
    def log_time(self, request, pk=None):
        """Log actual time spent on task"""
        task = self.get_object()
        hours = request.data.get('hours')
        
        if not hours:
            return Response({'error': 'hours is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            hours = float(hours)
            task.actual_hours += hours
            task.save()
            return Response({'success': True, 'actual_hours': task.actual_hours})
        except ValueError:
            return Response({'error': 'Invalid hours value'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_tasks(self, request):
        """Get tasks assigned to current user"""
        tasks = Task.objects.filter(assigned_to=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue tasks"""
        tasks = Task.objects.filter(
            assigned_to=request.user,
            status__in=['PENDING', 'IN_PROGRESS'],
            deadline__lt=timezone.now()
        )
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)
    @action(detail=True, methods=['post'], url_path='update_deadline')
    def update_deadline(self, request, pk=None):
        task = self.get_object()
        new_deadline = request.data.get('deadline')
        if not new_deadline:
            return Response({'error': 'deadline required'}, status=status.HTTP_400_BAD_REQUEST)
        from dateutil import parser
        task.deadline = parser.isoparse(new_deadline)
        task.save()
        return Response({'success': True, 'deadline': task.deadline.isoformat()})