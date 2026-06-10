# apps/projects/api.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from .models import Project
from .serializers import ProjectSerializer
from .filters import ProjectFilter
from apps.accounts.permissions import IsSuperAdmin, IsProjectManager

class ProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing projects
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProjectFilter
    search_fields = ['name', 'project_code', 'description']
    ordering_fields = ['created_at', 'start_date', 'end_date', 'status', 'priority']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return Project.objects.all()
        elif user.role == 'PROJECT_MANAGER':
            return Project.objects.filter(Q(project_manager=user) | Q(team_members=user))
        else:
            return Project.objects.filter(team_members=user)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """Add a member to the project"""
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from apps.accounts.models import User
            user = User.objects.get(id=user_id)
            project.team_members.add(user)
            return Response({'success': f'User {user.username} added to project'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """Remove a member from the project"""
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response({'error': 'user_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        project.team_members.remove(user_id)
        return Response({'success': 'Member removed successfully'})
    
    @action(detail=True, methods=['get'])
    def tasks(self, request, pk=None):
        """Get all tasks for a project"""
        project = self.get_object()
        tasks = project.tasks.all()
        from apps.tasks.serializers import TaskSerializer
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get project statistics"""
        project = self.get_object()
        total_tasks = project.tasks.count()
        completed_tasks = project.tasks.filter(status='COMPLETED').count()
        
        return Response({
            'project_id': project.id,
            'project_name': project.name,
            'progress': project.progress,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': project.tasks.filter(status='PENDING').count(),
            'in_progress_tasks': project.tasks.filter(status='IN_PROGRESS').count(),
            'testing_tasks': project.tasks.filter(status='TESTING').count(),
            'overdue_tasks': project.tasks.filter(status__in=['PENDING', 'IN_PROGRESS'], deadline__lt=timezone.now()).count(),
            'total_budget': project.budget,
            'days_remaining': project.days_remaining,
        })