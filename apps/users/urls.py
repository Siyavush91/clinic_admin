from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, PatientRegistrationAPIView, StaffRegistrationAPIView
from . import views

app_name = 'users'

router = DefaultRouter()
router.register(r'users', UserViewSet)

api_urlpatterns = [
    path('', include(router.urls)),
    path('register/patient/', PatientRegistrationAPIView.as_view(), name='patient-registration'),
    path('register/staff/', StaffRegistrationAPIView.as_view(), name='staff-registration'),
]

template_urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('register/staff/', views.register_view, name='staff-registration'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    path('patient-dashboard/', views.profile_view, name='patient_dashboard'),
    path('doctor-dashboard/', views.profile_view, name='doctor_dashboard'),
]

# Kept for backward compatibility
urlpatterns = template_urlpatterns 