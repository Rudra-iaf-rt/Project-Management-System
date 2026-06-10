# apps/notifications/tasks.py
from celery import shared_task
from apps.notifications.models import Notification
from datetime import datetime, timedelta

@shared_task
def cleanup_old_notifications():
    """Delete notifications older than 30 days"""
    threshold_date = datetime.now() - timedelta(days=30)
    old_notifications = Notification.objects.filter(created_at__lt=threshold_date)
    count = old_notifications.count()
    old_notifications.delete()
    return f"Deleted {count} old notifications"

@shared_task
def send_bulk_notification(user_ids, title, message, notification_type, link=''):
    """Send bulk notifications to multiple users"""
    from apps.accounts.models import User
    users = User.objects.filter(id__in=user_ids)
    
    notifications = []
    for user in users:
        notifications.append(
            Notification(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                link=link
            )
        )
    
    Notification.objects.bulk_create(notifications)
    return f"Sent {len(notifications)} notifications"