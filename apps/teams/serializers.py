# apps/teams/serializers.py
from rest_framework import serializers
from .models import Team, TeamRole
from apps.accounts.serializers import UserSerializer

class TeamRoleSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = TeamRole
        fields = ['id', 'user', 'role']

class TeamSerializer(serializers.ModelSerializer):
    team_lead_name = serializers.CharField(source='team_lead.username', read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    roles = TeamRoleSerializer(many=True, read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'team_lead', 'team_lead_name', 
                  'members', 'member_count', 'roles', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']