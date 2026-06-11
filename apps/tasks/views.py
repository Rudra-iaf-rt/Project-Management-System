from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Task
from .forms import TaskForm, TaskUpdateForm
from apps.notifications.utils import send_task_notification

@login_required
def task_list(request):
    """List tasks based on user role"""
    if request.user.role == 'SUPER_ADMIN':
        tasks = Task.objects.all()
    elif request.user.role == 'PROJECT_MANAGER':
        tasks = Task.objects.filter(project__project_manager=request.user)
    else:
        tasks = Task.objects.filter(assigned_to=request.user)
    
    # Filters
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    search_query = request.GET.get('search', '')
    
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
    if search_query:
        tasks = tasks.filter(Q(title__icontains=search_query) | Q(description__icontains=search_query))
    
    # Pagination
    paginator = Paginator(tasks, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'tasks': page_obj,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
        'total_tasks': tasks.count(),
        'completed_tasks': tasks.filter(status='COMPLETED').count(),
        'pending_tasks': tasks.filter(status='PENDING').count(),
        'overdue_tasks': tasks.filter(deadline__lt=timezone.now(), status__in=['PENDING', 'IN_PROGRESS']).count(),
    }
    return render(request, 'tasks/task_list.html', context)

@login_required
def task_detail(request, pk):
    """Task details view"""
    task = get_object_or_404(Task, pk=pk)
    
    # Check permissions
    if request.user.role not in ['SUPER_ADMIN'] and \
       request.user != task.assigned_to and \
       request.user != task.project.project_manager:
        messages.error(request, 'You do not have permission to view this task.')
        return redirect('task_list')
    
    context = {
        'task': task,
        'can_edit': request.user.role in ['SUPER_ADMIN', 'PROJECT_MANAGER'] or request.user == task.assigned_to,
    }
    return render(request, 'tasks/task_detail.html', context)

@login_required
def task_create(request):
    """Create new task"""
    if request.user.role not in ['SUPER_ADMIN', 'PROJECT_MANAGER']:
        messages.error(request, 'You do not have permission to create tasks.')
        return redirect('task_list')
    
    if request.method == 'POST':
        form = TaskForm(request.user, request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.assigned_by = request.user
            task.save()
            
            # Send notification to assigned user
            send_task_notification(task, 'assigned')
            
            messages.success(request, f'Task "{task.title}" created and assigned to {task.assigned_to.username}!')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskForm(request.user)
    
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Create Task'})

@login_required
def task_update(request, pk):
    """Update task"""
    task = get_object_or_404(Task, pk=pk)
    
    if request.user.role not in ['SUPER_ADMIN', 'PROJECT_MANAGER'] and request.user != task.assigned_to:
        messages.error(request, 'You do not have permission to edit this task.')
        return redirect('task_list')
    
    if request.method == 'POST':
        form = TaskUpdateForm(request.POST, instance=task)
        if form.is_valid():
            old_status = task.status
            task = form.save()
            
            # Send notification if status changed
            if old_status != task.status:
                send_task_notification(task, f'status_changed_to_{task.status}')
            
            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect('task_detail', pk=task.pk)
    else:
        form = TaskUpdateForm(instance=task)
    
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Update Task', 'task': task})

@login_required
def task_delete(request, pk):
    """Delete task"""
    task = get_object_or_404(Task, pk=pk)
    
    if request.user.role not in ['SUPER_ADMIN', 'PROJECT_MANAGER']:
        messages.error(request, 'You do not have permission to delete this task.')
        return redirect('task_list')
    
    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, f'Task "{task_title}" deleted successfully!')
        return redirect('task_list')
    
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})

@login_required
def update_task_status(request, pk):
    """AJAX endpoint to update task status (for Kanban board)"""
    if request.method == 'POST':
        task = get_object_or_404(Task, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(Task.STATUS_CHOICES).keys():
            old_status = task.status
            task.status = new_status
            
            if new_status == 'COMPLETED':
                task.completed_at = timezone.now()
            
            task.save()
            
            # Send notification
            if old_status != new_status:
                send_task_notification(task, f'status_changed_to_{new_status}')
            
            return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=400)

    # apps/tasks/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Task

@login_required
def kanban_board(request):
    """Kanban board view for task management"""
    user = request.user
    
    # Get tasks based on user role
    if user.role == 'SUPER_ADMIN':
        tasks = Task.objects.all()
    elif user.role == 'PROJECT_MANAGER':
        tasks = Task.objects.filter(project__project_manager=user)
    else:  # EMPLOYEE
        tasks = Task.objects.filter(assigned_to=user)
    
    # Organize tasks by status
    context = {
        'pending_tasks': tasks.filter(status='PENDING'),
        'in_progress_tasks': tasks.filter(status='IN_PROGRESS'),
        'testing_tasks': tasks.filter(status='TESTING'),
        'completed_tasks': tasks.filter(status='COMPLETED'),
    }
    
    return render(request, 'tasks/kanban_board.html', context)