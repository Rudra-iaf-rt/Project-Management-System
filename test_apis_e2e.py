from rest_framework.test import APITestCase
from django.urls import reverse
from apps.accounts.models import User
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.teams.models import Team
from apps.notifications.models import Notification
from apps.chat.models import ChatMessage
from django.utils import timezone
from datetime import timedelta
import json

class E2EAPITests(APITestCase):
    def setUp(self):
        # Create users
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

        # Get JWT tokens for authentication
        # Login admin
        response = self.client.post('/api/token/', {
            'username': 'admin',
            'password': 'adminpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.admin_access = response.data['access']

        # Login employee
        response = self.client.post('/api/token/', {
            'username': 'employee',
            'password': 'employeepassword'
        })
        self.assertEqual(response.status_code, 200)
        self.employee_access = response.data['access']

    def test_end_to_end_workflow(self):
        # We will run an end-to-end simulation of all features
        print("\n--- Starting End-to-End API Verification ---")
        
        # Set authorization header to Admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_access}')
        
        # 1. Profile / Users
        print("Testing User/Profile API...")
        response = self.client.get('/api/users/')
        self.assertEqual(response.status_code, 200)
        print("  - List Users success")
        
        response = self.client.get('/api/users/me/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'admin')
        print("  - Get Me success")
        
        response = self.client.put('/api/users/update_me/', {'first_name': 'Super', 'last_name': 'Admin'})
        self.assertEqual(response.status_code, 200)
        print("  - Update Me success")
        
        response = self.client.get('/api/profile/my_profile/')
        self.assertEqual(response.status_code, 200)
        print("  - Get Profile success")
        
        response = self.client.put('/api/profile/my_profile/', {'bio': 'System Administrator'})
        self.assertEqual(response.status_code, 200)
        print("  - Update Profile success")
        
        # 2. Projects
        print("Testing Projects API...")
        project_data = {
            'name': 'E2E Testing Project',
            'description': 'End-to-End API validation',
            'project_code': 'E2E-101',
            'start_date': '2026-06-11',
            'end_date': '2026-12-31',
            'budget': '100000.00',
            'priority': 'HIGH',
            'status': 'IN_PROGRESS',
            'project_manager': self.manager.id
        }
        response = self.client.post('/api/projects/', project_data)
        self.assertEqual(response.status_code, 201)
        project_id = response.data['id']
        print("  - Create Project success")
        
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, 200)
        print("  - List Projects success")
        
        response = self.client.get(f'/api/projects/{project_id}/')
        self.assertEqual(response.status_code, 200)
        print("  - Retrieve Project success")
        
        response = self.client.post(f'/api/projects/{project_id}/add_member/', {'user_id': self.employee.id})
        self.assertEqual(response.status_code, 200)
        print("  - Add Member success")
        
        # 3. Tasks
        print("Testing Tasks API...")
        task_data = {
            'title': 'Test REST Endpoints',
            'description': 'Write and run verification scripts',
            'project': project_id,
            'assigned_to': self.employee.id,
            'priority': 'HIGH',
            'status': 'PENDING',
            'deadline': (timezone.now() + timedelta(days=5)).isoformat(),
            'estimated_hours': '12.00'
        }
        response = self.client.post('/api/tasks/', task_data)
        if response.status_code != 201:
            print(f"ERROR DETAILS: {response.data}")
        self.assertEqual(response.status_code, 201)
        task_id = response.data['id']
        print("  - Create Task success")
        
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, 200)
        print("  - List Tasks success")
        
        response = self.client.get(f'/api/tasks/{task_id}/')
        self.assertEqual(response.status_code, 200)
        print("  - Retrieve Task success")
        
        # Change credentials to Employee to simulate task execution
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.employee_access}')
        
        response = self.client.get('/api/tasks/my_tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) > 0)
        print("  - Get My Tasks success")
        
        response = self.client.post(f'/api/tasks/{task_id}/log_time/', {'hours': '4.5'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(float(response.data['actual_hours']), 4.5)
        print("  - Log Time success")
        
        response = self.client.post(f'/api/tasks/{task_id}/update_status/', {'status': 'IN_PROGRESS'})
        self.assertEqual(response.status_code, 200)
        print("  - Update Task Status success")
        
        response = self.client.get(f'/api/projects/{project_id}/statistics/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_tasks'], 1)
        print("  - Get Project Statistics success")
        
        # Switch back to Admin
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_access}')
        
        new_deadline = (timezone.now() + timedelta(days=10)).isoformat()
        response = self.client.post(f'/api/tasks/{task_id}/update_deadline/', {'deadline': new_deadline})
        self.assertEqual(response.status_code, 200)
        print("  - Update Deadline success")
        
        response = self.client.get('/api/tasks/overdue/')
        self.assertEqual(response.status_code, 200)
        print("  - Get Overdue Tasks success")
        
        response = self.client.get(f'/api/projects/{project_id}/tasks/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        print("  - Get Project Tasks list success")
        
        # 4. Teams
        print("Testing Teams API...")
        response = self.client.post('/api/teams/', {'name': 'QA Team'})
        if response.status_code != 201:
            print(f"TEAM CREATION ERROR DETAILS: {response.data}")
        self.assertEqual(response.status_code, 201)
        team_id = response.data['id']
        print("  - Create Team success")
        
        response = self.client.get('/api/teams/')
        self.assertEqual(response.status_code, 200)
        print("  - List Teams success")
        
        response = self.client.get(f'/api/teams/{team_id}/')
        self.assertEqual(response.status_code, 200)
        print("  - Retrieve Team success")
        
        response = self.client.post(f'/api/teams/{team_id}/add_member/', {'user_id': self.employee.id, 'role': 'QA Engineer'})
        self.assertEqual(response.status_code, 200)
        print("  - Add Team Member success")
        
        response = self.client.get(f'/api/teams/{team_id}/members/')
        self.assertEqual(response.status_code, 200)
        print("  - Get Team Members success")
        
        response = self.client.post(f'/api/projects/{project_id}/remove_member/', {'user_id': self.employee.id})
        self.assertEqual(response.status_code, 200)
        print("  - Remove Project Member success")
        
        response = self.client.post(f'/api/teams/{team_id}/remove_member/', {'user_id': self.employee.id})
        self.assertEqual(response.status_code, 200)
        print("  - Remove Team Member success")
        
        # 5. Notifications
        print("Testing Notifications API...")
        notif = Notification.objects.create(
            user=self.admin,
            title='Test Notification',
            message='Alert for E2E validation',
            notification_type='SYSTEM'
        )
        
        response = self.client.get('/api/notifications/unread_count/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['unread_count'], 1)
        print("  - Unread Count success")
        
        response = self.client.get('/api/notifications/')
        self.assertEqual(response.status_code, 200)
        print("  - List Notifications success")
        
        response = self.client.post(f'/api/notifications/{notif.id}/mark_read/')
        self.assertEqual(response.status_code, 200)
        print("  - Mark notification read success")
        
        response = self.client.post('/api/notifications/mark_all_read/')
        self.assertEqual(response.status_code, 200)
        print("  - Mark all read success")
        
        # 6. Reports
        print("Testing Reports API...")
        response = self.client.get('/api/reports/dashboard-stats/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['total_projects'], 1)
        print("  - Dashboard Stats success")
        
        response = self.client.post('/api/reports/project/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        print("  - Generate Excel Report success")
        
        response = self.client.post('/api/reports/task/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        print("  - Generate PDF Report success")
        
        # 7. Calendar
        print("Testing Calendar API...")
        cal_task_data = {
            'title': 'Calendar quick task',
            'project_id': project_id,
            'deadline': (timezone.now() + timedelta(days=2)).isoformat(),
            'priority': 'LOW'
        }
        response = self.client.post('/api/calendar/events/quick-task/', cal_task_data)
        self.assertEqual(response.status_code, 201)
        print("  - Quick Task creation success")
        
        response = self.client.get('/api/calendar/events/?start=2026-06-01T00:00:00Z&end=2026-06-30T23:59:59Z')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.data) >= 1)
        print("  - Calendar Events list success")
        
        # 8. Chat
        print("Testing Chat API...")
        chat_msg = ChatMessage.objects.create(
            user=self.employee,
            team=Team.objects.get(id=team_id),
            message='Hello team!'
        )
        
        response = self.client.get(f'/api/chat/messages/?team_id={team_id}')
        self.assertEqual(response.status_code, 200)
        if len(response.data) != 1:
            print(f"CHAT MESSAGES: {response.data}")
        self.assertEqual(len(response.data), 1)
        print("  - List Chat Messages success")
        
        response = self.client.get(f'/api/chat/messages/history/{team_id}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['message'], 'Hello team!')
        print("  - Get Chat Message History success")
        
        response = self.client.post(f'/api/chat/messages/mark-read/{team_id}/')
        self.assertEqual(response.status_code, 200)
        print("  - Mark Chat Messages Read success")
        
        print("\n>>> ALL API CHANNELS AND ACTION ENDPOINTS COMPLETED END-TO-END SUCCESSFULLY! <<<\n")
