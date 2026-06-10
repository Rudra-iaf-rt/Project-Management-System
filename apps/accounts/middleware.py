# apps/accounts/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import ActivityLog
from django.urls import resolve
import re

class ActivityLoggingMiddleware(MiddlewareMixin):
    """Middleware to log user activities"""
    
    # Exclude paths from logging
    EXCLUDED_PATHS = [
        r'^/static/',
        r'^/media/',
        r'^/admin/jsi18n/',
    ]
    
    def process_request(self, request):
        # Store request start time
        request.start_time = timezone.now()
        return None
    
    def process_response(self, request, response):
        # Skip logging for excluded paths
        path = request.path
        for pattern in self.EXCLUDED_PATHS:
            if re.match(pattern, path):
                return response
        
        # Only log authenticated users
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Skip if already logged (to avoid duplicates)
            if getattr(request, '_activity_logged', False):
                return response
            
            # Determine action based on path and method
            action = self.get_action_from_request(request)
            
            # Don't log static file requests
            if not action:
                return response
            
            # Create activity log
            ActivityLog.objects.create(
                user=request.user,
                action=action,
                ip_address=self.get_client_ip(request),
                details=self.get_request_details(request, response)
            )
            
            request._activity_logged = True
        
        return response
    
    def get_action_from_request(self, request):
        """Extract meaningful action from request"""
        resolver_match = resolve(request.path)
        view_name = resolver_match.url_name if resolver_match else None
        
        if not view_name:
            return None
        
        # Map view names to user-friendly actions
        action_map = {
            'login': 'User logged in',
            'logout': 'User logged out',
            'profile': 'Viewed profile',
            'change_password': 'Changed password',
            'project_create': f'Created new project',
            'project_update': f'Updated project',
            'project_delete': f'Deleted project',
            'task_create': f'Created new task',
            'task_update': f'Updated task',
            'task_delete': f'Deleted task',
            'team_create': f'Created new team',
            'team_update': f'Updated team',
            'file_upload': f'Uploaded a file',
            'file_download': f'Downloaded a file',
            'file_delete': f'Deleted a file',
        }
        
        base_action = action_map.get(view_name, f'Accessed {view_name}')
        
        # Add HTTP method context
        if request.method == 'POST' and 'delete' not in view_name:
            return f"{base_action} (via {request.method})"
        
        return base_action
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_request_details(self, request, response):
        """Get additional request details for logging"""
        details = {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # Add POST data (excluding sensitive info)
        if request.method == 'POST' and request.POST:
            safe_data = {k: v for k, v in request.POST.items() 
                        if k not in ['password', 'csrfmiddlewaretoken']}
            details['post_data'] = safe_data
        
        return str(details)

class UserActivityMiddleware(MiddlewareMixin):
    """Update user's last activity timestamp"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Update last activity every hour
            now = timezone.now()
            if hasattr(request.user, 'last_activity'):
                if not request.user.last_activity or \
                   (now - request.user.last_activity).seconds > 3600:
                    request.user.last_activity = now
                    request.user.save(update_fields=['last_activity'])