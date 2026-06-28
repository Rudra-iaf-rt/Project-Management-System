from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Meeting, MeetingParticipant, MeetingSettings
from apps.projects.models import Project
from apps.teams.models import Team

@login_required
def meeting_dashboard(request):
    user = request.user
    
    # Query accessible projects & teams for scheduling dropdowns
    if user.role == 'SUPER_ADMIN':
        projects = Project.objects.all()
        teams = Team.objects.all()
        meetings = Meeting.objects.all()
    elif user.role == 'PROJECT_MANAGER':
        projects = Project.objects.filter(project_manager=user)
        teams = Team.objects.filter(team_lead=user)
        meetings = Meeting.objects.filter(host=user)
    else:
        projects = Project.objects.filter(team_members=user)
        teams = Team.objects.filter(members=user)
        meetings = Meeting.objects.filter(participants__user=user)
        
    meetings = meetings.distinct()
    upcoming_meetings = meetings.filter(status='SCHEDULED', start_time__gte=timezone.now()).order_by('start_time')
    past_meetings = meetings.filter(status='COMPLETED').order_by('-start_time')
    active_meetings = meetings.filter(status='IN_PROGRESS')
    
    context = {
        'upcoming_meetings': upcoming_meetings,
        'past_meetings': past_meetings,
        'active_meetings': active_meetings,
        'projects': projects,
        'teams': teams,
    }
    return render(request, 'meetings/meeting_dashboard.html', context)

@login_required
def meeting_room(request, meeting_code):
    meeting = get_object_or_404(Meeting, meeting_code=meeting_code)
    
    # Validate permission: check if meeting is project/team locked
    if meeting.host != request.user and request.user.role != 'SUPER_ADMIN':
        if meeting.project and not meeting.project.team_members.filter(id=request.user.id).exists():
            messages.error(request, "You are not a member of this project workspace.")
            return redirect('meeting_dashboard')
        if meeting.team and not meeting.team.members.filter(id=request.user.id).exists():
            messages.error(request, "You are not a member of this team.")
            return redirect('meeting_dashboard')

    settings, _ = MeetingSettings.objects.get_or_create(meeting=meeting)
    participant, created = MeetingParticipant.objects.get_or_create(
        meeting=meeting,
        user=request.user,
        defaults={
            'role': 'HOST' if meeting.host == request.user else 'PARTICIPANT',
            'state': 'APPROVED' if (meeting.host == request.user or not settings.waiting_room_enabled) else 'WAITING'
        }
    )
    
    # If waiting, redirect to preview page to wait for approval
    if participant.state == 'WAITING':
        return redirect('meeting_preview', meeting_code=meeting_code)
        
    context = {
        'meeting': meeting,
        'participant': participant,
        'is_host': participant.role == 'HOST',
    }
    return render(request, 'meetings/meeting_room.html', context)

@login_required
def meeting_preview(request, meeting_code):
    meeting = get_object_or_404(Meeting, meeting_code=meeting_code)
    
    # Handle instant joining requests or setup check
    participant = MeetingParticipant.objects.filter(meeting=meeting, user=request.user).first()
    
    context = {
        'meeting': meeting,
        'participant': participant,
    }
    return render(request, 'meetings/meeting_preview.html', context)
