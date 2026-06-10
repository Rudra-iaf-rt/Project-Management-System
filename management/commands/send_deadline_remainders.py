# management/commands/send_deadline_reminders.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.tasks.models import Task
from apps.notifications.models import Notification
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

class Command(BaseCommand):
    help = 'Send deadline reminders for tasks due in 1, 3, or 7 days'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            help='Send reminders for tasks due in specific days'
        )
    
    def handle(self, *args, **options):
        today = timezone.now()
        days = options.get('days', None)
        
        if days:
            reminder_days = [days]
        else:
            reminder_days = [1, 3, 7]
        
        total_notifications = 0
        total_emails = 0
        
        for days_until_deadline in reminder_days:
            deadline_date = today + timedelta(days=days_until_deadline)
            deadline_end = deadline_date + timedelta(days=1)
            
            tasks = Task.objects.filter(
                deadline__range=(deadline_date, deadline_end),
                status__in=['PENDING', 'IN_PROGRESS']
            )
            
            for task in tasks:
                # Create notification
                Notification.objects.create(
                    user=task.assigned_to,
                    title=f'⏰ Deadline Reminder: {task.title}',
                    message=f'Task "{task.title}" is due in {days_until_deadline} day(s). Please complete it on time.',
                    notification_type='DEADLINE_REMINDER',
                    link=f'/tasks/{task.id}/'
                )
                total_notifications += 1
                
                # Send email if user has email
                if task.assigned_to.email:
                    html_message = render_to_string('email/deadline_reminder.html', {
                        'user': task.assigned_to,
                        'tasks': [task],
                        'days': days_until_deadline,
                        'site_url': settings.SITE_URL
                    })
                    
                    send_mail(
                        f'Task Deadline Reminder: {task.title}',
                        f'Your task "{task.title}" is due in {days_until_deadline} day(s).',
                        settings.DEFAULT_FROM_EMAIL,
                        [task.assigned_to.email],
                        html_message=html_message,
                        fail_silently=True
                    )
                    total_emails += 1
                
                self.stdout.write(
                    self.style.SUCCESS(f'Reminder sent for task: {task.title}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully sent {total_notifications} notifications and {total_emails} emails'
            )
        )