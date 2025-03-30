from rest_framework import permissions

class IsDoctor(permissions.BasePermission):
    """
    Permission to check if the user is a doctor.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'doctor'


class IsPatient(permissions.BasePermission):
    """
    Permission to check if the user is a patient.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'patient'


class IsReceptionist(permissions.BasePermission):
    """
    Permission to check if the user is a receptionist.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'receptionist'


class IsAdmin(permissions.BasePermission):
    """
    Permission to check if the user is an admin.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsDoctorOrAdmin(permissions.BasePermission):
    """
    Permission to check if the user is a doctor or admin.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['doctor', 'admin']


class IsDoctorOrReceptionist(permissions.BasePermission):
    """
    Permission to check if the user is a doctor or receptionist.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['doctor', 'receptionist']


class IsPatientOwner(permissions.BasePermission):
    """
    Object-level permission to check if the user is the patient
    associated with the object.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is the patient associated with this object
        if hasattr(obj, 'patient') and hasattr(obj.patient, 'user'):
            return obj.patient.user == request.user
        return False


class IsDoctorAssigned(permissions.BasePermission):
    """
    Object-level permission to check if the user is the assigned doctor
    associated with the object.
    """
    def has_object_permission(self, request, view, obj):
        # Check if user is the doctor associated with this object
        if hasattr(obj, 'doctor') and hasattr(obj.doctor, 'user'):
            return obj.doctor.user == request.user
        return False


class IsPatientOwnerOrDoctorAssigned(permissions.BasePermission):
    """
    Object-level permission to check if the user is either the patient owner
    or the assigned doctor for the object.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for patient owner or assigned doctor
        patient_owner = False
        doctor_assigned = False
        
        if hasattr(obj, 'patient') and hasattr(obj.patient, 'user'):
            patient_owner = obj.patient.user == request.user
            
        if hasattr(obj, 'doctor') and hasattr(obj.doctor, 'user'):
            doctor_assigned = obj.doctor.user == request.user
            
        # Allow SAFE_METHODS for both, but modifications only for doctor
        if request.method in permissions.SAFE_METHODS:
            return patient_owner or doctor_assigned
        return doctor_assigned 