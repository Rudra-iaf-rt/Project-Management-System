from django import forms
from .models import Team
from apps.accounts.models import User

class TeamForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role='EMPLOYEE'),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = Team
        fields = ['name', 'description', 'members']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class AddMemberForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.filter(role='EMPLOYEE'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        choices=[
            ('Manager', 'Manager'),
            ('Developer', 'Developer'),
            ('Tester', 'Tester'),
            ('Designer', 'Designer'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )