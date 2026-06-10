# apps/projects/tests.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import datetime, timedelta
from apps.projects.models import Project
from apps.tasks.models import Task

User = get_user_model()

class ProjectsTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
        
        # Create users
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
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
            description='This is a test project',
            project_code='TEST-001',
            start_date=datetime.now().date(),
            end_date=datetime.now().date() + timedelta(days=30),
            priority='HIGH',
            status='PENDING',
            budget=50000,
            project_manager=self.manager
        )
        self.project.team_members.add(self.employee)
    
    def test_project_creation(self):
        """Test that projects are created correctly"""
        self.assertEqual(self.project.name, 'Test Project')
        self.assertEqual(self.project.project_code, 'TEST-001')
        self.assertEqual(self.project.project_manager, self.manager)
        self.assertEqual(self.project.team_members.count(), 1)
    
    def test_project_progress_calculation(self):
        """Test project progress calculation"""
        # Create tasks
        Task.objects.create(
            title='Task 1',
            description='Task 1 description',
            project=self.project,
            assigned_to=self.employee,
            assigned_by=self.manager,
            status='COMPLETED',
            deadline=datetime.now() + timedelta(days=7)
        )
        
        Task.objects.create(
            title='Task 2',
            description='Task 2 description',
            project=self.project,
            assigned_to=self.employee,
            assigned_by=self.manager,
            status='PENDING',
            deadline=datetime.now() + timedelta(days=14)
        )
        
        self.assertEqual(self.project.progress, 50)  # 1 of 2 tasks completed
    
    def test_project_list_view_authenticated(self):
        """Test project list view for authenticated user"""
        self.client.login(username='employee', password='employee123')
        response = self.client.get(reverse('project_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project')
    
    def test_project_detail_view(self):
        """Test project detail view"""
        self.client.login(username='employee', password='employee123')
        response = self.client.get(reverse('project_detail', args=[self.project.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Project')
    
    def test_project_create_by_manager(self):
        """Test project creation by manager"""
        self.client.login(username='manager', password='manager123')
        response = self.client.post(reverse('project_create'), {
            'name': 'New Project',
            'description': 'New project description',
            'project_code': 'NEW-001',
            'start_date': datetime.now().date(),
            'end_date': datetime.now().date() + timedelta(days=60),
            'priority': 'MEDIUM',
            'status': 'PENDING',
            'budget': 75000,
            'team_members': [self.employee.id]
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Project.objects.filter(name='New Project').exists())
    
    def test_project_update_by_manager(self):
        """Test project update by manager"""
        self.client.login(username='manager', password='manager123')
        response = self.client.post(
            reverse('project_update', args=[self.project.id]),
            {
                'name': 'Updated Project Name',
                'description': self.project.description,
                'project_code': self.project.project_code,
                'start_date': self.project.start_date,
                'end_date': self.project.end_date,
                'priority': self.project.priority,
                'status': 'IN_PROGRESS',
                'budget': self.project.budget,
                'team_members': [self.employee.id]
            }
        )
        
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, 'Updated Project Name')
        self.assertEqual(self.project.status, 'IN_PROGRESS')
    
    def test_unauthorized_project_access(self):
        """Test unauthorized user cannot access project"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='other123',
            role='EMPLOYEE'
        )
        
        self.client.login(username='other', password='other123')
        response = self.client.get(reverse('project_detail', args=[self.project.id]))
        self.assertEqual(response.status_code, 302)  # Redirect with error message