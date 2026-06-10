# apps/reports/serializers.py
from rest_framework import serializers
from .models import Report

class ReportSerializer(serializers.ModelSerializer):
    generated_by_name = serializers.CharField(source='generated_by.username', read_only=True)
    
    class Meta:
        model = Report
        fields = ['id', 'name', 'report_type', 'generated_by', 'generated_by_name', 
                  'filters', 'file', 'created_at']
        read_only_fields = ['id', 'created_at', 'generated_by']