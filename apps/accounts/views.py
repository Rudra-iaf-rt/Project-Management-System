# apps/accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.utils import timezone
from .models import User, UserProfile, ActivityLog
from .forms import UserRegisterForm, UserProfileForm, UserUpdateForm
# Fix: Import Task from tasks app, not projects
from apps.projects.models import Project
from apps.tasks.models import Task  # Changed this line
from django.core.paginator import Paginator

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Log activity
            ActivityLog.objects.create(
                user=user,
                action='User logged in',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            # Redirect based on role
            if user.role == 'SUPER_ADMIN':
                return redirect('admin_dashboard')
            elif user.role == 'PROJECT_MANAGER':
                return redirect('manager_dashboard')
            else:
                return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    ActivityLog.objects.create(
        user=request.user,
        action='User logged out',
        ip_address=request.META.get('REMOTE_ADDR')
    )
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

@login_required
def dashboard(request):
    """Main dashboard for regular employees"""
    user = request.user
    
    # Get user statistics
    context = {
        'total_projects': Project.objects.filter(team_members=user).count(),
        'active_projects': Project.objects.filter(team_members=user, status='IN_PROGRESS').count(),
        'completed_tasks': Task.objects.filter(assigned_to=user, status='COMPLETED').count(),
        'pending_tasks': Task.objects.filter(assigned_to=user, status='PENDING').count(),
        'in_progress_tasks': Task.objects.filter(assigned_to=user, status='IN_PROGRESS').count(),
        'recent_tasks': Task.objects.filter(assigned_to=user).order_by('-created_at')[:5],
        'upcoming_deadlines': Task.objects.filter(
            assigned_to=user,
            status__in=['PENDING', 'IN_PROGRESS'],
            deadline__gte=timezone.now()
        ).order_by('deadline')[:5],
        'overdue_tasks': Task.objects.filter(
            assigned_to=user,
            status__in=['PENDING', 'IN_PROGRESS'],
            deadline__lt=timezone.now()
        ).count(),
        'recent_activities': ActivityLog.objects.filter(user=user)[:10],
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def profile_view(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})

@login_required
def manager_dashboard(request):
    """Dashboard for project managers"""
    if request.user.role not in ['PROJECT_MANAGER', 'SUPER_ADMIN']:
        return redirect('dashboard')
    
    # Statistics
    managed_projects = Project.objects.filter(project_manager=request.user)
    team_members = User.objects.filter(projects__in=managed_projects).distinct()
    
    context = {
        'total_projects': managed_projects.count(),
        'active_projects': managed_projects.filter(status='IN_PROGRESS').count(),
        'completed_projects': managed_projects.filter(status='COMPLETED').count(),
        'total_team_members': team_members.count(),
        'total_tasks': Task.objects.filter(project__in=managed_projects).count(),
        'completed_tasks': Task.objects.filter(project__in=managed_projects, status='COMPLETED').count(),
        'pending_tasks': Task.objects.filter(project__in=managed_projects, status='PENDING').count(),
        'projects': managed_projects[:5],
        'recent_tasks': Task.objects.filter(project__in=managed_projects).order_by('-created_at')[:10],
        'team_performance': [],
    }
    
    return render(request, 'accounts/manager_dashboard.html', context)

@login_required
def admin_dashboard(request):
    """Dashboard for super admin"""
    if request.user.role != 'SUPER_ADMIN':
        return redirect('dashboard')
    
    context = {
        'total_users': User.objects.count(),
        'total_projects': Project.objects.count(),
        'total_tasks': Task.objects.count(),
        'total_managers': User.objects.filter(role='PROJECT_MANAGER').count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'recent_users': User.objects.order_by('-date_joined')[:10],
        'system_stats': {
            'projects_by_status': list(Project.objects.values('status').annotate(count=Count('id'))),
            'tasks_by_priority': list(Task.objects.values('priority').annotate(count=Count('id'))),
        }
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)