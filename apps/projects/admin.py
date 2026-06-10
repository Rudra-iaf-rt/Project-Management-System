from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'project_code', 'status', 'priority', 'project_manager', 'progress']
    list_filter = ['status', 'priority', 'start_date']
    search_fields = ['name', 'project_code', 'description']