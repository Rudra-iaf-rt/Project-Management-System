from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import models
from .models import Meeting, MeetingParticipant, MeetingChat, MeetingRecording, MeetingSettings
from .serializers import MeetingSerializer, MeetingParticipantSerializer, MeetingChatSerializer, MeetingRecordingSerializer, MeetingSettingsSerializer

class MeetingViewSet(viewsets.ModelViewSet):
    serializer_class = MeetingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'SUPER_ADMIN':
            return Meeting.objects.all()
        # Managers can see managed meetings, Employees can see meetings they host or are invited to/team meetings
        return Meeting.objects.filter(
            models.Q(host=user) | 
            models.Q(team__members=user) | 
            models.Q(project__team_members=user) | 
            models.Q(participants__user=user)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        meeting = self.get_object()
        settings, _ = MeetingSettings.objects.get_or_create(meeting=meeting)
        participant, created = MeetingParticipant.objects.get_or_create(
            meeting=meeting,
            user=request.user,
            defaults={
                'role': 'HOST' if meeting.host == request.user else 'PARTICIPANT',
                'state': 'APPROVED' if (meeting.host == request.user or not settings.waiting_room_enabled) else 'WAITING',
                'joined_at': timezone.now() if (meeting.host == request.user or not settings.waiting_room_enabled) else None
            }
        )
        if not created and participant.state == 'LEFT':
            participant.state = 'APPROVED' if (meeting.host == request.user or not settings.waiting_room_enabled) else 'WAITING'
            participant.joined_at = timezone.now() if participant.state == 'APPROVED' else None
            participant.save()
            
        serializer = MeetingParticipantSerializer(participant)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        meeting = self.get_object()
        try:
            participant = MeetingParticipant.objects.get(meeting=meeting, user=request.user)
            participant.state = 'LEFT'
            participant.left_at = timezone.now()
            participant.save()
            return Response({'status': 'left'})
        except MeetingParticipant.DoesNotExist:
            return Response({'error': 'Not joined'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def waiting_room(self, request, pk=None):
        meeting = self.get_object()
        if meeting.host != request.user:
            return Response({'error': 'Only host can view waiting room'}, status=status.HTTP_403_FORBIDDEN)
        
        waiting_participants = meeting.participants.filter(state='WAITING')
        serializer = MeetingParticipantSerializer(waiting_participants, many=True)
        return Response(serializer.data)

class MeetingChatViewSet(viewsets.ModelViewSet):
    serializer_class = MeetingChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        meeting_id = self.request.query_params.get('meeting')
        if meeting_id:
            return MeetingChat.objects.filter(meeting_id=meeting_id).order_by('timestamp')
        return MeetingChat.objects.none()

    def perform_create(self, serializer):
        meeting_id = self.request.data.get('meeting')
        meeting = get_object_or_404(Meeting, id=meeting_id)
        serializer.save(user=self.request.user, meeting=meeting)
