from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User, ActivityLog
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.teams.models import Team
from apps.notifications.models import Notification
from apps.chat.models import ChatMessage
from django.utils import timezone
from datetime import date, timedelta
from rest_framework.test import APITestCase
import json

class WebE2ETests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword',
            role='SUPER_ADMIN'
        )
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='managerpassword',
            role='PROJECT_MANAGER'
        )
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@example.com',
            password='employeepassword',
            role='EMPLOYEE'
        )

        self.project = Project.objects.create(
            name='E2E Web Project',
            description='Audit project description',
            project_code='AUDIT-E2E',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            priority='HIGH',
            status='IN_PROGRESS',
            project_manager=self.manager
        )

    def test_authentication_and_dashboards(self):
        # 1. Test custom Login view
        response = self.client.post(reverse('login'), {
            'username': 'admin',
            'password': 'adminpassword'
        })
        self.assertEqual(response.status_code, 302)
        # Should redirect to admin_dashboard for SUPER_ADMIN
        self.assertRedirects(response, reverse('admin_dashboard'))

        # Check ActivityLog was created
        self.assertTrue(ActivityLog.objects.filter(user=self.admin, action='User logged in').exists())

        # Test Admin Dashboard renders
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

        # Logout
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(ActivityLog.objects.filter(user=self.admin, action='User logged out').exists())

    def test_project_member_management(self):
        # Login manager
        self.client.login(username='manager', password='managerpassword')

        # Test project detail renders can_edit = True
        response = self.client.get(reverse('project_detail', args=[self.project.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['can_edit'])

        # Test project assign members page GET
        response = self.client.get(reverse('project_assign', args=[self.project.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'employee')

        # Test project assign POST
        response = self.client.post(reverse('project_assign', args=[self.project.id]), {
            'members': [self.employee.id]
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.project.team_members.filter(id=self.employee.id).exists())

        # Test project remove member
        response = self.client.get(reverse('project_remove_member', args=[self.project.id, self.employee.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.project.team_members.filter(id=self.employee.id).exists())


class APIIntegrationTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username='admin_api',
            email='admin_api@example.com',
            password='adminpassword',
            role='SUPER_ADMIN'
        )
        self.employee = User.objects.create_user(
            username='employee_api',
            email='employee_api@example.com',
            password='employeepassword',
            role='EMPLOYEE'
        )
        response = self.client.post('/api/token/', {
            'username': 'admin_api',
            'password': 'adminpassword'
        })
        self.access_token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

        self.project = Project.objects.create(
            name='API Project',
            description='API Test Project',
            project_code='API-101',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=15),
            priority='LOW',
            status='PENDING',
            project_manager=self.admin
        )

    def test_task_operations_and_decimal_math(self):
        # 1. Create task via API
        task_data = {
            'title': 'API E2E Task',
            'description': 'Description',
            'project': self.project.id,
            'assigned_to': self.employee.id,
            'priority': 'MEDIUM',
            'status': 'PENDING',
            'deadline': (timezone.now() + timedelta(days=2)).isoformat(),
            'estimated_hours': '10.50'
        }
        response = self.client.post('/api/tasks/', task_data)
        self.assertEqual(response.status_code, 201)
        task_id = response.data['id']

        # 2. Log actual hours spent (validates decimal conversion logic)
        response = self.client.post(f'/api/tasks/{task_id}/log_time/', {'hours': '3.25'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(float(response.data['actual_hours']), 3.25)
        
        # 3. Update task status
        response = self.client.post(f'/api/tasks/{task_id}/update_status/', {'status': 'COMPLETED'})
        self.assertEqual(response.status_code, 200)

        # 4. Generate Reports view responses
        response = self.client.post('/api/reports/project/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        response = self.client.post('/api/reports/task/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
