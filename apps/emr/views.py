from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.db import models

from .models import (
    Patient, Doctor, Department, Visit, Diagnosis,
    LabTest, LabOrder, LabResult, Medication,
    Prescription, Procedure, ProcedureOrder, Hospitalization
)
from .serializers import (
    PatientSerializer, DoctorSerializer, DepartmentSerializer,
    VisitListSerializer, VisitDetailSerializer, DiagnosisSerializer,
    LabTestSerializer, LabOrderListSerializer, LabOrderDetailSerializer,
    LabResultSerializer, MedicationSerializer,
    PrescriptionListSerializer, PrescriptionDetailSerializer,
    ProcedureSerializer, ProcedureOrderListSerializer, ProcedureOrderDetailSerializer,
    HospitalizationListSerializer, HospitalizationDetailSerializer,
    PatientVisitSerializer, PatientLabResultSerializer
)
from .permissions import (
    IsDoctor, IsPatient, IsReceptionist, IsAdmin,
    IsDoctorOrAdmin, IsDoctorOrReceptionist,
    IsPatientOwner, IsDoctorAssigned, IsPatientOwnerOrDoctorAssigned
)
from .utils import generate_medical_report, generate_discharge_summary

class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing patients
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated, IsDoctorOrReceptionist]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    
    def get_permissions(self):
        if self.action == 'retrieve':
            return [IsAuthenticated(), IsPatientOwnerOrDoctorAssigned()]
        return super().get_permissions()
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            # Patients can only see their own profile
            return Patient.objects.filter(user=user)
        return super().get_queryset()

    @action(detail=True, methods=['get'])
    def medical_report(self, request, pk=None):
        """
        Generate a medical report for a patient in PDF format
        """
        patient = self.get_object()
        diagnoses = Diagnosis.objects.filter(patient=patient).order_by('-diagnosis_date')
        prescriptions = Prescription.objects.filter(patient=patient, status='active')
        lab_orders = LabOrder.objects.filter(patient=patient, status='completed').order_by('-order_date')[:5]
        
        pdf = generate_medical_report(patient, diagnoses, prescriptions, lab_orders)
        
        # Create the HttpResponse with PDF content
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"medical_report_{patient.user.last_name}_{patient.user.first_name}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response


class DoctorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing doctors
    """
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['user__first_name', 'user__last_name', 'specialization']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]


class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing departments
    """
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]


class VisitViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing patient visits
    """
    queryset = Visit.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['patient', 'doctor', 'department', 'status', 'visit_date']
    search_fields = ['reason', 'notes']
    ordering_fields = ['visit_date', 'created_at']
    ordering = ['-visit_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return VisitListSerializer
        return VisitDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [IsAuthenticated(), IsDoctorOrReceptionist()]
        elif self.action == 'destroy':
            return [IsAuthenticated(), IsAdmin()]
        elif self.action in ['retrieve', 'list']:
            return [IsAuthenticated(), IsPatientOwnerOrDoctorAssigned()]
        return super().get_permissions()
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            # Patients can only see their own visits
            return Visit.objects.filter(patient__user=user)
        elif user.role == 'doctor':
            # Doctors can only see visits assigned to them
            return Visit.objects.filter(doctor__user=user)
        return super().get_queryset()


class DiagnosisViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing diagnoses
    """
    queryset = Diagnosis.objects.all()
    serializer_class = DiagnosisSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['patient', 'doctor', 'visit', 'is_primary', 'is_chronic', 'diagnosis_date']
    search_fields = ['diagnosis_code', 'diagnosis_name', 'description']
    ordering_fields = ['diagnosis_date', 'created_at']
    ordering = ['-diagnosis_date']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsDoctor()]
        return [IsAuthenticated(), IsPatientOwnerOrDoctorAssigned()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            # Patients can only see their own diagnoses
            return Diagnosis.objects.filter(patient__user=user)
        elif user.role == 'doctor':
            # Doctors can only see diagnoses they created
            return Diagnosis.objects.filter(doctor__user=user)
        return super().get_queryset()


class LabTestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing lab tests
    """
    queryset = LabTest.objects.all()
    serializer_class = LabTestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsDoctorOrAdmin()]
        return [IsAuthenticated()]


class LabOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing lab orders
    """
    queryset = LabOrder.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['patient', 'doctor', 'visit', 'status', 'priority']
    ordering_fields = ['order_date', 'created_at']
    ordering = ['-order_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return LabOrderListSerializer
        return LabOrderDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [IsAuthenticated(), IsDoctor()]
        elif self.action == 'destroy':
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsPatientOwnerOrDoctorAssigned()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            # Patients can only see their own lab orders
            return LabOrder.objects.filter(patient__user=user)
        elif user.role == 'doctor':
            # Doctors can only see lab orders they created
            return LabOrder.objects.filter(doctor__user=user)
        return super().get_queryset()


class LabResultViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing lab results
    """
    queryset = LabResult.objects.all()
    serializer_class = LabResultSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['lab_order', 'lab_test', 'is_abnormal']
    ordering_fields = ['result_date', 'created_at']
    ordering = ['-result_date']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [IsAuthenticated(), IsDoctorOrAdmin()]
        elif self.action == 'destroy':
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsPatientOwnerOrDoctorAssigned()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            # Patients can only see their own lab results
            return LabResult.objects.filter(lab_order__patient__user=user)
        elif user.role == 'doctor':
            # Doctors can only see lab results for patients assigned to them
            return LabResult.objects.filter(lab_order__doctor__user=user)
        return super().get_queryset()


class MedicationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing medications
    """
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'generic_name', 'description']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsDoctorOrAdmin()]
        return [IsAuthenticated()]


class PrescriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing prescriptions
    """
    queryset = Prescription.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['patient', 'doctor', 'visit', 'medication', 'status']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-start_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PrescriptionListSerializer
        return PrescriptionDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [IsAuthenticated(), IsDoctor()]
        elif self.action == 'destroy':
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsPatientOwnerOrDoctorAssigned()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            # Patients can only see their own prescriptions
            return Prescription.objects.filter(patient__user=user)
        elif user.role == 'doctor':
            # Doctors can only see prescriptions they created
            return Prescription.objects.filter(doctor__user=user)
        return super().get_queryset()


class ProcedureViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing procedures
    """
    queryset = Procedure.objects.all()
    serializer_class = ProcedureSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description', 'procedure_code']
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsDoctorOrAdmin()]
        return [IsAuthenticated()]


class ProcedureOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing procedure orders
    """
    queryset = ProcedureOrder.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['patient', 'doctor', 'visit', 'procedure', 'status']
    ordering_fields = ['order_date', 'scheduled_date', 'created_at']
    ordering = ['-order_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProcedureOrderListSerializer
        return ProcedureOrderDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [IsAuthenticated(), IsDoctor()]
        elif self.action == 'destroy':
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsPatientOwnerOrDoctorAssigned()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            # Patients can only see their own procedure orders
            return ProcedureOrder.objects.filter(patient__user=user)
        elif user.role == 'doctor':
            # Doctors can only see procedure orders they created
            return ProcedureOrder.objects.filter(doctor__user=user)
        return super().get_queryset()


class HospitalizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing hospitalizations
    """
    queryset = Hospitalization.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['patient', 'doctor', 'department', 'status']
    ordering_fields = ['admission_date', 'discharge_date', 'created_at']
    ordering = ['-admission_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return HospitalizationListSerializer
        return HospitalizationDetailSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [IsAuthenticated(), IsDoctor()]
        elif self.action == 'destroy':
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated(), IsPatientOwnerOrDoctorAssigned()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'patient':
            # Patients can only see their own hospitalizations
            return Hospitalization.objects.filter(patient__user=user)
        elif user.role == 'doctor':
            # Doctors can only see hospitalizations where they are assigned
            return Hospitalization.objects.filter(doctor__user=user)
        return super().get_queryset()
    
    @action(detail=True, methods=['get'])
    def discharge_summary(self, request, pk=None):
        """
        Generate a discharge summary in PDF format
        """
        hospitalization = self.get_object()
        if hospitalization.status != 'discharged':
            return Response(
                {'error': 'Cannot generate discharge summary for patients who have not been discharged.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pdf = generate_discharge_summary(hospitalization)
        
        # Create the HttpResponse with PDF content
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"discharge_summary_{hospitalization.patient.user.last_name}_{hospitalization.admission_date.strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response


class PatientVisitViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for returning patient's own visits
    """
    serializer_class = PatientVisitSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            patient = self.request.user.patient_profile
            return Visit.objects.filter(patient=patient).order_by('-visit_date')
        except:
            return Visit.objects.none()


class PatientLabResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for returning patient's own lab results
    """
    serializer_class = PatientLabResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            patient = self.request.user.patient_profile
            # Query both direct and indirect relationships to find all lab results
            return LabResult.objects.filter(
                models.Q(patient=patient) | models.Q(lab_order__patient=patient)
            ).select_related('lab_test', 'lab_order', 'ordering_doctor').order_by('-result_date')
        except:
            return LabResult.objects.none()

# Template Views
@login_required
def dashboard_view(request):
    """
    Main dashboard view, redirects based on user role
    """
    user = request.user
    if user.role == 'patient':
        return patient_dashboard_view(request)
    elif user.role == 'doctor':
        return doctor_dashboard_view(request)
    else:
        # Default to patient list for admin/receptionist
        return patient_list_view(request)

@login_required
def patient_dashboard_view(request):
    """
    Dashboard view for patients
    """
    user = request.user
    if user.role != 'patient':
        # If not a patient, redirect to appropriate dashboard
        return dashboard_view(request)
    
    try:
        patient = Patient.objects.get(user=user)
        
        # Recent visits
        recent_visits = Visit.objects.filter(patient=patient).order_by('-visit_date')[:5]
        
        # Active prescriptions
        active_prescriptions = Prescription.objects.filter(
            patient=patient, status='active'
        ).order_by('-created_at')[:5]
        
        # Recent lab orders/results
        recent_lab_orders = LabOrder.objects.filter(
            patient=patient
        ).order_by('-order_date')[:5]
        
        # Upcoming procedures
        upcoming_procedures = ProcedureOrder.objects.filter(
            patient=patient, status='scheduled'
        ).order_by('scheduled_date')[:5]
        
        context = {
            'patient': patient,
            'recent_visits': recent_visits,
            'active_prescriptions': active_prescriptions,
            'recent_lab_orders': recent_lab_orders,
            'upcoming_procedures': upcoming_procedures,
            'active_menu': 'dashboard',
        }
        
        return render(request, 'emr/dashboard/patient_dashboard.html', context)
    except Patient.DoesNotExist:
        # If patient profile doesn't exist, redirect to user profile
        return redirect('users:profile')

@login_required
def doctor_dashboard_view(request):
    """
    Dashboard view for doctors
    """
    user = request.user
    if user.role != 'doctor':
        # If not a doctor, redirect to appropriate dashboard
        return dashboard_view(request)
    
    try:
        doctor = Doctor.objects.get(user=user)
        
        # Today's appointments
        today = timezone.now().date()
        today_appointments = Visit.objects.filter(
            doctor=doctor, 
            visit_date__date=today,
            status__in=['scheduled', 'in_progress']
        ).order_by('visit_date')
        
        # Recent patients
        recent_patients = Visit.objects.filter(
            doctor=doctor
        ).order_by('-visit_date').distinct('patient')[:10]
        
        # Lab orders waiting for results
        pending_lab_orders = LabOrder.objects.filter(
            doctor=doctor, status='in_progress'
        ).order_by('-order_date')[:5]
        
        # Recent lab results
        recent_lab_results = LabResult.objects.filter(
            lab_order__doctor=doctor
        ).order_by('-result_date')[:5]
        
        context = {
            'doctor': doctor,
            'today_appointments': today_appointments,
            'recent_patients': recent_patients,
            'pending_lab_orders': pending_lab_orders,
            'recent_lab_results': recent_lab_results,
            'active_menu': 'dashboard',
        }
        
        return render(request, 'emr/dashboard/doctor_dashboard.html', context)
    except Doctor.DoesNotExist:
        # If doctor profile doesn't exist, redirect to user profile
        return redirect('users:profile')

# Patient views
@login_required
def patient_list_view(request):
    """View for listing patients"""
    if request.user.role not in ['doctor', 'receptionist', 'admin']:
        return redirect('emr:dashboard')
    
    search_query = request.GET.get('q', '')
    if search_query:
        patients = Patient.objects.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        ).order_by('user__last_name', 'user__first_name')
    else:
        patients = Patient.objects.all().order_by('user__last_name', 'user__first_name')
    
    context = {
        'patients': patients,
        'search_query': search_query,
        'active_menu': 'patients',
    }
    return render(request, 'emr/patients/patient_list.html', context)

@login_required
def patient_detail_view(request, pk):
    """View for patient details"""
    patient = get_object_or_404(Patient, pk=pk)
    
    # Check permissions
    user = request.user
    if user.role == 'patient' and user != patient.user:
        return redirect('emr:dashboard')
    
    # Get related data
    visits = Visit.objects.filter(patient=patient).order_by('-visit_date')
    active_prescriptions = Prescription.objects.filter(
        patient=patient, status='active'
    ).order_by('-created_at')
    lab_orders = LabOrder.objects.filter(patient=patient).order_by('-order_date')
    
    context = {
        'patient': patient,
        'visits': visits,
        'active_prescriptions': active_prescriptions,
        'lab_orders': lab_orders,
        'active_menu': 'patients',
    }
    return render(request, 'emr/patients/patient_detail.html', context)

@login_required
def patient_create_view(request):
    """View for creating a new patient"""
    if request.user.role not in ['receptionist', 'admin']:
        return redirect('emr:dashboard')
    
    # Implementation will depend on the form structure
    context = {
        'active_menu': 'patients',
    }
    return render(request, 'emr/patients/patient_form.html', context)

@login_required
def patient_edit_view(request, pk):
    """View for editing a patient"""
    if request.user.role not in ['receptionist', 'admin']:
        return redirect('emr:dashboard')
    
    patient = get_object_or_404(Patient, pk=pk)
    
    # Implementation will depend on the form structure
    context = {
        'patient': patient,
        'active_menu': 'patients',
    }
    return render(request, 'emr/patients/patient_form.html', context)

@login_required
def patient_medical_report_view(request, pk):
    """View for generating a medical report"""
    patient = get_object_or_404(Patient, pk=pk)
    
    # Check permissions
    user = request.user
    if user.role == 'patient' and user != patient.user:
        return redirect('emr:dashboard')
    
    # Reuse the PDF generation from the API view
    diagnoses = Diagnosis.objects.filter(patient=patient).order_by('-diagnosis_date')
    prescriptions = Prescription.objects.filter(patient=patient, status='active')
    lab_orders = LabOrder.objects.filter(patient=patient, status='completed').order_by('-order_date')[:5]
    
    pdf = generate_medical_report(patient, diagnoses, prescriptions, lab_orders)
    
    # Create the HttpResponse with PDF content
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"medical_report_{patient.user.last_name}_{patient.user.first_name}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

# Visit views
@login_required
def visit_list_view(request):
    """View for listing visits"""
    user = request.user
    
    if user.role == 'patient':
        return patient_visits_view(request)
    
    search_query = request.GET.get('q', '')
    
    if user.role == 'doctor':
        # Doctors can only see their own visits
        try:
            doctor = Doctor.objects.get(user=user)
            if search_query:
                visits = Visit.objects.filter(
                    Q(doctor=doctor),
                    Q(patient__user__first_name__icontains=search_query) |
                    Q(patient__user__last_name__icontains=search_query) |
                    Q(reason__icontains=search_query)
                ).order_by('-visit_date')
            else:
                visits = Visit.objects.filter(doctor=doctor).order_by('-visit_date')
        except Doctor.DoesNotExist:
            visits = Visit.objects.none()
    else:
        # Admin and receptionists can see all visits
        if search_query:
            visits = Visit.objects.filter(
                Q(patient__user__first_name__icontains=search_query) |
                Q(patient__user__last_name__icontains=search_query) |
                Q(doctor__user__first_name__icontains=search_query) |
                Q(doctor__user__last_name__icontains=search_query) |
                Q(reason__icontains=search_query)
            ).order_by('-visit_date')
        else:
            visits = Visit.objects.all().order_by('-visit_date')
    
    context = {
        'visits': visits,
        'search_query': search_query,
        'active_menu': 'visits',
    }
    return render(request, 'emr/visits/visit_list.html', context)

@login_required
def visit_detail_view(request, pk):
    """View for visit details"""
    visit = get_object_or_404(Visit, pk=pk)
    
    # Check permissions
    user = request.user
    if user.role == 'patient' and user != visit.patient.user:
        return redirect('emr:dashboard')
    if user.role == 'doctor' and user != visit.doctor.user:
        return redirect('emr:dashboard')
    
    context = {
        'visit': visit,
        'active_menu': 'visits',
    }
    return render(request, 'emr/visits/visit_detail.html', context)

@login_required
def visit_create_view(request):
    """View for creating a new visit"""
    if request.user.role not in ['doctor', 'receptionist', 'admin']:
        return redirect('emr:dashboard')
    
    # Get patient if provided in URL
    patient_id = request.GET.get('patient')
    patient = None
    if patient_id:
        patient = get_object_or_404(Patient, pk=patient_id)
    
    # Implementation will depend on the form structure
    context = {
        'patient': patient,
        'active_menu': 'visits',
    }
    return render(request, 'emr/visits/visit_form.html', context)

@login_required
def visit_edit_view(request, pk):
    """View for editing a visit"""
    if request.user.role not in ['doctor', 'receptionist', 'admin']:
        return redirect('emr:dashboard')
    
    visit = get_object_or_404(Visit, pk=pk)
    
    # Check permissions for doctors (can only edit their own visits)
    user = request.user
    if user.role == 'doctor' and user != visit.doctor.user:
        return redirect('emr:dashboard')
    
    # Implementation will depend on the form structure
    context = {
        'visit': visit,
        'active_menu': 'visits',
    }
    return render(request, 'emr/visits/visit_form.html', context)

@login_required
def patient_visits_view(request):
    """View for patients to see their visits"""
    # Only show visits for the current patient
    if request.user.role == 'patient':
        try:
            patient = request.user.patient_profile
            visits = Visit.objects.filter(patient=patient).order_by('-visit_date')
            return render(request, 'emr/visits/patient_visits.html', {
                'visits': visits
            })
        except:
            messages.error(request, "Patient profile not found")
            return redirect('emr:dashboard')
    else:
        messages.error(request, "Only patients can access this page")
        return redirect('emr:dashboard')

# Lab views (simplified - similar pattern for other views)
@login_required
def lab_order_list_view(request):
    """View for listing lab orders"""
    user = request.user
    
    if user.role == 'patient':
        return patient_lab_results_view(request)
    
    # Similar to visit_list_view logic but for lab orders
    context = {
        'active_menu': 'labs',
    }
    return render(request, 'emr/labs/lab_order_list.html', context)

@login_required
def lab_order_detail_view(request, pk):
    """View for lab order details"""
    lab_order = get_object_or_404(LabOrder, pk=pk)
    
    # Check permissions
    # Similar to visit_detail_view logic
    
    context = {
        'lab_order': lab_order,
        'active_menu': 'labs',
    }
    return render(request, 'emr/labs/lab_order_detail.html', context)

@login_required
def lab_order_create_view(request):
    """View for creating a new lab order"""
    if request.user.role != 'doctor':
        return redirect('emr:dashboard')
    
    # Implementation will depend on the form structure
    context = {
        'active_menu': 'labs',
    }
    return render(request, 'emr/labs/lab_order_form.html', context)

@login_required
def lab_order_edit_view(request, pk):
    """View for editing a lab order"""
    if request.user.role != 'doctor':
        return redirect('emr:dashboard')
    
    lab_order = get_object_or_404(LabOrder, pk=pk)
    
    # Check permissions
    # Similar to visit_edit_view logic
    
    context = {
        'lab_order': lab_order,
        'active_menu': 'labs',
    }
    return render(request, 'emr/labs/lab_order_form.html', context)

@login_required
def lab_order_update_status_view(request, pk):
    """View for updating lab order status"""
    if request.user.role not in ['doctor', 'lab_technician']:
        return redirect('emr:dashboard')
    
    lab_order = get_object_or_404(LabOrder, pk=pk)
    status = request.GET.get('status')
    
    # Update status and redirect back to detail view
    if status in ['scheduled', 'in_progress', 'completed', 'cancelled']:
        lab_order.status = status
        lab_order.save()
    
    return redirect('emr:lab_order_detail', pk=pk)

@login_required
def lab_result_create_view(request):
    """View for creating a new lab result"""
    if request.user.role not in ['doctor', 'lab_technician']:
        return redirect('emr:dashboard')
    
    # Get lab order if provided in URL
    order_id = request.GET.get('order')
    lab_order = None
    if order_id:
        lab_order = get_object_or_404(LabOrder, pk=order_id)
    
    # Implementation will depend on the form structure
    context = {
        'lab_order': lab_order,
        'active_menu': 'labs',
    }
    return render(request, 'emr/labs/lab_result_form.html', context)

@login_required
def lab_result_detail_view(request, pk):
    """View for lab result details"""
    lab_result = get_object_or_404(LabResult, pk=pk)
    
    # Check permissions
    # Similar to visit_detail_view logic
    
    context = {
        'lab_result': lab_result,
        'active_menu': 'labs',
    }
    return render(request, 'emr/labs/lab_result_detail.html', context)

@login_required
def lab_result_edit_view(request, pk):
    """View for editing a lab result"""
    if request.user.role not in ['doctor', 'lab_technician']:
        return redirect('emr:dashboard')
    
    lab_result = get_object_or_404(LabResult, pk=pk)
    
    # Implementation will depend on the form structure
    context = {
        'lab_result': lab_result,
        'active_menu': 'labs',
    }
    return render(request, 'emr/labs/lab_result_form.html', context)

@login_required
def patient_lab_results_view(request):
    """View for patients to see their lab results"""
    # Only show lab results for the current patient
    if request.user.role == 'patient':
        try:
            patient = request.user.patient_profile
            # Query both the direct relationship and the indirect relationship
            # to ensure we find all lab results
            lab_results = LabResult.objects.filter(
                models.Q(patient=patient) | models.Q(lab_order__patient=patient)
            ).select_related('lab_test', 'lab_order').order_by('-result_date')
            
            return render(request, 'emr/labs/patient_lab_results.html', {
                'lab_results': lab_results
            })
        except Exception as e:
            messages.error(request, f"Error retrieving lab results: {str(e)}")
            return redirect('emr:dashboard')
    else:
        messages.error(request, "Only patients can access this page")
        return redirect('emr:dashboard')

# Add placeholder functions for the remaining views
# Each view should follow similar patterns to those above

@login_required
def prescription_list_view(request):
    """View for listing prescriptions"""
    # Implementation similar to lab_order_list_view
    context = {'active_menu': 'prescriptions'}
    return render(request, 'emr/prescriptions/prescription_list.html', context)

@login_required
def prescription_create_view(request):
    """View for creating a prescription"""
    # Implementation similar to lab_order_create_view
    context = {'active_menu': 'prescriptions'}
    return render(request, 'emr/prescriptions/prescription_form.html', context)

@login_required
def prescription_detail_view(request, pk):
    """View for prescription details"""
    # Implementation similar to lab_result_detail_view
    context = {'active_menu': 'prescriptions'}
    return render(request, 'emr/prescriptions/prescription_detail.html', context)

@login_required
def prescription_edit_view(request, pk):
    """View for editing a prescription"""
    # Implementation similar to lab_result_edit_view
    context = {'active_menu': 'prescriptions'}
    return render(request, 'emr/prescriptions/prescription_form.html', context)

@login_required
def patient_prescriptions_view(request):
    """View for a patient's prescriptions"""
    # Implementation similar to patient_lab_results_view
    context = {'active_menu': 'my_prescriptions'}
    return render(request, 'emr/prescriptions/patient_prescriptions.html', context)

# Similar pattern for procedure views
@login_required
def procedure_list_view(request):
    context = {'active_menu': 'procedures'}
    return render(request, 'emr/procedures/procedure_list.html', context)

@login_required
def procedure_order_list_view(request):
    context = {'active_menu': 'procedures'}
    return render(request, 'emr/procedures/procedure_order_list.html', context)

@login_required
def procedure_order_create_view(request):
    context = {'active_menu': 'procedures'}
    return render(request, 'emr/procedures/procedure_order_form.html', context)

@login_required
def procedure_order_detail_view(request, pk):
    context = {'active_menu': 'procedures'}
    return render(request, 'emr/procedures/procedure_order_detail.html', context)

@login_required
def procedure_order_edit_view(request, pk):
    context = {'active_menu': 'procedures'}
    return render(request, 'emr/procedures/procedure_order_form.html', context)

@login_required
def patient_procedures_view(request):
    context = {'active_menu': 'my_procedures'}
    return render(request, 'emr/procedures/patient_procedures.html', context)

# Hospitalization views
@login_required
def hospitalization_list_view(request):
    context = {'active_menu': 'hospitalizations'}
    return render(request, 'emr/hospitalizations/hospitalization_list.html', context)

@login_required
def hospitalization_create_view(request):
    context = {'active_menu': 'hospitalizations'}
    return render(request, 'emr/hospitalizations/hospitalization_form.html', context)

@login_required
def hospitalization_detail_view(request, pk):
    context = {'active_menu': 'hospitalizations'}
    return render(request, 'emr/hospitalizations/hospitalization_detail.html', context)

@login_required
def hospitalization_edit_view(request, pk):
    context = {'active_menu': 'hospitalizations'}
    return render(request, 'emr/hospitalizations/hospitalization_form.html', context)

# Report views
@login_required
def report_list_view(request):
    context = {'active_menu': 'reports'}
    return render(request, 'emr/reports/report_list.html', context)

@login_required
def patient_reports_view(request):
    context = {'active_menu': 'my_reports'}
    return render(request, 'emr/reports/patient_reports.html', context)
