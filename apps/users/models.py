from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('receptionist', 'Receptionist'),
        ('patient', 'Patient'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create Patient or Doctor profile when a user is created
    """
    if created:
        # Import here to avoid circular imports
        from apps.emr.models import Patient, Doctor
        
        if instance.role == 'patient':
            # Create associated patient profile
            Patient.objects.create(
                user=instance,
                date_of_birth=instance.date_of_birth or None
            )
        elif instance.role == 'doctor':
            # Create associated doctor profile
            Doctor.objects.create(
                user=instance,
                specialization='General'  # Default value
            ) 