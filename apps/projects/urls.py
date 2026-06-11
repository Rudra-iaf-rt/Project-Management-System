from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('create/', views.project_create, name='project_create'),
    path('<int:pk>/update/', views.project_update, name='project_update'),
    path('<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('<int:pk>/assign/', views.project_assign, name='project_assign'),
    path('<int:project_id>/remove-member/<int:member_id>/', views.project_remove_member, name='project_remove_member'),
]