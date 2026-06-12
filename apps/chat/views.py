from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ChatMessage
from apps.teams.models import Team

@login_required
def chat_room(request, team_id):
    """Chat room view"""
    team = get_object_or_404(Team, id=team_id)
    
    # Check if user is member of the team
    if request.user not in team.members.all() and request.user.role != 'SUPER_ADMIN':
        from django.shortcuts import redirect
        from django.contrib import messages
        messages.error(request, 'You are not a member of this team.')
        return redirect('team_list')
    
    # Get previous messages
    messages = ChatMessage.objects.filter(team=team)[:50]
    
    context = {
        'team': team,
        'messages': messages,
    }
    return render(request, 'chat/chat_room.html', context)

@login_required
def send_message_api(request):
    """API endpoint to send message"""
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        team_id = data.get('team_id')
        message = data.get('message')
        
        team = get_object_or_404(Team, id=team_id)
        
        chat_message = ChatMessage.objects.create(
            user=request.user,
            team=team,
            message=message
        )
        
        return JsonResponse({
            'success': True,
            'message': message,
            'username': request.user.username,
            'timestamp': chat_message.timestamp.isoformat()
        })
    
    return JsonResponse({'success': False}, status=400)

# apps/chat/views.py - Add this function
@login_required
def chat_index(request):
    """Show list of teams to chat with"""
    teams = Team.objects.filter(members=request.user)
    return render(request, 'chat/chat_index.html', {'teams': teams})

@login_required
def chat_history_api(request, team_id):
    """API endpoint to get message history"""
    team = get_object_or_404(Team, id=team_id)
    if request.user not in team.members.all() and request.user.role != 'SUPER_ADMIN':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    messages = ChatMessage.objects.filter(team=team).order_by('timestamp')[:100]
    data = []
    for msg in messages:
        data.append({
            'username': msg.user.username,
            'message': msg.message,
            'timestamp': msg.timestamp.isoformat(),
        })
    return JsonResponse(data, safe=False)

@login_required
def chat_mark_read_api(request, team_id):
    """API endpoint to mark messages as read"""
    team = get_object_or_404(Team, id=team_id)
    if request.user not in team.members.all() and request.user.role != 'SUPER_ADMIN':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    ChatMessage.objects.filter(team=team).exclude(user=request.user).update(is_read=True)
    return JsonResponse({'success': True})