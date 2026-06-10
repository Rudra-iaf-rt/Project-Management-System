from django import forms
from .models import ProjectFile
from apps.projects.models import Project
from django.db.models import Q

class FileUploadForm(forms.Form):
    file = forms.FileField(widget=forms.FileInput(attrs={'class': 'form-control'}))
    project = forms.ModelChoiceField(
        queryset=Project.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            if user.role == 'SUPER_ADMIN':
                self.fields['project'].queryset = Project.objects.all()
            else:
                self.fields['project'].queryset = Project.objects.filter(
                    Q(project_manager=user) | Q(team_members=user)
                ).distinct()