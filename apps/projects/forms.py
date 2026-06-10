from django import forms
from .models import Project
from apps.accounts.models import User

class ProjectForm(forms.ModelForm):
    team_members = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role='EMPLOYEE'),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = Project
        fields = ['name', 'description', 'project_code', 'start_date', 'end_date', 
                 'priority', 'status', 'budget', 'team_members']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'project_code': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'budget': forms.NumberInput(attrs={'class': 'form-control'}),
        }