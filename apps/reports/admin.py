from django.contrib import admin
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'report_type', 'generated_by', 'created_at']
    list_filter = ['report_type', 'created_at']
    search_fields = ['name']
    readonly_fields = ['generated_by', 'created_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('name', 'report_type', 'filters')
        }),
        ('File Information', {
            'fields': ('file',)
        }),
        ('Metadata', {
            'fields': ('generated_by', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.generated_by = request.user
        super().save_model(request, obj, form, change)