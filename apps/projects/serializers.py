# apps/projects/serializers.py
from rest_framework import serializers
from .models import Project
from apps.accounts.serializers import UserSerializer
from apps.tasks.serializers import TaskSerializer

class ProjectSerializer(serializers.ModelSerializer):
    progress = serializers.IntegerField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    project_manager_name = serializers.CharField(source='project_manager.username', read_only=True)
    tasks = TaskSerializer(many=True, read_only=True)
    team_members = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']