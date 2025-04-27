import random
from datetime import datetime, timedelta

class DummyDatabase:
    """Simple in-memory DB."""
    def __init__(self):
        self.patients = {
            "user123": {
                "user_id": "user123",
                "name": "John Doe",
                "location": {"lat": 28.6, "lng": 77.2, "address": "Village X, District Y"},
                "previous_context": {},
                "previous_messages": [],
            }
        }
        self.doctors = {
            "doc1": {
                "doctor_id": "doc1",
                "name": "Dr. Amrita Singh",
                "specialty": "Cardiology",
                "hospital": "Community Health Center",
                "location": {"lat": 28.7, "lng": 77.1},
                "rating": 4.8
            },
            "doc2": {
                "doctor_id": "doc2",
                "name": "Dr. Rajan Kumar",
                "specialty": "General Medicine",
                "hospital": "Rural Hospital",
                "location": {"lat": 28.8, "lng": 77.3},
                "rating": 4.5
            }
        }
        self.appointments = {}

    def get_patient_profile(self, user_id):
        return self.patients.get(user_id)

    def get_doctors_by_specialty(self, specialty):
        return [
            doctor for doctor in self.doctors.values()
            if doctor["specialty"].lower() == specialty.lower()
        ]

    def create_appointment(self, user_id, doctor_id, date="2025-05-01", time="10:00"):
        appointment_id = f"appt{random.randint(1000, 9999)}"
        self.appointments[appointment_id] = {
            "appointment_id": appointment_id,
            "user_id": user_id,
            "doctor_id": doctor_id,
            "date": date,
            "time": time,
            "status": "confirmed"
        }
        return self.appointments[appointment_id]

    def send_notification(self, user_id, message):
        return {"status": "sent", "message": message, "user_id": user_id}


class DummyServices:
    """Service layer matching agent needs."""
    def __init__(self):
        self.db = DummyDatabase()

    def fetch_user_profile(self, user_id):
        """Fetch user profile + context."""
        patient = self.db.get_patient_profile(user_id)
        if patient:
            return {
                "previous_context": patient.get("previous_context", {}),
                "previous_messages": patient.get("previous_messages", [])
            }
        return {"previous_context": {}, "previous_messages": []}

    def get_doctor_list(self, specialty):
        """Get list of doctors matching specialty."""
        doctors = self.db.get_doctors_by_specialty(specialty)
        # Add dummy slots
        today = datetime.now()
        for doctor in doctors:
            slots = []
            for i in range(5):
                day = (today + timedelta(days=i)).strftime("%Y-%m-%d")
                slots.append({"date": day, "times": ["10:00", "11:00", "15:00"]})
            doctor["available_slots"] = slots
        return doctors

    def book_appointment_service(self, appointment_info):
        """Book an appointment."""
        user_id = appointment_info["user_id"]
        doctor_id = appointment_info["doctor_id"]
        date = appointment_info.get("preferred_date", "2025-05-01")
        time = appointment_info.get("preferred_time", "10:00")
        return self.db.create_appointment(user_id, doctor_id, date, time)

    def notification_service(self, user_id, message):
        """Send notification to patient."""
        return self.db.send_notification(user_id, message)
