from django import forms
from django.forms import inlineformset_factory
from .models import Course, Module, Lesson
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from .models import Profile

User = get_user_model()

class CourseUploadForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'master_category', 'title', 'thumbnail',
            'description', 'price', 'discount_price',
            'level', 'is_live', 'is_active'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter course title'}),
            'master_category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-select'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
            'is_live': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['title', 'order']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Module Title'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'style': 'width:80px;'}),
        }

ModuleFormSet = inlineformset_factory(
    Course, Module, form=ModuleForm,
    extra=1, can_delete=True
)

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control bg-light border-0'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control bg-light border-0'}))
    user_type = forms.ChoiceField(
        choices=[('Student', 'Student'), ('Teacher', 'Teacher')],
        widget=forms.Select(attrs={'class': 'form-select bg-light border-0'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control bg-light border-0', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control bg-light border-0', 'placeholder': 'Last Name'}),
            'username': forms.TextInput(attrs={'class': 'form-control bg-light border-0', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control bg-light border-0', 'placeholder': 'Email Address'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data
    
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['photo', 'phone_number', 'address', 'bio',
                  'qualification', 'experience_years',
                  'enrollment_number', 'date_of_birth', 'college_name', 'branch']
        
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. M.Sc in Physics'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'enrollment_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'college_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. IIT Delhi'}),
            'branch': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Mechanical, IT'}),
        
        }