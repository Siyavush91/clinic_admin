from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()

class PatientRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    date_of_birth = forms.DateField(
        required=True,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    gender = forms.ChoiceField(
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        required=False
    )
    # EMR specific fields
    blood_group = forms.ChoiceField(
        choices=[
            ('', '---'),
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
            ('O+', 'O+'), ('O-', 'O-'),
        ],
        required=False
    )
    allergies = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    chronic_diseases = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    emergency_contact = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password1', 'password2', 
            'first_name', 'last_name', 'date_of_birth', 
            'phone_number', 'address', 'gender'
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = 'patient'
        user.date_of_birth = self.cleaned_data['date_of_birth']
        user.phone_number = self.cleaned_data['phone_number']
        user.address = self.cleaned_data['address']
        user.gender = self.cleaned_data['gender']
        
        if commit:
            user.save()
            # Get the created patient profile and update additional fields
            patient = user.patient_profile
            patient.blood_group = self.cleaned_data['blood_group']
            patient.allergies = self.cleaned_data['allergies']
            patient.chronic_diseases = self.cleaned_data['chronic_diseases']
            patient.emergency_contact = self.cleaned_data['emergency_contact']
            patient.save()
            
        return user

class StaffRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    role = forms.ChoiceField(choices=[('doctor', 'Doctor'), ('receptionist', 'Receptionist')], required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    gender = forms.ChoiceField(
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        required=False
    )
    # Doctor specific fields
    specialization = forms.CharField(max_length=100, required=False)
    license_number = forms.CharField(max_length=50, required=False)
    experience_years = forms.IntegerField(min_value=0, required=False)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password1', 'password2', 
            'first_name', 'last_name', 'role',
            'phone_number', 'address', 'date_of_birth', 'gender'
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.role = self.cleaned_data['role']
        user.phone_number = self.cleaned_data['phone_number']
        user.address = self.cleaned_data['address']
        user.date_of_birth = self.cleaned_data['date_of_birth']
        user.gender = self.cleaned_data['gender']
        
        if commit:
            user.save()
            # Update doctor specific fields if role is doctor
            if user.role == 'doctor':
                doctor = user.doctor_profile
                doctor.specialization = self.cleaned_data['specialization'] or 'General'
                doctor.license_number = self.cleaned_data['license_number'] or f'TMP-{user.id}'
                doctor.experience_years = self.cleaned_data['experience_years'] or 0
                doctor.save()
                
        return user

class UserEditForm(UserChangeForm):
    password = None  # Remove password field from form
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'address', 'date_of_birth', 'gender')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3})
        } 