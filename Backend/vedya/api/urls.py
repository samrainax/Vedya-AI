from django.urls import path
from . import views

urlpatterns = [
    path('webhook/twilio/', views.twilio_webhook, name='twilio_webhook'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('patients/', views.patient_list, name='patient_list'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/<str:appointment_id>/', views.appointment_detail, name='appointment_detail'),
]
