# apps/reports/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports_dashboard'),
    path('project-report/', views.generate_project_report, name='project_report'),
    path('task-report/', views.generate_task_report, name='task_report'),
    path('employee-performance/', views.employee_performance_report, name='employee_performance'),
]