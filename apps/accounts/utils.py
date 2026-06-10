from django.core.mail import send_mail
from django.conf import settings
from .models import ActivityLog

def log_user_activity(user, action, request=None):
    """Helper function to log user activities"""
    ip_address = request.META.get('REMOTE_ADDR') if request else None
    ActivityLog.objects.create(
        user=user,
        action=action,
        ip_address=ip_address
    )

def send_welcome_email(user):
    """Send welcome email to new user"""
    subject = 'Welcome to Project Management System'
    message = f"""
    Hello {user.first_name},

    Welcome to our Project Management System!
    
    Your account has been created successfully.
    Username: {user.username}
    
    You can now log in and start managing your projects.
    
    Best regards,
    PMS Team
    """
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])