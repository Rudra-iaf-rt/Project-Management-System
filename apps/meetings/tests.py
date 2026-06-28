from django.test import TestCase
from rest_framework.test import APITestCase
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

class MeetingAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', password='password123', role='PROJECT_MANAGER')
        self.client.force_authenticate(user=self.user)

    def test_create_instant_meeting_api(self):
        payload = {
            "title": "Instant Test Meeting",
            "description": "API Instant test call",
            "start_time": timezone.now().isoformat(),
            "duration_minutes": 45
        }
        response = self.client.post('/api/meetings/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('meeting_code', response.data)
