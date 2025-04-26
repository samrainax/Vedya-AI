from langchain.agents import Agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import json
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import project-specific modules
from AI.tools.appointment_tools import (
    FindDoctorsTool,
    BookAppointmentTool,
    RescheduleAppointmentTool,
    CancelAppointmentTool,
    GetPatientAppointmentsTool
)
from AI.tools.patient_tools import (
    ExtractSymptomsTool, 
    GetPatientProfileTool,
    UpdatePatientProfileTool
)

class PatientAgent:
    """AI agent that handles patient interactions via WhatsApp"""
    
    def __init__(self, llm):
        self.llm = llm
        self.memory = ConversationBufferMemory()
        self.tools = self._setup_tools()
        self.agent = self._create_agent()
        
    def _setup_tools(self):
        """Set up the tools available to the agent"""
        # In a real implementation, these tools would be initialized with database access
        # Here we're just showing the structure
        return [
            ExtractSymptomsTool(),
            GetPatientProfileTool(),
            UpdatePatientProfileTool(),
            FindDoctorsTool(),
            BookAppointmentTool(),
            RescheduleAppointmentTool(),
            CancelAppointmentTool(),
            GetPatientAppointmentsTool(),
        ]
    
    def _create_agent(self):
        """Create the LangChain agent with the necessary configuration"""
        # System message that defines the agent's behavior
        system_message = SystemMessage(content="""You are a helpful medical assistant on WhatsApp. 
        You help patients book appointments with doctors, reschedule or cancel appointments, 
        and answer basic medical questions. Always be empathetic and professional.
        
        When discussing symptoms:
        1. Ask clarifying questions to understand the severity
        2. Never diagnose conditions - your role is to connect patients with doctors
        3. Express appropriate concern for serious symptoms
        4. Gather relevant information about duration, intensity, and context
        
        For appointment booking:
        1. Confirm patient identity
        2. Collect symptoms and reason for visit
        3. Help find appropriate specialists
        4. Offer available time slots
        5. Confirm appointment details before booking
        
        Always prioritize patient privacy and comply with healthcare regulations.""")
        
        # TODO: In a real implementation, this would be a LangChain agent with tools
        # For now, we'll use a placeholder that will be replaced later
        agent = "placeholder"
        
        return agent
    
    def process_message(self, patient_id, message_text):
        """Process an incoming message from a patient"""
        # TODO: In a real implementation, this would use the LangChain agent
        # For now, we'll use a simple conditional response
        
        # Classify intent (in a real implementation, this would be done by the LLM)
        intent = self._classify_intent(message_text)
        
        if "appointment" in message_text.lower() and "book" in message_text.lower():
            return "I'd be happy to help you book an appointment. What symptoms are you experiencing?"
        
        elif "reschedule" in message_text.lower():
            return "I can help you reschedule your appointment. Which appointment would you like to change?"
        
        elif "cancel" in message_text.lower():
            return "I can help you cancel your appointment. Which appointment would you like to cancel?"
        
        elif any(symptom in message_text.lower() for symptom in ["pain", "fever", "headache", "cough"]):
            return "I understand you're not feeling well. Could you tell me more about your symptoms and how long you've been experiencing them?"
        
        else:
            return "Thank you for your message. How can I assist you with your healthcare needs today?"
    
    def _classify_intent(self, message_text):
        """Classify the intent of the patient's message"""
        # In a real implementation, this would use the LLM to classify intent
        # For now, we'll use a simple keyword-based approach
        
        message_lower = message_text.lower()
        
        if any(word in message_lower for word in ["book", "schedule", "appointment", "see doctor"]):
            return "NEW_APPOINTMENT"
        
        elif any(word in message_lower for word in ["reschedule", "change appointment", "different time"]):
            return "RESCHEDULE"
        
        elif any(word in message_lower for word in ["cancel", "delete appointment"]):
            return "CANCEL_APPOINTMENT"
        
        elif any(word in message_lower for word in ["symptoms", "pain", "feeling", "sick"]):
            return "DESCRIBE_SYMPTOMS"
        
        else:
            return "GENERAL_INQUIRY"
