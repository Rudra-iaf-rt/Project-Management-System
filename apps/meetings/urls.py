from django.urls import path
from . import views

urlpatterns = [
    path('', views.meeting_dashboard, name='meeting_dashboard'),
    path('room/<str:meeting_code>/', views.meeting_room, name='meeting_room'),
    path('preview/<str:meeting_code>/', views.meeting_preview, name='meeting_preview'),
]
