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
from AI.tools.doctor_tools import (
    GetDoctorScheduleTool,
    UpdateAvailabilityTool,
    GetPatientHistoryTool,
    AddAppointmentNotesTool
)

class DoctorAgent:
    """AI agent that helps doctors manage their schedule and patient interactions"""
    
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
            GetDoctorScheduleTool(),
            UpdateAvailabilityTool(),
            GetPatientHistoryTool(),
            AddAppointmentNotesTool(),
        ]
    
    def _create_agent(self):
        """Create the LangChain agent with the necessary configuration"""
        # System message that defines the agent's behavior
        system_message = SystemMessage(content="""You are an AI assistant for doctors. 
        You help doctors manage their schedules, view patient information, and add notes to appointments. 
        Be professional, concise, and respect medical ethics and privacy guidelines.
        
        For schedule management:
        1. Show upcoming appointments clearly organized by day/time
        2. Help update availability windows
        3. Provide relevant patient information for each appointment
        
        For patient information:
        1. Summarize relevant medical history
        2. Highlight recent symptoms and concerns
        3. Note any recurring issues or patterns
        
        For appointment notes:
        1. Help structure notes in a standard medical format
        2. Suggest relevant follow-up actions when appropriate
        3. Flag any potential concerns based on patient history""")
        
        # TODO: In a real implementation, this would be a LangChain agent with tools
        # For now, we'll use a placeholder that will be replaced later
        agent = "placeholder"
        
        return agent
    
    def process_request(self, doctor_id, request_text):
        """Process a request from a doctor"""
        # TODO: In a real implementation, this would use the LangChain agent
        # For now, we'll use a simple conditional response
        
        # Classify intent (in a real implementation, this would be done by the LLM)
        intent = self._classify_intent(request_text)
        
        if "appointments" in request_text.lower() and any(word in request_text.lower() for word in ["today", "tomorrow", "schedule"]):
            return "Here is your schedule for today: [Schedule would be displayed here]"
        
        elif "availability" in request_text.lower() and "update" in request_text.lower():
            return "I'll help you update your availability. What days and times would you like to set as available?"
        
        elif "patient" in request_text.lower() and "history" in request_text.lower():
            return "Here is the patient history for your next appointment: [Patient history would be displayed here]"
        
        else:
            return "How can I assist you with your schedule or patient information today?"
    
    def _classify_intent(self, request_text):
        """Classify the intent of the doctor's request"""
        # In a real implementation, this would use the LLM to classify intent
        # For now, we'll use a simple keyword-based approach
        
        request_lower = request_text.lower()
        
        if any(word in request_lower for word in ["schedule", "appointments", "calendar"]):
            return "VIEW_SCHEDULE"
        
        elif any(word in request_lower for word in ["availability", "available", "times"]):
            return "UPDATE_AVAILABILITY"
        
        elif any(word in request_lower for word in ["patient", "history", "record"]):
            return "VIEW_PATIENT_HISTORY"
        
        elif any(word in request_lower for word in ["notes", "add notes", "update notes"]):
            return "ADD_NOTES"
        
        else:
            return "GENERAL_INQUIRY"
