from rest_framework import serializers
from .models import (
    Patient, Doctor, Department, Visit, Diagnosis, 
    LabTest, LabOrder, LabResult, Medication, 
    Prescription, Procedure, ProcedureOrder, Hospitalization
)
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']


class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Patient
        fields = '__all__'


class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Doctor
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'


class VisitListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Visit
        fields = ['id', 'patient', 'patient_name', 'doctor', 'doctor_name', 
                  'department', 'department_name', 'visit_date', 'reason', 
                  'status', 'created_at']
    
    def get_patient_name(self, obj):
        return str(obj.patient)
    
    def get_doctor_name(self, obj):
        return str(obj.doctor)
    
    def get_department_name(self, obj):
        return str(obj.department) if obj.department else None


class VisitDetailSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    
    class Meta:
        model = Visit
        fields = '__all__'


class DiagnosisSerializer(serializers.ModelSerializer):
    doctor_name = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Diagnosis
        fields = '__all__'
    
    def get_doctor_name(self, obj):
        return str(obj.doctor)


class LabTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTest
        fields = '__all__'


class LabOrderListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LabOrder
        fields = ['id', 'patient', 'patient_name', 'doctor', 'doctor_name', 
                  'order_date', 'status', 'priority']
    
    def get_patient_name(self, obj):
        return str(obj.patient)
    
    def get_doctor_name(self, obj):
        return str(obj.doctor)


class LabResultSerializer(serializers.ModelSerializer):
    lab_test_name = serializers.SerializerMethodField()
    lab_test_unit = serializers.SerializerMethodField()
    
    class Meta:
        model = LabResult
        fields = '__all__'
    
    def get_lab_test_name(self, obj):
        return obj.lab_test.name
    
    def get_lab_test_unit(self, obj):
        return obj.lab_test.unit


class LabOrderDetailSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    results = LabResultSerializer(many=True, read_only=True)
    
    class Meta:
        model = LabOrder
        fields = '__all__'


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'


class PrescriptionListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.SerializerMethodField()
    medication_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Prescription
        fields = ['id', 'patient', 'patient_name', 'doctor', 'doctor_name',
                  'medication', 'medication_name', 'start_date', 'status']
    
    def get_patient_name(self, obj):
        return str(obj.patient)
    
    def get_doctor_name(self, obj):
        return str(obj.doctor)
    
    def get_medication_name(self, obj):
        return str(obj.medication)


class PrescriptionDetailSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    medication = MedicationSerializer(read_only=True)
    
    class Meta:
        model = Prescription
        fields = '__all__'


class ProcedureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Procedure
        fields = '__all__'


class ProcedureOrderListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    procedure_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProcedureOrder
        fields = ['id', 'patient', 'patient_name', 'procedure', 'procedure_name', 
                  'order_date', 'scheduled_date', 'status']
    
    def get_patient_name(self, obj):
        return str(obj.patient)
    
    def get_procedure_name(self, obj):
        return obj.procedure.name


class ProcedureOrderDetailSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    procedure = ProcedureSerializer(read_only=True)
    
    class Meta:
        model = ProcedureOrder
        fields = '__all__'


class HospitalizationListSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Hospitalization
        fields = ['id', 'patient', 'patient_name', 'department', 'department_name',
                  'admission_date', 'discharge_date', 'status']
    
    def get_patient_name(self, obj):
        return str(obj.patient)
    
    def get_department_name(self, obj):
        return str(obj.department)


class HospitalizationDetailSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    doctor = DoctorSerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    
    class Meta:
        model = Hospitalization
        fields = '__all__' 