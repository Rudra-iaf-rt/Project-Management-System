import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms.settings')

app = Celery('pms')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'send-deadline-reminders': {
        'task': 'apps.projects.tasks.check_deadline_reminders',
        'schedule': crontab(hour=9, minute=0),  # daily at 9 AM
    },
    'cleanup-old-notifications': {
        'task': 'apps.notifications.tasks.cleanup_old_notifications',
        'schedule': crontab(day_of_month=1, hour=0, minute=0),  # monthly
    },
    'update-project-progress': {
        'task': 'apps.projects.tasks.update_project_progress',
        'schedule': crontab(minute='*/30'),  # every 30 minutes
    },
}