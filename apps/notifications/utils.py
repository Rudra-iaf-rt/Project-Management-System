from .models import Notification

def send_task_notification(task, action):
    """Helper function to send task notifications"""
    if action == 'assigned':
        title = f'New Task: {task.title}'
        message = f'You have been assigned to task "{task.title}" in project {task.project.name}. Deadline: {task.deadline}'
    elif action == 'status_changed_to_COMPLETED':
        title = f'Task Completed: {task.title}'
        message = f'Task "{task.title}" has been marked as completed.'
    else:
        title = f'Task Updated: {task.title}'
        message = f'Task "{task.title}" status changed.'
    
    Notification.objects.create(
        user=task.assigned_to,
        title=title,
        message=message,
        notification_type='TASK_UPDATED',
        link=f'/tasks/{task.id}/'
    )