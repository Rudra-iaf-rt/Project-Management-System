from django.contrib import admin
from .models import Team, TeamRole

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'team_lead', 'member_count', 'created_at']
    search_fields = ['name', 'description']

@admin.register(TeamRole)
class TeamRoleAdmin(admin.ModelAdmin):
    list_display = ['team', 'user', 'role']
    list_filter = ['role']