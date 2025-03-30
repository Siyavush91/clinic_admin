from django.contrib import admin
from .models import (
    Patient, Doctor, Department, Visit, Diagnosis,
    LabTest, LabOrder, LabResult, Medication,
    Prescription, Procedure, ProcedureOrder, Hospitalization
)

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_of_birth', 'blood_group')
    search_fields = ('user__first_name', 'user__last_name', 'user__email')


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'license_number', 'experience_years')
    search_fields = ('user__first_name', 'user__last_name', 'specialization')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'department', 'visit_date', 'status')
    list_filter = ('status', 'department')
    search_fields = ('patient__user__first_name', 'patient__user__last_name', 'doctor__user__last_name')
    date_hierarchy = 'visit_date'


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('patient', 'diagnosis_code', 'diagnosis_name', 'doctor', 'diagnosis_date', 'is_primary', 'is_chronic')
    list_filter = ('is_primary', 'is_chronic', 'diagnosis_date')
    search_fields = ('diagnosis_name', 'diagnosis_code', 'patient__user__last_name')
    date_hierarchy = 'diagnosis_date'


@admin.register(LabTest)
class LabTestAdmin(admin.ModelAdmin):
    list_display = ('name', 'normal_range', 'unit')
    search_fields = ('name', 'description')


@admin.register(LabOrder)
class LabOrderAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'order_date', 'status', 'priority')
    list_filter = ('status', 'priority', 'order_date')
    search_fields = ('patient__user__last_name', 'doctor__user__last_name')
    date_hierarchy = 'order_date'


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ('lab_order', 'lab_test', 'value', 'is_abnormal', 'result_date')
    list_filter = ('is_abnormal', 'result_date')
    search_fields = ('lab_order__patient__user__last_name', 'lab_test__name')
    date_hierarchy = 'result_date'


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'form', 'strength')
    list_filter = ('form',)
    search_fields = ('name', 'generic_name')


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'medication', 'dosage', 'frequency', 'start_date', 'status')
    list_filter = ('status', 'start_date')
    search_fields = ('patient__user__last_name', 'medication__name')
    date_hierarchy = 'start_date'


@admin.register(Procedure)
class ProcedureAdmin(admin.ModelAdmin):
    list_display = ('name', 'procedure_code')
    search_fields = ('name', 'description', 'procedure_code')


@admin.register(ProcedureOrder)
class ProcedureOrderAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'procedure', 'order_date', 'scheduled_date', 'status')
    list_filter = ('status', 'order_date')
    search_fields = ('patient__user__last_name', 'procedure__name')
    date_hierarchy = 'order_date'


@admin.register(Hospitalization)
class HospitalizationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'department', 'admission_date', 'discharge_date', 'status')
    list_filter = ('status', 'department', 'admission_date')
    search_fields = ('patient__user__last_name', 'reason')
    date_hierarchy = 'admission_date'
