from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Project
from .forms import ProjectForm
from apps.tasks.models import Task
from apps.accounts.models import User

@login_required
def project_list(request):
    """List all projects for the user"""
    if request.user.role == 'SUPER_ADMIN':
        projects = Project.objects.all()
    elif request.user.role == 'PROJECT_MANAGER':
        projects = Project.objects.filter(project_manager=request.user)
    else:
        projects = Project.objects.filter(team_members=request.user)
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |
            Q(project_code__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(projects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'projects': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_projects': projects.count(),
        'completed_projects': projects.filter(status='COMPLETED').count(),
        'in_progress_projects': projects.filter(status='IN_PROGRESS').count(),
    }
    return render(request, 'projects/project_list.html', context)

@login_required
def project_detail(request, pk):
    """Project details view"""
    project = get_object_or_404(Project, pk=pk)
    
    # Check permissions
    if request.user.role not in ['SUPER_ADMIN'] and \
       request.user != project.project_manager and \
       request.user not in project.team_members.all():
        messages.error(request, 'You do not have permission to view this project.')
        return redirect('project_list')
    
    # Get project tasks
    tasks = project.tasks.all()
    
    # Task statistics
    task_stats = {
        'total': tasks.count(),
        'pending': tasks.filter(status='PENDING').count(),
        'in_progress': tasks.filter(status='IN_PROGRESS').count(),
        'testing': tasks.filter(status='TESTING').count(),
        'completed': tasks.filter(status='COMPLETED').count(),
    }
    
    can_edit = request.user.role == 'SUPER_ADMIN' or request.user == project.project_manager
    
    context = {
        'project': project,
        'tasks': tasks[:10],
        'task_stats': task_stats,
        'team_members': project.team_members.all(),
        'progress': project.progress,
        'can_edit': can_edit,
    }
    return render(request, 'projects/project_detail.html', context)

@login_required
def project_create(request):
    """Create new project"""
    if request.user.role not in ['SUPER_ADMIN', 'PROJECT_MANAGER']:
        messages.error(request, 'You do not have permission to create projects.')
        return redirect('project_list')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.project_manager = request.user
            project.save()
            form.save_m2m()  # Save many-to-many relationships
            
            messages.success(request, f'Project "{project.name}" created successfully!')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm()
    
    return render(request, 'projects/project_form.html', {'form': form, 'title': 'Create Project'})

@login_required
def project_update(request, pk):
    """Update project"""
    project = get_object_or_404(Project, pk=pk)
    
    if request.user.role not in ['SUPER_ADMIN'] and request.user != project.project_manager:
        messages.error(request, 'You do not have permission to edit this project.')
        return redirect('project_list')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Project "{project.name}" updated successfully!')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'projects/project_form.html', {'form': form, 'title': 'Update Project', 'project': project})

@login_required
def project_delete(request, pk):
    """Delete project"""
    project = get_object_or_404(Project, pk=pk)
    
    if request.user.role != 'SUPER_ADMIN' and request.user != project.project_manager:
        messages.error(request, 'You do not have permission to delete this project.')
        return redirect('project_list')
    
    if request.method == 'POST':
        project_name = project.name
        project.delete()
        messages.success(request, f'Project "{project_name}" deleted successfully!')
        return redirect('project_list')
    
    return render(request, 'projects/project_delete.html', {'project': project})

@login_required
def project_assign(request, pk):
    """Assign team members to project"""
    project = get_object_or_404(Project, pk=pk)
    
    # Check permissions (only super admin or project manager can assign)
    if request.user.role not in ['SUPER_ADMIN'] and request.user != project.project_manager:
        messages.error(request, 'You do not have permission to manage members for this project.')
        return redirect('project_detail', pk=project.pk)
    
    if request.method == 'POST':
        member_ids = request.POST.getlist('members')
        # Add new members
        for m_id in member_ids:
            try:
                user = User.objects.get(id=m_id, role='EMPLOYEE')
                project.team_members.add(user)
            except User.DoesNotExist:
                pass
        messages.success(request, 'Members added successfully!')
        return redirect('project_assign', pk=project.pk)
        
    # Get users who are employees, and not already in team_members
    available_users = User.objects.filter(role='EMPLOYEE').exclude(id__in=project.team_members.all())
    
    context = {
        'project': project,
        'available_users': available_users,
    }
    return render(request, 'projects/project_assign.html', context)

@login_required
def project_remove_member(request, project_id, member_id):
    """Remove team member from project"""
    project = get_object_or_404(Project, pk=project_id)
    
    if request.user.role not in ['SUPER_ADMIN'] and request.user != project.project_manager:
        messages.error(request, 'You do not have permission to manage members for this project.')
        return redirect('project_detail', pk=project.pk)
        
    member = get_object_or_404(User, id=member_id)
    project.team_members.remove(member)
    messages.success(request, f'Member "{member.get_full_name()}" removed successfully!')
    return redirect('project_assign', pk=project.pk)