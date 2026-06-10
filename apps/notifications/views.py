from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification

@login_required
def notification_list(request):
    """List all notifications for the user"""
    notifications = Notification.objects.filter(user=request.user)
    
    # Mark all as read if requested
    if request.GET.get('mark_all_read'):
        notifications.update(is_read=True)
        return JsonResponse({'success': True})
    
    context = {
        'notifications': notifications[:50],
        'unread_count': notifications.filter(is_read=False).count(),
    }
    return render(request, 'notifications/notification_list.html', context)

@login_required
def mark_as_read(request, pk):
    """Mark a single notification as read"""
    if request.method == 'POST':
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=400)

@login_required
def get_notifications_api(request):
    """API endpoint for fetching notifications (for AJAX)"""
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:10]
    
    data = {
        'count': notifications.count(),
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.notification_type,
                'link': n.link,
                'created_at': n.created_at.isoformat(),
            }
            for n in notifications
        ]
    }
    
    return JsonResponse(data)