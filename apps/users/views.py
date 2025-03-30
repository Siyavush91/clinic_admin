from rest_framework import viewsets, status, generics, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from .serializers import (
    UserSerializer, PatientRegistrationSerializer, StaffRegistrationSerializer,
    PatientDetailSerializer, DoctorDetailSerializer
)
from .permissions import IsAdmin
from .forms import PatientRegistrationForm, StaffRegistrationForm, UserEditForm
from .models import CustomUser
from apps.emr.models import Patient, Doctor, Visit, LabOrder, Prescription
from django.utils import timezone

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'create':
            return PatientRegistrationSerializer
        elif self.action == 'patient_detail':
            return PatientDetailSerializer
        elif self.action == 'doctor_detail':
            return DoctorDetailSerializer
        return UserSerializer

    @action(detail=False, methods=['post'])
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': UserSerializer(user).data
                })
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'detail': 'Successfully logged out'})
        except Exception:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
            
    @action(detail=True, methods=['get'])
    def patient_detail(self, request, pk=None):
        """Get detailed patient information including EMR profile"""
        user = self.get_object()
        if user.role != 'patient':
            return Response({'error': 'User is not a patient'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = PatientDetailSerializer(user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def doctor_detail(self, request, pk=None):
        """Get detailed doctor information including EMR profile"""
        user = self.get_object()
        if user.role != 'doctor':
            return Response({'error': 'User is not a doctor'}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = DoctorDetailSerializer(user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def medical_history(self, request, pk=None):
        """Get patient's medical history"""
        user = self.get_object()
        if user.role != 'patient':
            return Response({'error': 'User is not a patient'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            patient = user.patient_profile
            visits = Visit.objects.filter(patient=patient).order_by('-visit_date')
            
            history = {
                'patient_info': {
                    'name': f"{user.first_name} {user.last_name}",
                    'dob': user.date_of_birth,
                    'blood_group': patient.blood_group,
                    'allergies': patient.allergies,
                    'chronic_diseases': patient.chronic_diseases
                },
                'visits': []
            }
            
            for visit in visits:
                visit_data = {
                    'id': visit.id,
                    'date': visit.visit_date,
                    'doctor': f"Dr. {visit.doctor.user.first_name} {visit.doctor.user.last_name}",
                    'reason': visit.reason,
                    'status': visit.status,
                    'department': visit.department.name if visit.department else None,
                    'diagnoses': [
                        {
                            'name': diagnosis.diagnosis_name,
                            'code': diagnosis.diagnosis_code,
                            'is_chronic': diagnosis.is_chronic
                        } for diagnosis in visit.diagnoses.all()
                    ],
                    'lab_orders': [
                        {
                            'id': order.id,
                            'status': order.status,
                            'date': order.order_date,
                            'has_results': order.results.exists()
                        } for order in visit.lab_orders.all()
                    ],
                    'prescriptions': [
                        {
                            'medication': prescription.medication.name,
                            'dosage': prescription.dosage,
                            'frequency': prescription.frequency,
                            'duration': prescription.duration,
                            'status': prescription.status
                        } for prescription in visit.prescriptions.all()
                    ]
                }
                history['visits'].append(visit_data)
            
            return Response(history)
        except Patient.DoesNotExist:
            return Response({'error': 'Patient profile not found'}, status=status.HTTP_404_NOT_FOUND)

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Successfully logged in!')
            
            # Redirect based on user role
            if user.role == 'patient':
                return redirect('emr:patient_dashboard')
            elif user.role == 'doctor':
                return redirect('emr:doctor_dashboard')
            elif user.role == 'receptionist':
                return redirect('appointment_list')
            else:
                return redirect('users:profile')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'users/login.html')

def register_view(request):
    if request.user.is_authenticated and request.user.role == 'admin':
        # Staff registration form for admin
        if request.method == 'POST':
            form = StaffRegistrationForm(request.POST)
            if form.is_valid():
                user = form.save()
                messages.success(request, f'Staff member {user.username} registered successfully!')
                return redirect('users:profile')
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = StaffRegistrationForm()
    else:
        # Patient registration form
        if request.method == 'POST':
            form = PatientRegistrationForm(request.POST)
            if form.is_valid():
                user = form.save()
                login(request, user)
                messages.success(request, 'Account created successfully!')
                return redirect('emr:patient_dashboard')
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = PatientRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Successfully logged out!')
    return redirect('users:login')

@login_required
def profile_view(request):
    user = request.user
    context = {'user': user}
    
    if user.role == 'patient':
        # Get EMR data for patients
        patient = user.patient_profile
        visits = Visit.objects.filter(patient=patient).order_by('-visit_date')
        active_prescriptions = Prescription.objects.filter(
            patient=patient, status='active'
        ).order_by('-created_at')
        
        context.update({
            'patient': patient,
            'recent_visits': visits[:5],
            'active_prescriptions': active_prescriptions,
            'lab_orders': LabOrder.objects.filter(patient=patient).order_by('-order_date')[:5]
        })
        
    elif user.role == 'doctor':
        # Get EMR data for doctors
        doctor = user.doctor_profile
        today_appointments = Visit.objects.filter(
            doctor=doctor, 
            visit_date__date=timezone.now().date(),
            status__in=['scheduled', 'in_progress']
        ).order_by('visit_date')
        
        context.update({
            'doctor': doctor,
            'today_appointments': today_appointments,
            'recent_patients': Visit.objects.filter(doctor=doctor).order_by('-visit_date').distinct('patient')[:10]
        })
    
    return render(request, 'users/profile.html', context)

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserEditForm(instance=request.user)
    return render(request, 'users/edit_profile.html', {'form': form})

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})

class PatientRegistrationAPIView(generics.CreateAPIView):
    serializer_class = PatientRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': 'Patient registered successfully',
            'user': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role
            }
        }, status=status.HTTP_201_CREATED)

class StaffRegistrationAPIView(generics.CreateAPIView):
    serializer_class = StaffRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def check_permissions(self, request):
        if not request.user.is_authenticated or request.user.role != 'admin':
            self.permission_denied(request)
        return super().check_permissions(request)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'message': 'Staff member registered successfully',
            'user': {
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role
            }
        }, status=status.HTTP_201_CREATED) 