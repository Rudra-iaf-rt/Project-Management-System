# apps/accounts/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from apps.accounts.models import User

@shared_task
def send_welcome_email(user_id):
    """Send welcome email to new user"""
    try:
        user = User.objects.get(id=user_id)
        subject = 'Welcome to Project Management System'
        html_message = render_to_string('email/welcome.html', {
            'user': user,
            'site_url': settings.SITE_URL
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False
        )
        return f"Welcome email sent to {user.email}"
    except User.DoesNotExist:
        return f"User {user_id} not found"

@shared_task
def send_password_reset_email(user_id, reset_link):
    """Send password reset email"""
    try:
        user = User.objects.get(id=user_id)
        subject = 'Password Reset Request'
        html_message = render_to_string('email/password_reset.html', {
            'user': user,
            'reset_link': reset_link,
            'site_url': settings.SITE_URL
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False
        )
        return f"Password reset email sent to {user.email}"
    except User.DoesNotExist:
        return f"User {user_id} not found"

@shared_task
def cleanup_inactive_users():
    """Deactivate users who haven't logged in for 90 days"""
    from datetime import datetime, timedelta
    threshold_date = datetime.now() - timedelta(days=90)
    inactive_users = User.objects.filter(
        last_login__lt=threshold_date,
        is_active=True
    )
    count = inactive_users.update(is_active=False)
    return f"Deactivated {count} inactive users"