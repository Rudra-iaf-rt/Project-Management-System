from rest_framework import serializers
from apps.accounts.serializers import UserSerializer
from apps.projects.serializers import ProjectSerializer
from apps.teams.serializers import TeamSerializer
from .models import Meeting, MeetingParticipant, MeetingSettings, MeetingChat, MeetingRecording

class MeetingSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingSettings
        fields = ['waiting_room_enabled', 'lock_share_screen', 'lock_chat', 'mute_on_entry']

class MeetingParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MeetingParticipant
        fields = ['user', 'role', 'state', 'joined_at', 'left_at', 'hand_raised', 'camera_on', 'mic_on', 'screen_sharing']
        read_only_fields = ['joined_at', 'left_at']

class MeetingSerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    settings = MeetingSettingsSerializer(required=False)
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Meeting
        fields = ['id', 'meeting_code', 'title', 'description', 'start_time', 'duration_minutes', 'status', 'host', 'project', 'team', 'is_locked', 'settings', 'participant_count', 'created_at']
        read_only_fields = ['id', 'meeting_code', 'host', 'is_locked', 'created_at']

    def get_participant_count(self, obj):
        return obj.participants.filter(state='APPROVED').count()

    def create(self, validated_data):
        settings_data = validated_data.pop('settings', {})
        # Assign current host
        validated_data['host'] = self.context['request'].user
        
        # Generate clean meeting code if not set (format: xxx-yyyy-zzz)
        import random, string
        rand_str = lambda n: ''.join(random.choices(string.ascii_lowercase, k=n))
        validated_data['meeting_code'] = f"{rand_str(3)}-{rand_str(4)}-{rand_str(3)}"
        
        meeting = Meeting.objects.create(**validated_data)
        if settings_data:
            settings_instance = meeting.settings
            for attr, value in settings_data.items():
                setattr(settings_instance, attr, value)
            settings_instance.save()
        return meeting

    def update(self, instance, validated_data):
        settings_data = validated_data.pop('settings', {})
        
        # Update meeting
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update settings
        settings_instance = instance.settings
        for attr, value in settings_data.items():
            setattr(settings_instance, attr, value)
        settings_instance.save()
        
        return instance

class MeetingChatSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MeetingChat
        fields = ['id', 'meeting', 'user', 'message', 'file', 'timestamp']
        read_only_fields = ['id', 'user', 'timestamp']

class MeetingRecordingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeetingRecording
        fields = ['id', 'meeting', 'file', 'duration_seconds', 'created_at']
        read_only_fields = ['id', 'created_at']
