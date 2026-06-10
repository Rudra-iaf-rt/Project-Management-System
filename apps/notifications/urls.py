from django.urls import path
from . import views

urlpatterns = [
    path('', views.notification_list, name='notification_list'),
    path('<int:pk>/mark-read/', views.mark_as_read, name='mark_notification_read'),
    path('api/unread/', views.get_notifications_api, name='api_notifications'),
]