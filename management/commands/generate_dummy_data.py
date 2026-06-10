# management/commands/generate_dummy_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import datetime, timedelta
import random
from faker import Faker

from apps.accounts.models import User, UserProfile
from apps.projects.models import Project
from apps.tasks.models import Task
from apps.teams.models import Team

fake = Faker()

class Command(BaseCommand):
    help = 'Generate dummy data for testing the application'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create (default: 20)'
        )
        parser.add_argument(
            '--projects',
            type=int,
            default=10,
            help='Number of projects to create (default: 10)'
        )
        parser.add_argument(
            '--tasks',
            type=int,
            default=50,
            help='Number of tasks to create (default: 50)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Generating dummy data...')
        
        # Create admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'password': make_password('admin123'),
                'first_name': 'Super',
                'last_name': 'Admin',
                'role': 'SUPER_ADMIN',
                'is_superuser': True,
                'is_staff': True
            }
        )
        
        # Create project managers
        managers = []
        for i in range(3):
            manager = User.objects.create(
                username=f'manager_{i+1}',
                email=f'manager_{i+1}@example.com',
                password=make_password('manager123'),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role='PROJECT_MANAGER',
                department=random.choice(['IT', 'HR', 'Sales', 'Marketing']),
                designation='Project Manager'
            )
            managers.append(manager)
        
        # Create employees
        employees = []
        roles = ['Developer', 'Tester', 'Designer', 'QA Engineer', 'Business Analyst']
        departments = ['IT', 'HR', 'Sales', 'Marketing', 'Finance']
        
        for i in range(options['users']):
            employee = User.objects.create(
                username=f'employee_{i+1}',
                email=f'employee_{i+1}@example.com',
                password=make_password('employee123'),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role='EMPLOYEE',
                department=random.choice(departments),
                designation=random.choice(roles)
            )
            
            # Create user profile
            UserProfile.objects.create(
                user=employee,
                bio=fake.text(max_nb_chars=200),
                skills=', '.join(fake.words(nb=5)),
                experience_years=random.randint(0, 15),
                address=fake.address()
            )
            employees.append(employee)
        
        self.stdout.write(f'Created {len(managers)} managers and {len(employees)} employees')
        
        # Create projects
        statuses = ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD']
        priorities = ['HIGH', 'MEDIUM', 'LOW']
        
        projects = []
        for i in range(options['projects']):
            start_date = fake.date_between(start_date='-1y', end_date='today')
            end_date = start_date + timedelta(days=random.randint(30, 180))
            
            project = Project.objects.create(
                name=fake.catch_phrase(),
                description=fake.text(max_nb_chars=500),
                project_code=f'PRJ-{i+1:04d}',
                start_date=start_date,
                end_date=end_date,
                priority=random.choice(priorities),
                status=random.choice(statuses),
                budget=random.randint(10000, 500000),
                project_manager=random.choice(managers)
            )
            
            # Add random team members
            project.team_members.add(*random.sample(employees, k=random.randint(3, 8)))
            projects.append(project)
        
        self.stdout.write(f'Created {len(projects)} projects')
        
        # Create tasks
        task_statuses = ['PENDING', 'IN_PROGRESS', 'TESTING', 'COMPLETED']
        
        for i in range(options['tasks']):
            project = random.choice(projects)
            assigned_to = random.choice(employees)
            deadline = fake.date_time_between(start_date='now', end_date='+30d')
            
            task = Task.objects.create(
                title=fake.sentence(nb_words=6),
                description=fake.text(max_nb_chars=300),
                project=project,
                assigned_to=assigned_to,
                assigned_by=project.project_manager,
                priority=random.choice(priorities),
                status=random.choice(task_statuses),
                deadline=deadline,
                estimated_hours=random.randint(1, 40),
                actual_hours=random.randint(0, 50)
            )
            
            if task.status == 'COMPLETED':
                task.completed_at = fake.date_time_between(start_date='-30d', end_date='now')
                task.save()
        
        self.stdout.write(f'Created {options["tasks"]} tasks')
        
        # Create teams
        for i in range(5):
            team_lead = random.choice(employees)
            team = Team.objects.create(
                name=fake.company(),
                description=fake.text(max_nb_chars=200),
                team_lead=team_lead
            )
            team.members.add(*random.sample(employees, k=random.randint(3, 10)))
        
        self.stdout.write(
            self.style.SUCCESS('Successfully generated dummy data!')
        )
        self.stdout.write('\nLogin Credentials:')
        self.stdout.write(f'Admin: admin / admin123')
        self.stdout.write(f'Manager: manager_1 / manager123')
        self.stdout.write(f'Employee: employee_1 / employee123')