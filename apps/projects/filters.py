import django_filters
from .models import Project

class ProjectFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    status = django_filters.ChoiceFilter(choices=Project.STATUS_CHOICES)
    priority = django_filters.ChoiceFilter(choices=Project.PRIORITY_CHOICES)
    start_date = django_filters.DateFromToRangeFilter()
    end_date = django_filters.DateFromToRangeFilter()
    
    class Meta:
        model = Project
        fields = ['name', 'status', 'priority', 'project_manager']