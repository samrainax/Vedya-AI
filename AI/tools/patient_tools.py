from langchain.tools import BaseTool
import json
import sys
import os

class ExtractSymptomsTool(BaseTool):
    """Tool to extract symptoms from patient messages"""
    name = "extract_symptoms"
    description = "Extract symptoms from a patient message"
    
    def _run(self, message):
        """Extract symptoms from the given message"""
        # In a real implementation, this would use NLP/LLM to extract symptoms
        # For now, use a simple keyword approach
        symptoms = []
        symptom_keywords = {
            "headache": "Head pain",
            "fever": "Elevated body temperature",
            "cough": "Expulsion of air from lungs",
            "pain": "Discomfort",
            "chest pain": "Discomfort in chest",
            "stomachache": "Abdominal pain",
            "nausea": "Feeling of sickness with an inclination to vomit",
            "dizziness": "Feeling of being unsteady or lightheaded"
        }
        
        message_lower = message.lower()
        for keyword, description in symptom_keywords.items():
            if keyword in message_lower:
                symptoms.append({"name": keyword, "description": description})
        
        return json.dumps(symptoms)
    
    async def _arun(self, message):
        # Async implementation would be similar
        return self._run(message)

class GetPatientProfileTool(BaseTool):
    """Tool to get a patient's profile"""
    name = "get_patient_profile"
    description = "Get a patient's profile information"
    
    def _run(self, patient_id=None, whatsapp_number=None):
        """Get profile for the specified patient"""
        # In a real implementation, this would query the database
        # For now, return mock data
        if patient_id or whatsapp_number:
            return json.dumps({
                "id": patient_id or "123",
                "name": "John Doe",
                "age": 35,
                "gender": "Male",
                "location": "Mumbai",
                "medical_history": {
                    "allergies": ["Penicillin"],
                    "chronic_conditions": [],
                    "previous_surgeries": ["Appendectomy 2018"]
                }
            })
        else:
            return json.dumps({"error": "Must provide either patient_id or whatsapp_number"})
    
    async def _arun(self, patient_id=None, whatsapp_number=None):
        # Async implementation would be similar
        return self._run(patient_id, whatsapp_number)

class UpdatePatientProfileTool(BaseTool):
    """Tool to update a patient's profile"""
    name = "update_patient_profile"
    description = "Update a patient's profile information"
    
    def _run(self, patient_id, updates):
        """Update the specified patient's profile"""
        # In a real implementation, this would update the database
        # For now, just return success
        if isinstance(updates, str):
            try:
                updates = json.loads(updates)
            except json.JSONDecodeError:
                return json.dumps({"error": "Invalid JSON in updates"})
        
        return json.dumps({
            "success": True,
            "patient_id": patient_id,
            "updated_fields": list(updates.keys())
        })
    
    async def _arun(self, patient_id, updates):
        # Async implementation would be similar
        return self._run(patient_id, updates)
