from django.contrib import admin
from .models import ChatMessage

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'message', 'timestamp', 'is_read']
    list_filter = ['is_read', 'timestamp']