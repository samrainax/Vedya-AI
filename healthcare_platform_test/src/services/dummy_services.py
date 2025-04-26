import json
from datetime import datetime, timedelta
import random

class DummyDatabase:
    """Simple in-memory database for testing."""
    
    def __init__(self):
        # Initialize with some dummy data
        self.patients = {
            "P12345": {
                "patient_id": "P12345",
                "name": "John Doe",
                "age": 45,
                "location": {"lat": 28.6139, "lng": 77.2090, "address": "Village Nagar, District X"},
                "medical_history": [
                    {"condition": "Hypertension", "diagnosed": "2018-05-10"},
                    {"condition": "Type 2 Diabetes", "diagnosed": "2020-01-15"}
                ],
                "past_appointments": [
                    {"doctor": "Dr. Smith", "date": "2023-10-15", "reason": "Annual checkup"}
                ]
            }
        }
        
        self.doctors = {
            "D101": {
                "doctor_id": "D101",
                "name": "Dr. Amrita Singh",
                "specialty": "Cardiology",
                "hospital": "Community Healthcare Center",
                "location": {"lat": 28.7139, "lng": 77.1090},
                "working_hours": {
                    "Monday": "9:00-17:00",
                    "Wednesday": "9:00-17:00",
                    "Friday": "9:00-13:00"
                },
                "rating": 4.8
            },
            "D102": {
                "doctor_id": "D102",
                "name": "Dr. Rajan Kumar",
                "specialty": "General Medicine",
                "hospital": "Rural Medical Institute",
                "location": {"lat": 28.8139, "lng": 77.3090},
                "working_hours": {
                    "Tuesday": "9:00-17:00",
                    "Thursday": "9:00-17:00",
                    "Saturday": "9:00-13:00"
                },
                "rating": 4.5
            }
        }
        
        self.appointments = {
            "A98765": {
                "appointment_id": "A98765",
                "patient_id": "P12345",
                "doctor_id": "D101",
                "date": "2025-04-24",
                "time": "15:30",
                "reason": "Chest pain, shortness of breath",
                "status": "confirmed"
            }
        }

    def get_patient(self, patient_id):
        """Get patient by ID."""
        return self.patients.get(patient_id)
    
    def get_doctor(self, doctor_id):
        """Get doctor by ID."""
        return self.doctors.get(doctor_id)
    
    def get_appointment(self, appointment_id):
        """Get appointment by ID."""
        return self.appointments.get(appointment_id)
    
    def create_appointment(self, patient_id, doctor_id, date, time, reason):
        """Create a new appointment."""
        appointment_id = f"A{random.randint(10000, 99999)}"
        self.appointments[appointment_id] = {
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "date": date,
            "time": time,
            "reason": reason,
            "status": "confirmed"
        }
        return appointment_id
    
    def update_appointment(self, appointment_id, updates):
        """Update an existing appointment."""
        if appointment_id in self.appointments:
            self.appointments[appointment_id].update(updates)
            return True
        return False
    
    def delete_appointment(self, appointment_id):
        """Delete an appointment."""
        if appointment_id in self.appointments:
            del self.appointments[appointment_id]
            return True
        return False

    def match_doctors(self, specialty, patient_location, urgency_level="normal"):
        """Find matching doctors based on specialty and location."""
        matched_doctors = []
        for doctor_id, doctor in self.doctors.items():
            if doctor["specialty"].lower() == specialty.lower():
                # Calculate simple distance (this is a simplification)
                doctor_location = doctor["location"]
                distance = ((patient_location["lat"] - doctor_location["lat"])**2 + 
                           (patient_location["lng"] - doctor_location["lng"])**2)**0.5 * 111  # rough km conversion
                
                # Generate available slots for next few days
                today = datetime.now()
                available_slots = []
                for i in range(5):  # Next 5 days
                    next_date = today + timedelta(days=i)
                    day_name = next_date.strftime("%A")
                    if day_name in doctor["working_hours"]:
                        hours = doctor["working_hours"][day_name].split("-")
                        start_hour = int(hours[0].split(":")[0])
                        end_hour = int(hours[1].split(":")[0])
                        
                        slots = []
                        for hour in range(start_hour, end_hour):
                            for minute in [0, 30]:
                                slots.append(f"{hour:02d}:{minute:02d}")
                        
                        available_slots.append({
                            "date": next_date.strftime("%Y-%m-%d"), 
                            "slots": slots
                        })
                
                doctor_copy = doctor.copy()
                doctor_copy["distance_km"] = round(distance, 1)
                doctor_copy["available_slots"] = available_slots
                matched_doctors.append(doctor_copy)
        
        return matched_doctors

class DummyServices:
    """Implementation of dummy service APIs for testing the agents."""
    
    def __init__(self):
        self.db = DummyDatabase()
    
    def patient_profile_service(self, patient_id=None, update_data=None):
        """Get or update patient profile."""
        if update_data:
            # In a real implementation, we would update the patient data
            return {"status": "success", "message": "Profile updated"}
        else:
            # For simplicity, always return the default patient
            return self.db.get_patient("P12345")
    
    def symptom_analysis_service(self, symptoms, patient_info=None):
        """Analyze symptoms to suggest possible conditions and specialties."""
        # Simple keyword matching for demo
        if any(s.lower() in ["chest pain", "chest", "heart", "breathing"] for s in symptoms):
            return {
                "possible_conditions": ["Heart condition", "Respiratory issue"],
                "suggested_specialties": ["Cardiology", "Pulmonology"],
                "urgency_level": "high"
            }
        elif any(s.lower() in ["fever", "cold", "cough", "flu"] for s in symptoms):
            return {
                "possible_conditions": ["Common cold", "Influenza", "Seasonal infection"],
                "suggested_specialties": ["General Medicine"],
                "urgency_level": "normal"
            }
        elif any(s.lower() in ["headache", "migraine", "dizziness"] for s in symptoms):
            return {
                "possible_conditions": ["Migraine", "Tension headache"],
                "suggested_specialties": ["Neurology"],
                "urgency_level": "normal"
            }
        else:
            return {
                "possible_conditions": ["General health issue"],
                "suggested_specialties": ["General Medicine"],
                "urgency_level": "normal"
            }
    
    def doctor_matching_service(self, specialty, patient_location, urgency_level="normal"):
        """Find suitable doctors based on specialty and location."""
        matched_doctors = self.db.match_doctors(specialty, patient_location, urgency_level)
        return {"doctors": matched_doctors}
    
    def appointment_booking_service(self, action, patient_id, doctor_id=None, 
                                   date=None, time=None, old_appointment_id=None):
        """Book, reschedule, or cancel appointments."""
        if action == "book":
            if not all([patient_id, doctor_id, date, time]):
                return {"status": "error", "message": "Missing required information"}
            
            # Create new appointment
            appointment_id = self.db.create_appointment(
                patient_id, doctor_id, date, time, "New appointment"
            )
            doctor = self.db.get_doctor(doctor_id)
            
            return {
                "status": "success",
                "appointment_id": appointment_id,
                "doctor": doctor["name"],
                "date": date,
                "time": time,
                "hospital": doctor["hospital"],
                "address": "123 Medical Street, District X",
                "preparation_instructions": "Please bring your previous medical records"
            }
        
        elif action == "reschedule":
            if not old_appointment_id or not date or not time:
                return {"status": "error", "message": "Missing required information"}
            
            if self.db.update_appointment(old_appointment_id, {"date": date, "time": time}):
                return {
                    "status": "success",
                    "appointment_id": old_appointment_id,
                    "new_date": date,
                    "new_time": time,
                    "message": "Your appointment has been rescheduled"
                }
            return {"status": "error", "message": "Appointment not found"}
        
        elif action == "cancel":
            if not old_appointment_id:
                return {"status": "error", "message": "Missing appointment ID"}
            
            if self.db.delete_appointment(old_appointment_id):
                return {
                    "status": "success",
                    "appointment_id": old_appointment_id,
                    "message": "Your appointment has been cancelled"
                }
            return {"status": "error", "message": "Appointment not found"}
        
        return {"status": "error", "message": "Invalid action"}
    
    def notification_service(self, recipient_type, recipient_id, notification_type, content):
        """Send notifications to patients or doctors."""
        # In a real implementation, this would send WhatsApp/SMS messages
        return {
            "status": "success",
            "notification_id": f"N{random.randint(100000, 999999)}",
            "delivered": True,
            "channel": "WhatsApp" if recipient_type == "patient" else "App"
        }
    
    def doctor_profile_service(self, doctor_id=None, update_data=None):
        """Get or update doctor profile."""
        if update_data:
            # In a real implementation, we would update the doctor data
            return {"status": "success", "message": "Profile updated"}
        else:
            return self.db.get_doctor(doctor_id or "D101")
    
    def doctor_schedule_service(self, doctor_id, date=None, action="view"):
        """View or update doctor's schedule."""
        if action == "view":
            doctor = self.db.get_doctor(doctor_id)
            if not doctor:
                return {"status": "error", "message": "Doctor not found"}
            
            today = datetime.now()
            
            # Get appointments for this doctor
            doctor_appointments = [
                appt for appt_id, appt in self.db.appointments.items()
                if appt["doctor_id"] == doctor_id
            ]
            
            if not date:
                return {
                    "today": today.strftime("%Y-%m-%d"),
                    "upcoming_appointments": doctor_appointments
                }
            else:
                # Filter appointments for specific date
                date_appointments = [
                    appt for appt in doctor_appointments
                    if appt["date"] == date
                ]
                
                return {
                    "date": date,
                    "appointments": date_appointments
                }
        
        return {"status": "error", "message": "Invalid action"}
    
    def patient_info_service(self, patient_id):
        """Get detailed information about a patient."""
        patient = self.db.get_patient(patient_id)
        if not patient:
            return {"status": "error", "message": "Patient not found"}
        
        # Add some additional details for doctor's view
        patient_copy = patient.copy()
        patient_copy.update({
            "allergies": ["Penicillin"],
            "vitals": {
                "last_recorded": "2023-10-15",
                "blood_pressure": "130/85",
                "heart_rate": 78,
                "temperature": "98.6F"
            }
        })
        
        return patient_copy
    
    def appointment_management_service(self, action, appointment_id, details=None):
        """Manage appointments (reschedule, cancel, add notes)."""
        if action == "reschedule":
            if not details or "new_date" not in details or "new_time" not in details:
                return {"status": "error", "message": "Missing date/time details"}
            
            if self.db.update_appointment(appointment_id, {
                "date": details["new_date"],
                "time": details["new_time"]
            }):
                return {
                    "status": "success",
                    "message": "Appointment rescheduled",
                    "appointment_id": appointment_id,
                    "new_date": details["new_date"],
                    "new_time": details["new_time"]
                }
            return {"status": "error", "message": "Appointment not found"}
        
        elif action == "cancel":
            if self.db.delete_appointment(appointment_id):
                return {
                    "status": "success",
                    "message": "Appointment cancelled",
                    "appointment_id": appointment_id
                }
            return {"status": "error", "message": "Appointment not found"}
        
        elif action == "add_notes":
            if not details or "notes" not in details:
                return {"status": "error", "message": "Missing notes"}
            
            if self.db.update_appointment(appointment_id, {"notes": details["notes"]}):
                return {
                    "status": "success",
                    "message": "Notes added",
                    "appointment_id": appointment_id
                }
            return {"status": "error", "message": "Appointment not found"}
        
        return {"status": "error", "message": "Invalid action"}
    
    def availability_management_service(self, doctor_id, updates):
        """Update doctor's availability schedule."""
        doctor = self.db.get_doctor(doctor_id)
        if not doctor:
            return {"status": "error", "message": "Doctor not found"}
        
        for update in updates:
            day = update.get("day")
            hours = update.get("hours")
            if day and hours:
                doctor["working_hours"][day] = hours
        
        return {
            "status": "success",
            "message": "Availability updated successfully",
            "updated_days": [update["day"] for update in updates if "day" in update]
        }