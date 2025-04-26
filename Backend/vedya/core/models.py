from django.db import models
from django.contrib.auth.models import User

class Doctor(models.Model):
    """Doctor model represents healthcare providers in the system"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    experience_years = models.PositiveIntegerField(default=0)
    phone_number = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    availability = models.JSONField(default=dict)  # Store availability schedule as JSON
    whatsapp_enabled = models.BooleanField(default=False)  # Whether doctor uses WhatsApp interface
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.specialization}"

class Patient(models.Model):
    """Patient model represents users seeking medical consultation"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile', null=True, blank=True)
    whatsapp_number = models.CharField(max_length=20, unique=True)  # Primary contact method
    full_name = models.CharField(max_length=255)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    medical_history = models.JSONField(default=dict, blank=True)  # Store medical history as JSON
    
    def __str__(self):
        return f"{self.full_name} ({self.whatsapp_number})"

class Appointment(models.Model):
    """Appointment model represents scheduled meetings between doctors and patients"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    scheduled_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    symptoms = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient} - {self.doctor} - {self.scheduled_time.strftime('%Y-%m-%d %H:%M')}"

class Conversation(models.Model):
    """Conversation model stores message history for WhatsApp interactions"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='conversations')
    started_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)  # Whether conversation is ongoing
    context = models.JSONField(default=dict, blank=True)  # Store conversation context/state
    
    def __str__(self):
        return f"Conversation with {self.patient} started at {self.started_at.strftime('%Y-%m-%d %H:%M')}"

class Message(models.Model):
    """Message model represents individual messages in a conversation"""
    SENDER_CHOICES = [
        ('patient', 'Patient'),
        ('system', 'System'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES)
    content = models.TextField()
    media_url = models.URLField(blank=True, null=True)  # For voice messages or images
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.sender} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
