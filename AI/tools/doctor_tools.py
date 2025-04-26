from langchain.tools import BaseTool
import json
import sys
import os
from datetime import datetime, timedelta

class GetDoctorScheduleTool(BaseTool):
    """Tool to get a doctor's schedule"""
    name = "get_doctor_schedule"
    description = "Get a doctor's appointment schedule"
    
    def _run(self, doctor_id, date=None):
        """Get the schedule for the specified doctor"""
        # In a real implementation, this would query the database
        # For now, return mock data
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        return json.dumps({
            "doctor_id": doctor_id,
            "appointments": [
                {"time": f"{today} 10:00", "patient": "John Doe", "reason": "Headache", "status": "scheduled"},
                {"time": f"{today} 11:30", "patient": "Jane Smith", "reason": "Follow-up", "status": "scheduled"},
                {"time": f"{tomorrow} 09:00", "patient": "Alice Johnson", "reason": "Fever", "status": "scheduled"},
            ]
        })
    
    async def _arun(self, doctor_id, date=None):
        # Async implementation would be similar
        return self._run(doctor_id, date)

class UpdateAvailabilityTool(BaseTool):
    """Tool to update a doctor's availability"""
    name = "update_availability"
    description = "Update a doctor's availability schedule"
    
    def _run(self, doctor_id, availability):
        """Update the availability for the specified doctor"""
        # In a real implementation, this would update the database
        # For now, just return success
        if isinstance(availability, str):
            try:
                availability = json.loads(availability)
            except json.JSONDecodeError:
                return json.dumps({"error": "Invalid JSON in availability"})
        
        return json.dumps({
            "success": True,
            "doctor_id": doctor_id,
            "availability": availability
        })
    
    async def _arun(self, doctor_id, availability):
        # Async implementation would be similar
        return self._run(doctor_id, availability)

class GetPatientHistoryTool(BaseTool):
    """Tool to get a patient's medical history"""
    name = "get_patient_history"
    description = "Get a patient's medical history"
    
    def _run(self, patient_id):
        """Get the medical history for the specified patient"""
        # In a real implementation, this would query the database
        # For now, return mock data
        return json.dumps({
            "patient_id": patient_id,
            "name": "John Doe",
            "age": 35,
            "medical_history": {
                "allergies": ["Penicillin"],
                "chronic_conditions": [],
                "previous_surgeries": ["Appendectomy 2018"]
            },
            "recent_appointments": [
                {"date": "2023-03-15", "doctor": "Dr. Smith", "reason": "Headache", "notes": "Prescribed paracetamol"},
                {"date": "2023-01-20", "doctor": "Dr. Johnson", "reason": "Flu", "notes": "Rest and fluids recommended"}
            ]
        })
    
    async def _arun(self, patient_id):
        # Async implementation would be similar
        return self._run(patient_id)

class AddAppointmentNotesTool(BaseTool):
    """Tool to add notes to an appointment"""
    name = "add_appointment_notes"
    description = "Add notes to a patient appointment"
    
    def _run(self, appointment_id, notes):
        """Add notes to the specified appointment"""
        # In a real implementation, this would update the database
        # For now, just return success
        return json.dumps({
            "success": True,
            "appointment_id": appointment_id,
            "notes": notes
        })
    
    async def _arun(self, appointment_id, notes):
        # Async implementation would be similar
        return self._run(appointment_id, notes)
