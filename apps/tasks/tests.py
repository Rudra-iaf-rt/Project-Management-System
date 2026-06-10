# apps/tasks/tests.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from apps.projects.models import Project
from apps.tasks.models import Task

User = get_user_model()

class TasksTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@example.com',
            password='manager123',
            role='PROJECT_MANAGER'
        )
        
        self.employee = User.objects.create_user(
            username='employee',
            email='employee@example.com',
            password='employee123',
            role='EMPLOYEE'
        )
        
        # Create project
        self.project = Project.objects.create(
            name='Test Project',
            description='Test project description',
            project_code='TEST-001',
            start_date=datetime.now().date(),
            end_date=datetime.now().date() + timedelta(days=30),
            priority='MEDIUM',
            status='PENDING',
            budget=50000,
            project_manager=self.manager
        )
        self.project.team_members.add(self.employee)
        
        # Create task
        self.task = Task.objects.create(
            title='Test Task',
            description='Test task description',
            project=self.project,
            assigned_to=self.employee,
            assigned_by=self.manager,
            priority='HIGH',
            status='PENDING',
            deadline=datetime.now() + timedelta(days=7),
            estimated_hours=8
        )
    
    def test_task_creation(self):
        """Test that tasks are created correctly"""
        self.assertEqual(self.task.title, 'Test Task')
        self.assertEqual(self.task.project, self.project)
        self.assertEqual(self.task.assigned_to, self.employee)
        self.assertEqual(self.task.priority, 'HIGH')
    
    def test_task_is_overdue_property(self):
        """Test is_overdue property"""
        # Create overdue task
        overdue_task = Task.objects.create(
            title='Overdue Task',
            description='This task is overdue',
            project=self.project,
            assigned_to=self.employee,
            assigned_by=self.manager,
            status='PENDING',
            deadline=datetime.now() - timedelta(days=1),
            estimated_hours=4
        )
        
        self.assertTrue(overdue_task.is_overdue)
        self.assertFalse(self.task.is_overdue)
    
    def test_task_list_view(self):
        """Test task list view"""
        self.client.login(username='employee', password='employee123')
        response = self.client.get(reverse('task_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Task')
    
    def test_task_detail_view(self):
        """Test task detail view"""
        self.client.login(username='employee', password='employee123')
        response = self.client.get(reverse('task_detail', args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Task')
    
    def test_task_create_by_manager(self):
        """Test task creation by manager"""
        self.client.login(username='manager', password='manager123')
        response = self.client.post(reverse('task_create'), {
            'title': 'New Task',
            'description': 'New task description',
            'project': self.project.id,
            'assigned_to': self.employee.id,
            'priority': 'MEDIUM',
            'deadline': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d %H:%M'),
            'estimated_hours': 6
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Task.objects.filter(title='New Task').exists())
    
    def test_task_status_update(self):
        """Test task status update via AJAX"""
        self.client.login(username='employee', password='employee123')
        response = self.client.post(
            reverse('update_task_status', args=[self.task.id]),
            {'status': 'IN_PROGRESS'}
        )
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'IN_PROGRESS')
    
    def test_task_assignment_notification(self):
        """Test that notification is created when task is assigned"""
        new_task = Task.objects.create(
            title='Notification Test Task',
            description='This should trigger a notification',
            project=self.project,
            assigned_to=self.employee,
            assigned_by=self.manager,
            priority='LOW',
            status='PENDING',
            deadline=datetime.now() + timedelta(days=5)
        )
        
        from apps.notifications.models import Notification
        notification_exists = Notification.objects.filter(
            user=self.employee,
            title__icontains='Notification Test Task'
        ).exists()
        
        self.assertTrue(notification_exists)