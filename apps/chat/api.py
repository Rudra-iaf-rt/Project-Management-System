# apps/chat/api.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import ChatMessage
from .serializers import ChatMessageSerializer
from apps.teams.models import Team

class ChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        team_id = self.request.query_params.get('team_id')
        if team_id:
            return ChatMessage.objects.filter(team_id=team_id).order_by('-timestamp')[:100]
        return ChatMessage.objects.none()
    
    @action(detail=False, methods=['get'], url_path='history/(?P<team_id>[^/.]+)')
    def history(self, request, team_id=None):
        messages = ChatMessage.objects.filter(team_id=team_id).order_by('timestamp')[:100]
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='mark-read/(?P<team_id>[^/.]+)')
    def mark_read(self, request, team_id=None):
        # Mark messages as read for current user in this team
        ChatMessage.objects.filter(team_id=team_id).exclude(user=request.user).update(is_read=True)
        return Response({'success': True})