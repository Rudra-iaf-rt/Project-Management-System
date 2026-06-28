from django.test import TestCase
from django.utils import timezone
from apps.accounts.models import User
from apps.meetings.models import Meeting, MeetingParticipant, MeetingSettings

class MeetingModelTests(TestCase):
    def setUp(self):
        self.host = User.objects.create_user(username='testhost', password='password123', role='PROJECT_MANAGER')
        self.participant = User.objects.create_user(username='testparticipant', password='password123', role='EMPLOYEE')
        
    def test_meeting_creation(self):
        meeting = Meeting.objects.create(
            meeting_code='test-call-123',
            title='Test Sprint Sync',
            start_time=timezone.now(),
            host=self.host
        )
        # Verify settings were automatically created by signal
        settings = MeetingSettings.objects.get(meeting=meeting)
        self.assertEqual(meeting.title, 'Test Sprint Sync')
        self.assertEqual(meeting.host, self.host)
        self.assertTrue(settings.waiting_room_enabled)

    def test_meeting_participant_state(self):
        meeting = Meeting.objects.create(
            meeting_code='test-call-456',
            title='Test Standup',
            start_time=timezone.now(),
            host=self.host
        )
        p = MeetingParticipant.objects.create(
            meeting=meeting,
            user=self.participant,
            role='PARTICIPANT',
            state='APPROVED'
        )
        self.assertEqual(p.state, 'APPROVED')
