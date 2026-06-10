# apps/accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
]