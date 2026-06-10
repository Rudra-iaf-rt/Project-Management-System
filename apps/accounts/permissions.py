# apps/accounts/permissions.py
from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    """
    Allow access only to super admins
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'SUPER_ADMIN'
    
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user.role == 'SUPER_ADMIN'


class IsProjectManager(permissions.BasePermission):
    """
    Allow access only to project managers and super admins
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['SUPER_ADMIN', 'PROJECT_MANAGER']
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'SUPER_ADMIN':
            return True
        if hasattr(obj, 'project_manager'):
            return obj.project_manager == request.user
        if hasattr(obj, 'team_lead'):
            return obj.team_lead == request.user
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Allow access only to object owner
    """
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return hasattr(obj, 'user') and obj.user == request.user


class IsTeamMember(permissions.BasePermission):
    """
    Allow access only to team members
    """
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'SUPER_ADMIN':
            return True
        if hasattr(obj, 'members'):
            return request.user in obj.members.all()
        if hasattr(obj, 'team_members'):
            return request.user in obj.team_members.all()
        return False


class IsAssignedUser(permissions.BasePermission):
    """
    Allow access only to assigned user (for tasks)
    """
    
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'SUPER_ADMIN':
            return True
        if hasattr(obj, 'assigned_to'):
            return obj.assigned_to == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False