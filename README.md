# Project Management System (PMS)

A complete web-based application designed to help companies and teams manage projects, tasks, employees, deadlines, files, notifications, and reports efficiently.

## 🚀 Features

### Core Features
- **User Management**: Registration, Login, Profile management, Role-based access (Super Admin, Project Manager, Employee)
- **Project Management**: Create, Read, Update, Delete projects, Track progress, Budget management
- **Task Management**: Assign tasks, Set priorities, Track status, Deadline management
- **Team Management**: Create teams, Add members, Assign roles
- **File Management**: Upload, Download, Delete project files
- **Notification System**: Real-time notifications, Email alerts
- **Team Chat**: Real-time messaging with WebSockets
- **Reports & Analytics**: Generate PDF/Excel reports, Dashboard analytics

### Advanced Features
- 📊 Kanban Board for task management
- 📈 Interactive dashboards with Charts.js
- 🔔 Real-time notifications
- 💬 WebSocket-based team chat
- 📧 Email notifications for task assignments
- 🔐 JWT authentication for API
- 📱 RESTful API for mobile apps
- 🐳 Docker support for easy deployment

## 🛠 Tech Stack

### Backend
- Python 3.11
- Django 5.0
- Django REST Framework
- PostgreSQL
- Redis (for caching and WebSocket)
- Celery (for async tasks)

### Frontend
- HTML5/CSS3
- Bootstrap 5
- JavaScript (Vanilla)
- Chart.js
- WebSocket API

### DevOps
- Docker & Docker Compose
- Nginx
- Gunicorn
- GitHub Actions (CI/CD)

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Node.js (for frontend build, optional)

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/pms.git
cd pms

# Copy environment variables
cp .env.example .env
# Edit .env with your values

# Build and run with Docker Compose
docker-compose up -d

# Run migrations
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Access the application
open http://localhost:8000