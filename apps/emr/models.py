from django.db import models
from django.conf import settings
from django.utils import timezone

class Patient(models.Model):
    """Patient model representing a person receiving medical care"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField()
    blood_group = models.CharField(max_length=10, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    chronic_diseases = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    
class Doctor(models.Model):
    """Doctor model representing a medical professional"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    experience_years = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"Dr. {self.user.first_name} {self.user.last_name} ({self.specialization})"


class Department(models.Model):
    """Department in the clinic"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name


class Visit(models.Model):
    """Model for patient visits to the clinic"""
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='visits')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='patient_visits')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='visits')
    visit_date = models.DateTimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient} - {self.visit_date.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-visit_date']


class Diagnosis(models.Model):
    """Medical diagnosis model"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='diagnoses')
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='diagnoses')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='diagnoses')
    diagnosis_code = models.CharField(max_length=20)  # ICD-10 or similar code
    diagnosis_name = models.CharField(max_length=255)
    description = models.TextField()
    diagnosis_date = models.DateTimeField(default=timezone.now)
    is_primary = models.BooleanField(default=True)
    is_chronic = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.diagnosis_name} ({self.diagnosis_code})"
    
    class Meta:
        ordering = ['-diagnosis_date']


class LabTest(models.Model):
    """Model for laboratory tests"""
    STATUS_CHOICES = (
        ('ordered', 'Ordered'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    normal_range = models.CharField(max_length=100, blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return self.name


class LabOrder(models.Model):
    """Model for lab test orders"""
    STATUS_CHOICES = (
        ('ordered', 'Ordered'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='lab_orders')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='ordered_labs')
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='lab_orders')
    order_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    priority = models.CharField(max_length=20, choices=[('routine', 'Routine'), ('urgent', 'Urgent')], default='routine')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Lab Order {self.id} - {self.patient}"


class LabResult(models.Model):
    """Model for lab test results"""
    lab_order = models.ForeignKey(LabOrder, on_delete=models.CASCADE, related_name='results')
    lab_test = models.ForeignKey(LabTest, on_delete=models.CASCADE, related_name='test_results')
    value = models.CharField(max_length=100)
    is_abnormal = models.BooleanField(default=False)
    result_date = models.DateTimeField(default=timezone.now)
    performed_by = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.lab_test.name}: {self.value} {self.lab_test.unit or ''}"


class Medication(models.Model):
    """Model for medications"""
    name = models.CharField(max_length=255)
    generic_name = models.CharField(max_length=255, blank=True, null=True)
    form = models.CharField(max_length=50, choices=[
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('liquid', 'Liquid'),
        ('injection', 'Injection'),
        ('cream', 'Cream'),
        ('ointment', 'Ointment'),
        ('other', 'Other'),
    ])
    strength = models.CharField(max_length=50, blank=True, null=True)
    manufacturer = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} {self.strength or ''}"


class Prescription(models.Model):
    """Model for medication prescriptions"""
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescribed_medications')
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='prescriptions')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='prescriptions')
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    refills = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.medication.name} - {self.patient}"


class Procedure(models.Model):
    """Model for medical procedures"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    procedure_code = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self):
        return self.name


class ProcedureOrder(models.Model):
    """Model for procedure orders"""
    STATUS_CHOICES = (
        ('ordered', 'Ordered'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='procedures')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='ordered_procedures')
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='procedures')
    procedure = models.ForeignKey(Procedure, on_delete=models.CASCADE, related_name='orders')
    order_date = models.DateTimeField(default=timezone.now)
    scheduled_date = models.DateTimeField(blank=True, null=True)
    completion_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.procedure.name} - {self.patient}"


class Hospitalization(models.Model):
    """Model for hospitalizations"""
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('admitted', 'Admitted'),
        ('discharged', 'Discharged'),
        ('cancelled', 'Cancelled'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='hospitalizations')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='hospitalized_patients')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='hospitalizations')
    related_visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, related_name='hospitalizations')
    reason = models.TextField()
    admission_date = models.DateTimeField()
    discharge_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    discharge_summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient} - {self.admission_date.strftime('%Y-%m-%d')}"
