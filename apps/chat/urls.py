from django.urls import path
from . import views

urlpatterns = [
    path('<int:team_id>/', views.chat_room, name='chat_room'),
    path('api/send/', views.send_message_api, name='send_message_api'),
]