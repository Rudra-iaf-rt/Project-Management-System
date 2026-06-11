# pms/urls.py - Comment out problematic imports
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from apps.accounts.views import dashboard
from apps.tasks.views import kanban_board

# Comment out API imports for now
# from rest_framework.routers import DefaultRouter
# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
#     TokenVerifyView,
# )
# from apps.projects.api import ProjectViewSet
# from apps.tasks.api import TaskViewSet
# from apps.teams.api import TeamViewSet
# from apps.accounts.api import UserViewSet, ProfileViewSet
# from apps.notifications.api import NotificationViewSet
# from apps.reports.api import ReportViewSet
# from apps.calendar.api import CalendarEventViewSet
# from apps.chat.api import ChatMessageViewSet

# Comment out router registration
# router = DefaultRouter()
# router.register(r'projects', ProjectViewSet, basename='api-projects')
# router.register(r'tasks', TaskViewSet, basename='api-tasks')
# router.register(r'teams', TeamViewSet, basename='api-teams')
# router.register(r'users', UserViewSet, basename='api-users')
# router.register(r'profile', ProfileViewSet, basename='api-profile')
# router.register(r'notifications', NotificationViewSet, basename='api-notifications')
# router.register(r'reports', ReportViewSet, basename='api-reports')
# router.register(r'calendar/events', CalendarEventViewSet, basename='api-calendar')
# router.register(r'chat/messages', ChatMessageViewSet, basename='api-chat')

urlpatterns = [
    path('', dashboard, name='dashboard'),  # Changed from 'home' to 'dashboard'
    path('home/', dashboard, name='home'),
    path('kanban/', kanban_board, name='kanban_board'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),
    path('profile/', include('apps.accounts.urls')),
    path('projects/', include('apps.projects.urls')),
    path('tasks/', include('apps.tasks.urls')),
    path('teams/', include('apps.teams.urls')),
    path('files/', include('apps.files.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('chat/', include('apps.chat.urls')),
    path('reports/', include('apps.reports.urls')),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
]

# Comment out API URLs for now
# urlpatterns += [
#     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
#     path('api-auth/', include('rest_framework.urls')),
#     path('api/', include(router.urls)),
# ]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)