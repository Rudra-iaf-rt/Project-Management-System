import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from apps.accounts.models import User
from .models import Meeting, MeetingParticipant, MeetingChat, MeetingSettings

class MeetingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.meeting_code = self.scope['url_route']['kwargs']['meeting_code']
        self.room_group_name = f'meeting_{self.meeting_code}'
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
            
        # Get or create participant record in DB
        self.participant = await self.get_or_create_participant()
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        # If participant is approved (or no waiting room), notify others
        if self.participant.state == 'APPROVED':
            await self.notify_join()

    async def disconnect(self, close_code):
        # Leave channel group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Mark as LEFT in DB
        await self.set_participant_left()
        
        # Notify others
        if hasattr(self, 'participant') and self.participant.state == 'APPROVED':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'participant_left',
                    'username': self.user.username,
                }
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        
        if action == 'signal':
            # Peer-to-peer WebRTC signaling (SDP or ICE)
            target = data.get('target')
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'webrtc_signal',
                    'sender': self.user.username,
                    'target': target,
                    'signal': data.get('signal'),
                }
            )
            
        elif action == 'state_change':
            # Camera, Mic, Screen Share, or Hand Raise toggle
            state_data = data.get('state', {})
            await self.update_participant_state(state_data)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'participant_state_updated',
                    'username': self.user.username,
                    'state': state_data,
                }
            )
            
        elif action == 'chat':
            # In-meeting chat
            message = data.get('message', '')
            chat_obj = await self.save_chat_message(message)
            if chat_obj:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'id': chat_obj['id'],
                        'username': self.user.username,
                        'message': message,
                        'timestamp': chat_obj['timestamp'],
                    }
                )
                
        elif action == 'host_command':
            # Commands executed by host (mute participant, remove user, end meeting, toggle locks)
            command = data.get('command')
            target_user = data.get('target')
            
            # Verify host permission
            is_host = await self.verify_is_host()
            if not is_host:
                return
                
            if command == 'mute_participant':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'mute_remote_participant',
                        'target': target_user,
                    }
                )
            elif command == 'remove_participant':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'kick_remote_participant',
                        'target': target_user,
                    }
                )
            elif command == 'approve_entry':
                await self.approve_waiting_room_entry(target_user)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'waiting_room_approved',
                        'target': target_user,
                    }
                )
            elif command == 'reject_entry':
                await self.reject_waiting_room_entry(target_user)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'waiting_room_rejected',
                        'target': target_user,
                    }
                )
            elif command == 'end_meeting':
                await self.end_meeting_session()
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'meeting_ended',
                    }
                )
            elif command == 'toggle_lock':
                locked_status = await self.toggle_meeting_lock()
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'lock_status_changed',
                        'is_locked': locked_status,
                    }
                )

    # Group Send Handlers
    async def webrtc_signal(self, event):
        # Only forward signal if it matches the target recipient
        if event['target'] == self.user.username:
            await self.send(text_data=json.dumps({
                'action': 'signal',
                'sender': event['sender'],
                'signal': event['signal']
            }))

    async def participant_joined(self, event):
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'action': 'participant_joined',
                'username': event['username'],
                'role': event['role'],
                'state': event['state']
            }))

    async def participant_left(self, event):
        await self.send(text_data=json.dumps({
            'action': 'participant_left',
            'username': event['username']
        }))

    async def participant_state_updated(self, event):
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'action': 'state_change',
                'username': event['username'],
                'state': event['state']
            }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'action': 'chat',
            'id': event['id'],
            'username': event['username'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))

    async def mute_remote_participant(self, event):
        if event['target'] == self.user.username:
            await self.send(text_data=json.dumps({
                'action': 'mute_mic'
            }))

    async def kick_remote_participant(self, event):
        if event['target'] == self.user.username:
            await self.send(text_data=json.dumps({
                'action': 'kicked'
            }))
            await self.close()

    async def waiting_room_approved(self, event):
        if event['target'] == self.user.username:
            # Participant is approved; update role and notify others
            self.participant = await self.get_or_create_participant()
            await self.notify_join()
            await self.send(text_data=json.dumps({
                'action': 'approved_entry'
            }))
        else:
            # Inform others about the entry approval
            await self.send(text_data=json.dumps({
                'action': 'participant_approved_status',
                'username': event['target']
            }))

    async def waiting_room_rejected(self, event):
        if event['target'] == self.user.username:
            await self.send(text_data=json.dumps({
                'action': 'rejected_entry'
            }))
            await self.close()

    async def meeting_ended(self, event):
        await self.send(text_data=json.dumps({
            'action': 'meeting_ended'
        }))
        await self.close()

    async def lock_status_changed(self, event):
        await self.send(text_data=json.dumps({
            'action': 'lock_status',
            'is_locked': event['is_locked']
        }))

    # Helper Database Accessors
    @database_sync_to_async
    def get_or_create_participant(self):
        meeting = Meeting.objects.get(meeting_code=self.meeting_code)
        is_host = meeting.host == self.user
        
        # Determine starting state based on settings
        initial_state = 'APPROVED'
        if not is_host:
            settings, _ = MeetingSettings.objects.get_or_create(meeting=meeting)
            if settings.waiting_room_enabled:
                initial_state = 'WAITING'
        else:
            initial_state = 'APPROVED'
            
        participant, created = MeetingParticipant.objects.get_or_create(
            meeting=meeting,
            user=self.user,
            defaults={
                'role': 'HOST' if is_host else 'PARTICIPANT',
                'state': initial_state,
                'joined_at': timezone.now() if initial_state == 'APPROVED' else None
            }
        )
        if not created and participant.state == 'LEFT':
            participant.state = initial_state
            participant.joined_at = timezone.now() if initial_state == 'APPROVED' else None
            participant.save()
            
        return participant

    @database_sync_to_async
    def set_participant_left(self):
        try:
            participant = MeetingParticipant.objects.get(meeting__meeting_code=self.meeting_code, user=self.user)
            participant.state = 'LEFT'
            participant.left_at = timezone.now()
            participant.save()
        except MeetingParticipant.DoesNotExist:
            pass

    @database_sync_to_async
    def update_participant_state(self, state):
        try:
            p = MeetingParticipant.objects.get(meeting__meeting_code=self.meeting_code, user=self.user)
            if 'camera' in state:
                p.camera_on = state['camera']
            if 'mic' in state:
                p.mic_on = state['mic']
            if 'screen' in state:
                p.screen_sharing = state['screen']
            if 'hand' in state:
                p.hand_raised = state['hand']
            p.save()
        except MeetingParticipant.DoesNotExist:
            pass

    @database_sync_to_async
    def save_chat_message(self, msg):
        try:
            meeting = Meeting.objects.get(meeting_code=self.meeting_code)
            chat = MeetingChat.objects.create(
                meeting=meeting,
                user=self.user,
                message=msg
            )
            return {
                'id': chat.id,
                'timestamp': chat.timestamp.isoformat()
            }
        except Exception:
            return None

    @database_sync_to_async
    def verify_is_host(self):
        try:
            meeting = Meeting.objects.get(meeting_code=self.meeting_code)
            return meeting.host == self.user
        except Meeting.DoesNotExist:
            return False

    @database_sync_to_async
    def approve_waiting_room_entry(self, username):
        try:
            p = MeetingParticipant.objects.get(meeting__meeting_code=self.meeting_code, user__username=username)
            p.state = 'APPROVED'
            p.joined_at = timezone.now()
            p.save()
        except MeetingParticipant.DoesNotExist:
            pass

    @database_sync_to_async
    def reject_waiting_room_entry(self, username):
        try:
            p = MeetingParticipant.objects.get(meeting__meeting_code=self.meeting_code, user__username=username)
            p.state = 'REJECTED'
            p.save()
        except MeetingParticipant.DoesNotExist:
            pass

    @database_sync_to_async
    def end_meeting_session(self):
        try:
            meeting = Meeting.objects.get(meeting_code=self.meeting_code)
            meeting.status = 'COMPLETED'
            meeting.save()
        except Meeting.DoesNotExist:
            pass

    @database_sync_to_async
    def toggle_meeting_lock(self):
        try:
            meeting = Meeting.objects.get(meeting_code=self.meeting_code)
            meeting.is_locked = not meeting.is_locked
            meeting.save()
            return meeting.is_locked
        except Meeting.DoesNotExist:
            return False

    async def notify_join(self):
        role_label = 'Host' if self.participant.role == 'HOST' else 'Participant'
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'participant_joined',
                'username': self.user.username,
                'role': role_label,
                'state': {
                    'camera': self.participant.camera_on,
                    'mic': self.participant.mic_on,
                    'screen': self.participant.screen_sharing,
                    'hand': self.participant.hand_raised
                }
            }
        )
