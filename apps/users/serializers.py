from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from apps.emr.models import Patient, Doctor

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'first_name', 'last_name', 
                 'phone_number', 'address', 'date_of_birth', 'gender')
        read_only_fields = ('id',)

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ('blood_group', 'allergies', 'chronic_diseases', 'emergency_contact')

class DoctorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ('specialization', 'license_number', 'experience_years')

class PatientRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    patient_profile = PatientProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name',
                 'phone_number', 'address', 'date_of_birth', 'gender', 'patient_profile')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Remove patient_profile data from attrs to handle separately
        self.patient_profile_data = attrs.pop('patient_profile', {})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role='patient',
            phone_number=validated_data.get('phone_number', ''),
            address=validated_data.get('address', ''),
            date_of_birth=validated_data.get('date_of_birth', None),
            gender=validated_data.get('gender', None)
        )
        
        # Update patient profile with additional data if provided
        if hasattr(self, 'patient_profile_data') and self.patient_profile_data:
            patient = user.patient_profile
            for key, value in self.patient_profile_data.items():
                setattr(patient, key, value)
            patient.save()
            
        return user

class StaffRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    doctor_profile = DoctorProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'first_name', 'last_name', 'role',
                 'phone_number', 'address', 'date_of_birth', 'gender', 'doctor_profile')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        if attrs['role'] not in ['doctor', 'receptionist']:
            raise serializers.ValidationError({"role": "Invalid role for staff registration."})
            
        # Remove doctor_profile data from attrs to handle separately
        if attrs['role'] == 'doctor':
            self.doctor_profile_data = attrs.pop('doctor_profile', {})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data['role'],
            phone_number=validated_data.get('phone_number', ''),
            address=validated_data.get('address', ''),
            date_of_birth=validated_data.get('date_of_birth', None),
            gender=validated_data.get('gender', None)
        )
        
        # Update doctor profile if role is doctor and profile data provided
        if user.role == 'doctor' and hasattr(self, 'doctor_profile_data') and self.doctor_profile_data:
            doctor = user.doctor_profile
            for key, value in self.doctor_profile_data.items():
                setattr(doctor, key, value)
            doctor.save()
            
        return user

class PatientDetailSerializer(UserSerializer):
    patient_profile = PatientProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ('patient_profile',)
        read_only_fields = ('id',)

class DoctorDetailSerializer(UserSerializer):
    doctor_profile = DoctorProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ('doctor_profile',)
        read_only_fields = ('id',) 