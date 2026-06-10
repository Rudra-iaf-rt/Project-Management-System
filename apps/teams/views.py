from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Team, TeamRole
from .forms import TeamForm, AddMemberForm
from apps.accounts.models import User

@login_required
def team_list(request):
    """List all teams"""
    if request.user.role == 'SUPER_ADMIN':
        teams = Team.objects.all()
    else:
        teams = Team.objects.filter(members=request.user)
    
    paginator = Paginator(teams, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'teams': page_obj,
        'total_teams': teams.count(),
    }
    return render(request, 'teams/team_list.html', context)

@login_required
def team_detail(request, pk):
    """Team details view"""
    team = get_object_or_404(Team, pk=pk)
    
    # Check membership
    if request.user not in team.members.all() and request.user.role != 'SUPER_ADMIN':
        messages.error(request, 'You are not a member of this team.')
        return redirect('team_list')
    
    # Get team roles
    team_roles = TeamRole.objects.filter(team=team)
    
    context = {
        'team': team,
        'members': team.members.all(),
        'team_roles': team_roles,
        'can_edit': request.user == team.team_lead or request.user.role == 'SUPER_ADMIN',
    }
    return render(request, 'teams/team_detail.html', context)

@login_required
def team_create(request):
    """Create new team"""
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.team_lead = request.user
            team.save()
            form.save_m2m()  # Save members
            
            # Add team lead to members if not already
            if request.user not in team.members.all():
                team.members.add(request.user)
            
            messages.success(request, f'Team "{team.name}" created successfully!')
            return redirect('team_detail', pk=team.pk)
    else:
        form = TeamForm()
    
    return render(request, 'teams/team_form.html', {'form': form, 'title': 'Create Team'})

@login_required
def team_update(request, pk):
    """Update team"""
    team = get_object_or_404(Team, pk=pk)
    
    if request.user != team.team_lead and request.user.role != 'SUPER_ADMIN':
        messages.error(request, 'You do not have permission to edit this team.')
        return redirect('team_list')
    
    if request.method == 'POST':
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            messages.success(request, f'Team "{team.name}" updated successfully!')
            return redirect('team_detail', pk=team.pk)
    else:
        form = TeamForm(instance=team)
    
    return render(request, 'teams/team_form.html', {'form': form, 'title': 'Update Team', 'team': team})

@login_required
def add_member(request, pk):
    """Add member to team"""
    team = get_object_or_404(Team, pk=pk)
    
    if request.user != team.team_lead and request.user.role != 'SUPER_ADMIN':
        messages.error(request, 'You do not have permission to add members to this team.')
        return redirect('team_list')
    
    if request.method == 'POST':
        form = AddMemberForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            role = form.cleaned_data['role']
            
            team.members.add(user)
            TeamRole.objects.create(team=team, user=user, role=role)
            
            messages.success(request, f'{user.username} added to team "{team.name}" as {role}!')
            return redirect('team_detail', pk=team.pk)
    else:
        form = AddMemberForm()
    
    return render(request, 'teams/add_member.html', {'form': form, 'team': team})