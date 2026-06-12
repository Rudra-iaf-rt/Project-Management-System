from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_index, name='chat_index'),  # Team selection
    path('<int:team_id>/', views.chat_room, name='chat_room'),
    path('api/send/', views.send_message_api, name='send_message_api'),
    path('api/history/<int:team_id>/', views.chat_history_api, name='chat_history_api'),
    path('api/mark-read/<int:team_id>/', views.chat_mark_read_api, name='chat_mark_read_api'),
]