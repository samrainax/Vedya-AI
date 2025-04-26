# src/utils/schema.py
from typing import Dict, List, Any, Optional
from langchain_core.pydantic_v1 import BaseModel

class PatientInputSchema(BaseModel):
    """Schema for the input from WhatsApp to the Patient Agent."""
    user_id: str
    message_type: str = "text"  # "text", "voice", "image"
    message_content: str
    timestamp: str
    previous_context: Optional[Dict[str, Any]] = None

class PatientOutputSchema(BaseModel):
    """Schema for the output from Patient Agent to WhatsApp."""
    user_id: str
    response_type: str = "text"  # "text", "options", "appointment_confirmation"
    message: str
    suggested_actions: Optional[List[Dict[str, str]]] = None
    appointment_details: Optional[Dict[str, Any]] = None
    requires_further_input: bool = False

class DoctorInputSchema(BaseModel):
    """Schema for the input from Doctor Dashboard to the Doctor Agent."""
    doctor_id: str
    query_type: str  # "schedule", "patient", "appointment", "availability"
    query_content: str
    timestamp: str

class DoctorOutputSchema(BaseModel):
    """Schema for the output from Doctor Agent to Doctor Dashboard."""
    doctor_id: str
    response_type: str  # "schedule", "patient_info", "confirmation"
    message: str
    data: Optional[Dict[str, Any]] = None
    requires_action: bool = False
    suggested_actions: Optional[List[Dict[str, str]]] = None