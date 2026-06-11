# apps/tasks/serializers.py
from rest_framework import serializers
from .models import Task
from apps.accounts.serializers import UserSerializer

class TaskSerializer(serializers.ModelSerializer):
    is_overdue = serializers.BooleanField(read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.username', read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at', 'assigned_by']