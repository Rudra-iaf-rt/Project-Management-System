from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, ActivityLog

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'department', 'is_active')
    list_filter = ('role', 'department', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone', 'department', 'designation', 'profile_picture')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone', 'department', 'designation')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)
admin.site.register(ActivityLog)