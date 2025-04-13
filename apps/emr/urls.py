from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'emr'

router = DefaultRouter()
router.register(r'patients', views.PatientViewSet)
router.register(r'doctors', views.DoctorViewSet)
router.register(r'departments', views.DepartmentViewSet)
router.register(r'visits', views.VisitViewSet)
router.register(r'diagnoses', views.DiagnosisViewSet)
router.register(r'lab-tests', views.LabTestViewSet)
router.register(r'lab-orders', views.LabOrderViewSet)
router.register(r'lab-results', views.LabResultViewSet)
router.register(r'medications', views.MedicationViewSet)
router.register(r'prescriptions', views.PrescriptionViewSet)
router.register(r'procedures', views.ProcedureViewSet)
router.register(r'procedure-orders', views.ProcedureOrderViewSet)
router.register(r'hospitalizations', views.HospitalizationViewSet)
router.register(r'my-visits', views.PatientVisitViewSet, basename='patient-visits')
router.register(r'my-lab-results', views.PatientLabResultViewSet, basename='patient-lab-results')

# API URLs
api_urls = [
    path('', include(router.urls)),
]

# Template URLs for web interface
template_urls = [
    # Dashboard URLs
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('patient-dashboard/', views.patient_dashboard_view, name='patient_dashboard'),
    path('doctor-dashboard/', views.doctor_dashboard_view, name='doctor_dashboard'),
    
    # Patient URLs
    path('patients/', views.patient_list_view, name='patient_list'),
    path('patients/<int:pk>/', views.patient_detail_view, name='patient_detail'),
    path('patients/create/', views.patient_create_view, name='patient_create'),
    path('patients/<int:pk>/edit/', views.patient_edit_view, name='patient_edit'),
    path('patients/<int:pk>/medical-report/', views.patient_medical_report_view, name='medical_report'),
    
    # Visit URLs
    path('visits/', views.visit_list_view, name='visit_list'),
    path('visits/<int:pk>/', views.visit_detail_view, name='visit_detail'),
    path('visits/create/', views.visit_create_view, name='visit_create'),
    path('visits/<int:pk>/edit/', views.visit_edit_view, name='visit_edit'),
    path('my-visits/', views.patient_visits_view, name='patient_visits'),
    
    # Lab URLs
    path('lab-orders/', views.lab_order_list_view, name='lab_order_list'),
    path('lab-orders/<int:pk>/', views.lab_order_detail_view, name='lab_order_detail'),
    path('lab-orders/create/', views.lab_order_create_view, name='lab_order_create'),
    path('lab-orders/<int:pk>/edit/', views.lab_order_edit_view, name='lab_order_edit'),
    path('lab-orders/<int:pk>/update-status/', views.lab_order_update_status_view, name='lab_order_update_status'),
    path('lab-results/create/', views.lab_result_create_view, name='lab_result_create'),
    path('lab-results/<int:pk>/', views.lab_result_detail_view, name='lab_result_detail'),
    path('lab-results/<int:pk>/edit/', views.lab_result_edit_view, name='lab_result_edit'),
    path('my-lab-results/', views.patient_lab_results_view, name='patient_lab_results'),
    
    # Prescription URLs
    path('prescriptions/', views.prescription_list_view, name='prescription_list'),
    path('prescriptions/create/', views.prescription_create_view, name='prescription_create'),
    path('prescriptions/<int:pk>/', views.prescription_detail_view, name='prescription_detail'),
    path('prescriptions/<int:pk>/edit/', views.prescription_edit_view, name='prescription_edit'),
    path('my-prescriptions/', views.patient_prescriptions_view, name='patient_prescriptions'),
    
    # Procedure URLs
    path('procedures/', views.procedure_list_view, name='procedure_list'),
    path('procedure-orders/', views.procedure_order_list_view, name='procedure_order_list'),
    path('procedure-orders/create/', views.procedure_order_create_view, name='procedure_order_create'),
    path('procedure-orders/<int:pk>/', views.procedure_order_detail_view, name='procedure_order_detail'),
    path('procedure-orders/<int:pk>/edit/', views.procedure_order_edit_view, name='procedure_order_edit'),
    path('my-procedures/', views.patient_procedures_view, name='patient_procedures'),
    
    # Hospitalization URLs
    path('hospitalizations/', views.hospitalization_list_view, name='hospitalization_list'),
    path('hospitalizations/create/', views.hospitalization_create_view, name='hospitalization_create'),
    path('hospitalizations/<int:pk>/', views.hospitalization_detail_view, name='hospitalization_detail'),
    path('hospitalizations/<int:pk>/edit/', views.hospitalization_edit_view, name='hospitalization_edit'),
    
    # Report URLs
    path('reports/', views.report_list_view, name='report_list'),
    path('my-reports/', views.patient_reports_view, name='patient_reports'),
]

urlpatterns = api_urls + template_urls 