# apps/accounts/tests.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.accounts.models import UserProfile, ActivityLog

User = get_user_model()

class AccountsTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            role='EMPLOYEE'
        )
        
    def test_user_creation(self):
        """Test that users are created correctly"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.role, 'EMPLOYEE')
        self.assertTrue(self.user.check_password('testpass123'))
    
    def test_user_profile_creation(self):
        """Test that user profile is created with user"""
        profile = UserProfile.objects.create(
            user=self.user,
            bio='Test bio',
            skills='Python, Django'
        )
        self.assertEqual(profile.user.username, 'testuser')
        self.assertEqual(profile.bio, 'Test bio')
    
    def test_login_view(self):
        """Test login functionality"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # Stays on login page
        self.assertContains(response, 'Invalid username or password')
    
    def test_logout_view(self):
        """Test logout functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)  # Redirect after logout
    
    def test_profile_view_authenticated(self):
        """Test profile view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
    
    def test_profile_view_unauthenticated(self):
        """Test profile view redirects unauthenticated users"""
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_activity_logging(self):
        """Test that user activities are logged"""
        self.client.login(username='testuser', password='testpass123')
        self.client.get(reverse('dashboard'))
        
        activity_exists = ActivityLog.objects.filter(
            user=self.user,
            action__icontains='dashboard'
        ).exists()
        self.assertTrue(activity_exists)
    
    def test_change_password(self):
        """Test password change functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('change_password'), {
            'old_password': 'testpass123',
            'new_password1': 'newpass123',
            'new_password2': 'newpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Test new password works
        self.client.logout()
        login_success = self.client.login(username='testuser', password='newpass123')
        self.assertTrue(login_success)