# apps/chat/serializers.py
from rest_framework import serializers
from .models import ChatMessage
from apps.accounts.serializers import UserSerializer

class ChatMessageSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'team', 'message', 'timestamp', 'is_read', 'time_ago']
        read_only_fields = ['id', 'timestamp']
    
    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.timestamp)