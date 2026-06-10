from django.urls import path
from . import views

urlpatterns = [
    path('', views.team_list, name='team_list'),
    path('<int:pk>/', views.team_detail, name='team_detail'),
    path('create/', views.team_create, name='team_create'),
    path('<int:pk>/update/', views.team_update, name='team_update'),
    path('<int:pk>/add-member/', views.add_member, name='add_member'),
]