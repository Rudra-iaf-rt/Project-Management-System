# apps/teams/api.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Team, TeamRole
from .serializers import TeamSerializer, TeamRoleSerializer
from apps.accounts.permissions import IsSuperAdmin, IsProjectManager

class TeamViewSet(viewsets.ModelViewSet):
    """
    API endpoint for teams
    """
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['team_lead']
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return Team.objects.all()
        return Team.objects.filter(members=user)
    
    def perform_create(self, serializer):
        serializer.save(team_lead=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        team = self.get_object()
        user_id = request.data.get('user_id')
        role_name = request.data.get('role', 'Member')
        
        from apps.accounts.models import User
        try:
            user = User.objects.get(id=user_id)
            team.members.add(user)
            TeamRole.objects.get_or_create(team=team, user=user, defaults={'role': role_name})
            return Response({'success': f'Added {user.username} to team'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        team = self.get_object()
        user_id = request.data.get('user_id')
        team.members.remove(user_id)
        TeamRole.objects.filter(team=team, user_id=user_id).delete()
        return Response({'success': 'Member removed'})
    
    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        team = self.get_object()
        from apps.accounts.serializers import UserSerializer
        serializer = UserSerializer(team.members.all(), many=True)
        return Response(serializer.data)