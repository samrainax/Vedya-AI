import sys
import json
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import enum
from pydantic import BaseModel, Field

# Add the src directory to the path so we can import from it
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.append(str(src_path))

from services.dummy_services import DummyServices
from groq_llama_helper import groq_llama_invoke

# Initialize dummy services
services = DummyServices()

# Define conversation stages to track progress
class ConversationStage(str, enum.Enum):
    INITIAL_GREETING = "initial_greeting"
    GATHERING_INFORMATION = "gathering_information"
    SUGGESTING_SPECIALTY = "suggesting_specialty" 
    RECOMMENDING_DOCTORS = "recommending_doctors"
    BOOKING_APPOINTMENT = "booking_appointment"
    CONFIRMATION = "confirmation"
    COMPLETED = "completed"

# State class for the patient agent
class PatientAgentState(BaseModel):
    """State for the Patient Agent."""
    messages: List[Dict[str, str]] = Field(default_factory=list)
    user_id: str
    current_stage: ConversationStage = ConversationStage.INITIAL_GREETING
    user_info: Dict[str, Any] = Field(default_factory=dict)
    health_issue: Dict[str, Any] = Field(default_factory=dict)
    specialty_recommendation: Optional[List[str]] = None
    selected_specialty: Optional[str] = None
    doctor_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    selected_doctor: Optional[Dict[str, Any]] = None
    appointment_details: Optional[Dict[str, Any]] = None
    conversation_complete: bool = False
    
    # For tracking extracted information
    extracted_info: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        arbitrary_types_allowed = True

# Schema definitions for input/output
class PatientInputSchema(BaseModel):
    """Schema for the input to the Patient Agent."""
    user_id: str
    message_type: str = "text"  # "text", "voice", "image"
    message_content: str
    timestamp: str
    previous_context: Optional[Dict[str, Any]] = None

class PatientOutputSchema(BaseModel):
    """Schema for the output from Patient Agent."""
    user_id: str
    response_type: str = "text"  # "text", "options", "appointment_confirmation"
    message: str
    suggested_actions: Optional[List[Dict[str, str]]] = None
    appointment_details: Optional[Dict[str, Any]] = None
    requires_further_input: bool = False
    current_stage: str = ConversationStage.INITIAL_GREETING

# Tool definitions
class Tools:
    @staticmethod
    def retrieve_user_context(state: PatientAgentState) -> PatientAgentState:
        """Retrieve user context including previous conversations and medical history."""
        print(f"Retrieving context for user: {state.user_id}")
        
        # Here we would normally fetch from a database - using dummy service for now
        user_profile = services.patient_profile_service()
        
        if user_profile:
            state.user_info = user_profile
            
            # Check if we have an incomplete conversation
            if state.previous_context and "current_stage" in state.previous_context:
                prev_stage = state.previous_context["current_stage"]
                # Convert string to enum if needed
                if isinstance(prev_stage, str):
                    try:
                        state.current_stage = ConversationStage(prev_stage)
                    except ValueError:
                        # If invalid stage, start fresh
                        state.current_stage = ConversationStage.INITIAL_GREETING
                
                # Restore other context if available
                if "health_issue" in state.previous_context:
                    state.health_issue = state.previous_context["health_issue"]
                if "specialty_recommendation" in state.previous_context:
                    state.specialty_recommendation = state.previous_context["specialty_recommendation"]
                if "selected_specialty" in state.previous_context:
                    state.selected_specialty = state.previous_context["selected_specialty"]
                if "doctor_recommendations" in state.previous_context:
                    state.doctor_recommendations = state.previous_context["doctor_recommendations"]
                if "extracted_info" in state.previous_context:
                    state.extracted_info = state.previous_context["extracted_info"]
        
        return state
    
    @staticmethod
    def extract_health_information(state: PatientAgentState) -> PatientAgentState:
        """Extract health information from user messages using LLM."""
        print("Extracting health information from conversation")
        
        # Prepare prompt for LLM to extract information
        system_prompt = """
        You are an AI assistant for a healthcare platform. Extract all relevant health information 
        from the patient's messages. Focus on:
        
        1. Symptoms and health concerns described
        2. Duration of symptoms
        3. Severity of symptoms
        4. Any relevant medical history mentioned
        5. Any date/time preferences for appointments mentioned
        6. Any doctor preferences mentioned
        
        Return the information as a JSON object with these fields where information is available.
        If certain information isn't mentioned, exclude those fields.
        """
        
        # Convert state messages to format needed for LLM
        prompt_messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # Add conversation history
        for msg in state.messages:
            prompt_messages.append(msg)
        
        # Call LLM to extract information
        response = groq_llama_invoke(prompt_messages)
        
        # Parse the extracted information
        try:
            # Find JSON in response (it might be embedded in explanation text)
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                extracted_info = json.loads(json_str)
                state.extracted_info.update(extracted_info)
                print(f"Successfully extracted info: {extracted_info}")
                
                # Update health issue with extracted info
                if "symptoms" in extracted_info:
                    state.health_issue["symptoms"] = extracted_info["symptoms"]
                if "duration" in extracted_info:
                    state.health_issue["duration"] = extracted_info["duration"]
                if "severity" in extracted_info:
                    state.health_issue["severity"] = extracted_info["severity"]
            else:
                print("No JSON object found in response")
        except Exception as e:
            print(f"Failed to parse JSON: {e}")
        
        return state
    
    @staticmethod
    def recommend_specialty(state: PatientAgentState) -> PatientAgentState:
        """Recommend medical specialties based on extracted health information using LLM."""
        print("Recommending medical specialties based on health info")
        
        # Prepare the prompt for specialty recommendation
        system_prompt = """
        You are an AI assistant specializing in healthcare triage. Based on the patient's symptoms 
        and health information, recommend the most appropriate medical specialties they should consult.
        
        Health information:
        {health_info}
        
        Patient history:
        {patient_history}
        
        Return a JSON object with:
        1. A list of recommended specialties in order of relevance
        2. A brief explanation for each recommendation 
        3. An urgency assessment (low, medium, high)
        """
        
        # Format health info for prompt
        health_info_str = json.dumps(state.health_issue)
        patient_history_str = json.dumps(state.user_info.get("medical_history", "No history available"))
        
        prompt_messages = [
            {"role": "system", "content": system_prompt.format(
                health_info=health_info_str, 
                patient_history=patient_history_str
            )},
        ]
        
        # Call LLM for specialty recommendation
        response = groq_llama_invoke(prompt_messages)
        
        # Parse recommendation
        try:
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                recommendation = json.loads(json_str)
                
                if "specialties" in recommendation:
                    state.specialty_recommendation = recommendation["specialties"]
                    
                    # If there's an "urgency" field, save it
                    if "urgency" in recommendation:
                        state.health_issue["urgency"] = recommendation["urgency"]
                        
                    # Save explanations if available
                    if "explanations" in recommendation:
                        state.health_issue["specialty_explanations"] = recommendation["explanations"]
                
                print(f"Recommended specialties: {state.specialty_recommendation}")
            else:
                # Fallback if JSON parsing fails
                state.specialty_recommendation = ["General Medicine"]
                print("No proper JSON found, defaulting to General Medicine")
        except Exception as e:
            print(f"Error parsing specialty recommendation: {e}")
            state.specialty_recommendation = ["General Medicine"]
        
        return state
    
    @staticmethod
    def fetch_doctor_recommendations(state: PatientAgentState) -> PatientAgentState:
        """Fetch doctor recommendations based on specialty and location."""
        print(f"Fetching doctor recommendations for specialty: {state.selected_specialty}")
        
        if not state.selected_specialty and state.specialty_recommendation:
            # Use the first recommendation if no selection made
            state.selected_specialty = state.specialty_recommendation[0]
        
        # Get patient location
        patient_location = state.user_info.get("location", {"lat": 0, "lng": 0})
        
        # Determine urgency level
        urgency_level = state.health_issue.get("urgency", "normal")
        
        # Call doctor matching service
        doctor_results = services.doctor_matching_service(
            specialty=state.selected_specialty,
            patient_location=patient_location,
            urgency_level=urgency_level
        )
        
        if "doctors" in doctor_results:
            state.doctor_recommendations = doctor_results["doctors"]
            print(f"Found {len(state.doctor_recommendations)} matching doctors")
        else:
            print("No doctors found for the selected specialty")
            state.doctor_recommendations = []
        
        return state
    
    @staticmethod
    def filter_doctor_recommendations(state: PatientAgentState) -> PatientAgentState:
        """Filter doctor recommendations based on patient preferences using LLM."""
        
        # Only proceed if we have doctors and messages to analyze
        if not state.doctor_recommendations or len(state.messages) < 2:
            return state
        
        print("Filtering doctor recommendations based on user preferences")
        
        # Extract user preferences using LLM
        system_prompt = """
        You are an AI assistant for a healthcare platform. Analyze the patient's messages 
        to identify any preferences they've expressed about doctor selection, such as:
        
        1. Gender preference
        2. Experience level preference
        3. Location preference (e.g., "close to home")
        4. Availability preference (e.g., "available this week")
        5. Hospital/facility preference
        
        Return a JSON object with the identified preferences.
        """
        
        # Create messages for LLM
        prompt_messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # Add only user messages
        for msg in state.messages:
            if msg["role"] == "user":
                prompt_messages.append(msg)
        
        # Call LLM to extract preferences
        response = groq_llama_invoke(prompt_messages)
        
        # Try to extract preferences
        try:
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                preferences = json.loads(json_str)
                
                # Simple filtering based on preferences - in a real implementation,
                # this would be more sophisticated
                filtered_doctors = state.doctor_recommendations.copy()
                
                # Example: Gender preference filter
                if "gender" in preferences and filtered_doctors:
                    gender_pref = preferences["gender"].lower()
                    if gender_pref in ["male", "female"]:
                        filtered_doctors = [d for d in filtered_doctors if d.get("gender", "").lower() == gender_pref]
                
                # Keep original recommendations if filtering removed all options
                if filtered_doctors:
                    state.doctor_recommendations = filtered_doctors
                    print(f"Filtered to {len(filtered_doctors)} doctors based on preferences")
                    
                # Save preferences for reference
                state.extracted_info["doctor_preferences"] = preferences
                
            else:
                print("No preference JSON found in response")
        except Exception as e:
            print(f"Error parsing doctor preferences: {e}")
        
        return state
    
    @staticmethod
    def book_appointment(state: PatientAgentState) -> PatientAgentState:
        """Book an appointment with the selected doctor."""
        print("Booking appointment")
        
        if not state.selected_doctor:
            print("No doctor selected, cannot book appointment")
            return state
        
        # Extract appointment details from extracted info
        date = state.extracted_info.get("appointment_date")
        time = state.extracted_info.get("appointment_time")
        
        # If date or time is missing, check available slots of selected doctor
        if not date or not time:
            # Use the first available slot if available
            if "available_slots" in state.selected_doctor and state.selected_doctor["available_slots"]:
                first_day = state.selected_doctor["available_slots"][0]
                date = first_day["date"]
                if first_day["slots"]:
                    time = first_day["slots"][0]
        
        # Book the appointment
        if date and time:
            patient_id = state.user_id  # In a real app, this would be a valid patient ID
            doctor_id = state.selected_doctor["doctor_id"]
            
            appointment_result = services.appointment_booking_service(
                action="book",
                patient_id=patient_id,
                doctor_id=doctor_id,
                date=date,
                time=time
            )
            
            if appointment_result["status"] == "success":
                state.appointment_details = appointment_result
                print(f"Appointment booked successfully: {date} at {time}")
            else:
                print(f"Failed to book appointment: {appointment_result.get('message')}")
        else:
            print("Missing date or time for appointment")
        
        return state
    
    @staticmethod
    def extract_appointment_details(state: PatientAgentState) -> PatientAgentState:
        """Extract appointment details like preferred date/time from user messages."""
        print("Extracting appointment details")
        
        system_prompt = """
        You are an AI assistant for a healthcare appointment scheduler. Extract any appointment 
        date and time preferences from the patient's messages. Look for:
        
        1. Specific dates (e.g., "next Monday", "May 5th", "tomorrow")
        2. Time preferences (e.g., "morning", "afternoon", "evening", "at 2pm")
        3. Day preferences (e.g., "weekdays only", "weekend")
        
        Convert relative dates to actual dates based on today's date: {today_date}
        
        Return a JSON object with "appointment_date" and "appointment_time" fields if found.
        Use ISO format for dates (YYYY-MM-DD) and 24-hour format for times (HH:MM).
        """
        
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        # Create messages for LLM
        prompt_messages = [
            {"role": "system", "content": system_prompt.format(today_date=today_date)},
        ]
        
        # Add conversation history
        for msg in state.messages:
            if msg["role"] == "user":
                prompt_messages.append(msg)
        
        # Call LLM to extract appointment details
        response = groq_llama_invoke(prompt_messages)
        
        # Try to extract appointment details
        try:
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                appointment_details = json.loads(json_str)
                
                # Update state with extracted details
                if "appointment_date" in appointment_details:
                    state.extracted_info["appointment_date"] = appointment_details["appointment_date"]
                if "appointment_time" in appointment_details:
                    state.extracted_info["appointment_time"] = appointment_details["appointment_time"]
                    
                print(f"Extracted appointment details: {appointment_details}")
            else:
                print("No appointment details found in response")
        except Exception as e:
            print(f"Error parsing appointment details: {e}")
        
        return state
    
    @staticmethod
    def send_confirmation(state: PatientAgentState) -> PatientAgentState:
        """Send confirmation notification to the patient."""
        if not state.appointment_details:
            print("No appointment details available for confirmation")
            return state
        
        print("Sending appointment confirmation")
        
        # In a real implementation, this would send an actual notification
        notification_result = services.notification_service(
            recipient_type="patient",
            recipient_id=state.user_id,
            notification_type="appointment_confirmation",
            content={
                "appointment_id": state.appointment_details["appointment_id"],
                "doctor": state.appointment_details["doctor"],
                "date": state.appointment_details["date"],
                "time": state.appointment_details["time"],
                "location": state.appointment_details["hospital"]
            }
        )
        
        print(f"Notification sent: {notification_result}")
        
        # Mark conversation as complete
        state.conversation_complete = True
        state.current_stage = ConversationStage.COMPLETED
        
        return state

# LLM-based agent functions
def identify_conversation_intent(state: PatientAgentState) -> PatientAgentState:
    """Identify the intent and next steps in the conversation flow using LLM."""
    print("Identifying conversation intent and next steps")
    
    system_prompt = """
    You are an AI assistant for a healthcare platform helping patients connect with doctors.
    Based on the conversation so far, determine what stage we're at and what should happen next.
    
    Current conversation stage: {current_stage}
    User information: {user_info}
    Health issue information: {health_issue}
    Extracted information: {extracted_info}
    Specialty recommendations: {specialty_recommendation}
    Selected specialty: {selected_specialty}
    Doctor recommendations available: {has_doctor_recommendations}
    Selected doctor: {selected_doctor}
    Appointment details: {appointment_details}
    
    Return a JSON object with:
    1. "next_stage": The appropriate next stage in the conversation
       (GATHERING_INFORMATION, SUGGESTING_SPECIALTY, RECOMMENDING_DOCTORS, BOOKING_APPOINTMENT, CONFIRMATION, COMPLETED)
    2. "reasoning": Brief explanation of why this stage is appropriate
    """
    
    # Format state info for prompt
    state_info = {
        "current_stage": state.current_stage,
        "user_info": "Available" if state.user_info else "Not available",
        "health_issue": json.dumps(state.health_issue) if state.health_issue else "Not available",
        "extracted_info": json.dumps(state.extracted_info) if state.extracted_info else "Not available",
        "specialty_recommendation": state.specialty_recommendation,
        "selected_specialty": state.selected_specialty or "None",
        "has_doctor_recommendations": "Yes" if state.doctor_recommendations else "No",
        "selected_doctor": state.selected_doctor["name"] if state.selected_doctor else "None",
        "appointment_details": "Available" if state.appointment_details else "Not available"
    }
    
    # Create prompt messages
    prompt_messages = [
        {"role": "system", "content": system_prompt.format(**state_info)},
    ]
    
    # Add recent conversation history (last 3 messages)
    for msg in state.messages[-3:]:
        prompt_messages.append(msg)
    
    # Call LLM to determine next stage
    response = groq_llama_invoke(prompt_messages)
    
    # Parse the response
    try:
        json_start = response.find('{')
        json_end = response.rfind('}')
        
        if json_start >= 0 and json_end >= 0:
            json_str = response[json_start:json_end+1]
            stage_decision = json.loads(json_str)
            
            if "next_stage" in stage_decision:
                next_stage = stage_decision["next_stage"]
                print(f"LLM suggests next stage: {next_stage}")
                
                # Update the state with the suggested stage
                try:
                    state.current_stage = ConversationStage(next_stage)
                except ValueError:
                    print(f"Invalid stage suggestion: {next_stage}, keeping current stage")
        else:
            print("No valid JSON found in response")
    except Exception as e:
        print(f"Error parsing stage decision: {e}")
    
    return state

def generate_response(state: PatientAgentState) -> PatientAgentState:
    """Generate conversational response based on current state."""
    print(f"Generating response for stage: {state.current_stage}")
    
    system_prompt = """
    You are an AI assistant for a healthcare platform helping rural patients connect with the right doctors.
    Your tone should be helpful, clear, and empathetic. Use simple language accessible to people with varying
    levels of healthcare literacy. Keep responses concise and focused.
    
    Current conversation stage: {current_stage}
    
    Based on the stage and available information, generate a helpful response to the patient.
    
    If in INITIAL_GREETING: Welcome them and ask about their health concern/what brought them here today.
    If in GATHERING_INFORMATION: Ask any questions needed to understand their health issue better.
    If in SUGGESTING_SPECIALTY: Explain the recommended medical specialty(ies) and ask if they'd like doctor recommendations.
    If in RECOMMENDING_DOCTORS: Present doctor options clearly and ask if they'd like to book an appointment.
    If in BOOKING_APPOINTMENT: Ask for/confirm appointment details (date/time preferences).
    If in CONFIRMATION: Confirm the appointment details and provide next steps.
    If in COMPLETED: Thank them for using the service and provide a helpful closing.
    
    Available information:
    User info: {user_info}
    Health issue details: {health_issue}
    Specialty recommendations: {specialty_recommendations}
    Doctor recommendations: {doctor_recommendations}
    Selected doctor: {selected_doctor}
    Appointment details: {appointment_details}
    """
    
    # Format state info for prompt
    state_info = {
        "current_stage": state.current_stage,
        "user_info": json.dumps(state.user_info, indent=2) if state.user_info else "Not available",
        "health_issue": json.dumps(state.health_issue, indent=2) if state.health_issue else "Not available",
        "specialty_recommendations": json.dumps(state.specialty_recommendation, indent=2) if state.specialty_recommendation else "Not available",
        "doctor_recommendations": f"{len(state.doctor_recommendations)} doctors available" if state.doctor_recommendations else "None",
        "selected_doctor": json.dumps(state.selected_doctor, indent=2) if state.selected_doctor else "None",
        "appointment_details": json.dumps(state.appointment_details, indent=2) if state.appointment_details else "None"
    }
    
    # Create prompt messages
    prompt_messages = [
        {"role": "system", "content": system_prompt.format(**state_info)},
    ]
    
    # Add conversation history (up to last 5 messages)
    for msg in state.messages[-5:]:
        prompt_messages.append(msg)
    
    # Call LLM for response generation
    response = groq_llama_invoke(prompt_messages)
    
    # Add the response to messages
    state.messages.append({
        "role": "assistant",
        "content": response
    })
    
    return state

def analyze_user_message(state: PatientAgentState, message_content: str) -> PatientAgentState:
    """Process a new user message and update the state."""
    print(f"Processing user message: {message_content}")
    
    # Add the message to the conversation history
    state.messages.append({
        "role": "user",
        "content": message_content
    })
    
    # If we're in specialty suggestion stage, check if user has selected a specialty
    if state.current_stage == ConversationStage.SUGGESTING_SPECIALTY and state.specialty_recommendation:
        system_prompt = """
        Analyze the user's message to determine if they've selected one of the recommended specialties
        or if they're asking for doctor recommendations. 
        
        Recommended specialties: {specialties}
        
        User message: {message}
        
        Return a JSON object with:
        - "selected_specialty": The specialty mentioned by the user, or null if none mentioned
        - "wants_recommendations": true if the user is asking for doctor recommendations, false otherwise
        """
        
        prompt_messages = [
            {"role": "system", "content": system_prompt.format(
                specialties=json.dumps(state.specialty_recommendation),
                message=message_content
            )},
        ]
        
        # Call LLM to analyze response
        response = groq_llama_invoke(prompt_messages)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                analysis = json.loads(json_str)
                
                if "selected_specialty" in analysis and analysis["selected_specialty"]:
                    state.selected_specialty = analysis["selected_specialty"]
                    print(f"User selected specialty: {state.selected_specialty}")
                
                if "wants_recommendations" in analysis and analysis["wants_recommendations"]:
                    # If user wants recommendations, move to next stage
                    state.current_stage = ConversationStage.RECOMMENDING_DOCTORS
                    print("User wants doctor recommendations, moving to RECOMMENDING_DOCTORS stage")
        except Exception as e:
            print(f"Error analyzing specialty selection: {e}")
    
    # If we're recommending doctors, check if user has selected one
    elif state.current_stage == ConversationStage.RECOMMENDING_DOCTORS and state.doctor_recommendations:
        system_prompt = """
        Analyze the user's message to determine if they've selected one of the recommended doctors
        or if they're asking for more information about doctors.
        
        Available doctors: {doctors}
        
        User message: {message}
        
        Return a JSON object with:
        - "selected_doctor_id": The ID of the doctor selected by the user, or null if none selected
        - "wants_booking": true if the user wants to book an appointment, false otherwise
        - "wants_more_options": true if the user is asking for more doctor options, false otherwise
        """
        
        # Prepare doctor info for prompt
        doctor_info = [
            {"id": doc["doctor_id"], "name": doc["name"], "specialty": doc["specialty"]}
            for doc in state.doctor_recommendations
        ]
        
        prompt_messages = [
            {"role": "system", "content": system_prompt.format(
                doctors=json.dumps(doctor_info),
                message=message_content
            )},
        ]
        
        # Call LLM to analyze response
        response = groq_llama_invoke(prompt_messages)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                analysis = json.loads(json_str)
                
                # Check if user selected a doctor
                if "selected_doctor_id" in analysis and analysis["selected_doctor_id"]:
                    doctor_id = analysis["selected_doctor_id"]
                    # Find the selected doctor in recommendations
                    for doc in state.doctor_recommendations:
                        if doc["doctor_id"] == doctor_id:
                            state.selected_doctor = doc
                            print(f"User selected doctor: {doc['name']}")
                            break
                
                # Check if user wants to book
                if "wants_booking" in analysis and analysis["wants_booking"]:
                    state.current_stage = ConversationStage.BOOKING_APPOINTMENT
                    print("User wants to book an appointment, moving to BOOKING_APPOINTMENT stage")
                
                # Check if user wants more options
                if "wants_more_options" in analysis and analysis["wants_more_options"]:
                    # Re-run doctor recommendations with filtering
                    state = Tools.filter_doctor_recommendations(state)
                    print("User wants more doctor options, refreshing recommendations")
        except Exception as e:
            print(f"Error analyzing doctor selection: {e}")
    
    return state

# Main flow handler
def process_message_and_execute_flow(state: PatientAgentState) -> PatientAgentState:
    """Process the current state and execute the appropriate workflow steps."""
    print(f"Current stage: {state.current_stage}")
    
    # Extract health information from conversation
    state = Tools.extract_health_information(state)
    
    # Identify the conversation intent and what stage we should be in
    state = identify_conversation_intent(state)
    
    # Execute stage-specific actions
    if state.current_stage == ConversationStage.GATHERING_INFORMATION:
        # No specific action needed - we've already extracted information
        pass
        
    elif state.current_stage == ConversationStage.SUGGESTING_SPECIALTY:
        # Recommend medical specialties if not done already
        if not state.specialty_recommendation:
            state = Tools.recommend_specialty(state)
    
    elif state.current_stage == ConversationStage.RECOMMENDING_DOCTORS:
        # If we have a specialty but no recommendations yet, fetch them
        if (state.selected_specialty or state.specialty_recommendation) and not state.doctor_recommendations:
            state = Tools.fetch_doctor_recommendations(state)
    
    elif state.current_stage == ConversationStage.BOOKING_APPOINTMENT:
        # Extract appointment details if available
        state = Tools.extract_appointment_details(state)
        
        # If we have a selected doctor and appointment details, book the appointment
        if state.selected_doctor and "appointment_date" in state.extracted_info and "appointment_time" in state.extracted_info:
            state = Tools.book_appointment(state)
            if state.appointment_details:
                state.current_stage = ConversationStage.CONFIRMATION
    
    elif state.current_stage == ConversationStage.CONFIRMATION:
        # Send confirmation if we have appointment details and haven't completed
        if state.appointment_details and not state.conversation_complete:
            state = Tools.send_confirmation(state)
    
    # Generate response to user
    state = generate_response(state)
    
    return state

# Complete PatientInputSchema and PatientOutputSchema classes
class PatientInputSchema(BaseModel):
    """Schema for the input to the Patient Agent."""
    user_id: str
    message_type: str = "text"  # "text", "voice", "image"
    message_content: str
    timestamp: str
    previous_context: Optional[Dict[str, Any]] = None

class PatientOutputSchema(BaseModel):
    """Schema for the output from Patient Agent."""
    user_id: str
    response_type: str = "text"  # "text", "options", "appointment_confirmation"
    message: str
    suggested_actions: Optional[List[Dict[str, str]]] = None
    appointment_details: Optional[Dict[str, Any]] = None
    requires_further_input: bool = False
    current_stage: str = ConversationStage.INITIAL_GREETING.value

# Main Patient Agent Class with Agentic Flow
class PatientAgent:
    """
    Patient Agent that handles the conversation flow with patients,
    helping them find appropriate doctors and book appointments.
    """
    
    def __init__(self):
        """Initialize the agent with required services and tools."""
        self.services = DummyServices()
        # Dictionary of tools that the agent can use
        self.tools = {
            "retrieve_user_context": self.retrieve_user_context,
            "extract_health_information": self.extract_health_information,
            "recommend_specialty": self.recommend_specialty,
            "fetch_doctor_recommendations": self.fetch_doctor_recommendations,
            "filter_doctor_recommendations": self.filter_doctor_recommendations,
            "extract_appointment_details": self.extract_appointment_details,
            "book_appointment": self.book_appointment,
            "send_confirmation": self.send_confirmation
        }
    
    def invoke(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for the agent."""
        # Parse input
        input_obj = PatientInputSchema(**input_data)
        
        # Initialize or retrieve state
        state = self._initialize_state(input_obj)
        
        # Process user message
        state = self._process_user_message(state, input_obj.message_content)
        
        # Execute the conversation flow
        state = self._execute_conversation_flow(state)
        
        # Generate response
        output = self._generate_output(state)
        
        return output.dict()
    
    def _initialize_state(self, input_obj: PatientInputSchema) -> PatientAgentState:
        """Initialize or retrieve the conversation state."""
        # Check if we have previous context
        if input_obj.previous_context:
            # Restore state from previous context
            state = PatientAgentState(
                user_id=input_obj.user_id,
                messages=input_obj.previous_context.get("messages", []),
                current_stage=ConversationStage(input_obj.previous_context.get("current_stage", ConversationStage.INITIAL_GREETING.value)),
                user_info=input_obj.previous_context.get("user_info", {}),
                health_issue=input_obj.previous_context.get("health_issue", {}),
                specialty_recommendation=input_obj.previous_context.get("specialty_recommendation"),
                selected_specialty=input_obj.previous_context.get("selected_specialty"),
                doctor_recommendations=input_obj.previous_context.get("doctor_recommendations", []),
                selected_doctor=input_obj.previous_context.get("selected_doctor"),
                appointment_details=input_obj.previous_context.get("appointment_details"),
                extracted_info=input_obj.previous_context.get("extracted_info", {})
            )
        else:
            # Initialize new state
            state = PatientAgentState(
                user_id=input_obj.user_id,
                current_stage=ConversationStage.INITIAL_GREETING
            )
            
            # Retrieve user context if available
            state = self.retrieve_user_context(state)
        
        return state
    
    def _process_user_message(self, state: PatientAgentState, message_content: str) -> PatientAgentState:
        """Process a new user message."""
        # Add message to conversation history
        state.messages.append({
            "role": "user",
            "content": message_content
        })
        
        return state
    
    def _execute_conversation_flow(self, state: PatientAgentState) -> PatientAgentState:
        """
        Execute the conversation flow based on agentic decision making.
        This is the core of the agent's intelligence.
        """
        # First, decide what tool to call next based on current conversation state
        next_tool = self._decide_next_tool(state)
        
        # Keep track of tools used for this turn to avoid infinite loops
        tools_used = set()
        
        # Execute tools until we've made sufficient progress or hit a max
        MAX_TOOL_CALLS = 5  # Safety limit
        while next_tool and len(tools_used) < MAX_TOOL_CALLS:
            print(f"Executing tool: {next_tool}")
            tools_used.add(next_tool)
            
            # Execute the tool
            if next_tool in self.tools:
                state = self.tools[next_tool](state)
            
            # Check if we need another tool
            next_tool = self._decide_next_tool(state, tools_used)
        
        # Generate response with LLM
        state = self._generate_response(state)
        
        return state
    
    def _decide_next_tool(self, state: PatientAgentState, tools_already_used: set = None) -> Optional[str]:
        """
        Use the LLM to decide what tool to use next based on the current state.
        This replaces explicit if-else logic with agentic decision making.
        """
        if tools_already_used is None:
            tools_already_used = set()
        
        # Create system prompt for tool selection
        system_prompt = """
        You are an AI assistant for a healthcare platform that helps patients connect with doctors.
        Based on the conversation state, determine what tool should be called next to progress the conversation.
        
        Current conversation stage: {current_stage}
        User information available: {has_user_info}
        Health issue information available: {has_health_info}
        Symptom analysis performed: {has_symptom_analysis}
        Specialty recommendations available: {has_specialty_recommendations}
        User selected specialty: {selected_specialty}
        Doctor recommendations available: {has_doctor_recommendations}
        User selected doctor: {has_selected_doctor}
        Appointment details available: {has_appointment_details}
        Appointment confirmation sent: {has_sent_confirmation}
        
        Available tools:
        - retrieve_user_context: Get user information and medical history
        - extract_health_information: Extract health concerns from conversation
        - recommend_specialty: Suggest medical specialties based on health issues
        - fetch_doctor_recommendations: Find doctors matching the specialty and location
        - filter_doctor_recommendations: Filter doctors based on user preferences
        - extract_appointment_details: Get appointment date/time preferences from conversation
        - book_appointment: Book an appointment with selected doctor
        - send_confirmation: Send appointment confirmation to user
        
        Already used tools in this conversation turn: {tools_used}
        
        Return only the name of the next tool to call, or "none" if no tool is needed right now.
        """
        
        # Format context for the prompt
        context = {
            "current_stage": state.current_stage.value,
            "has_user_info": bool(state.user_info),
            "has_health_info": bool(state.health_issue),
            "has_symptom_analysis": "symptoms" in state.health_issue,
            "has_specialty_recommendations": bool(state.specialty_recommendation),
            "selected_specialty": state.selected_specialty or "None",
            "has_doctor_recommendations": bool(state.doctor_recommendations),
            "has_selected_doctor": bool(state.selected_doctor),
            "has_appointment_details": bool(state.appointment_details),
            "has_sent_confirmation": state.conversation_complete,
            "tools_used": ", ".join(tools_already_used) or "None"
        }
        
        # Create messages for LLM
        messages = [
            {"role": "system", "content": system_prompt.format(**context)}
        ]
        
        # Call LLM to decide next tool
        response = groq_llama_invoke(messages)
        
        # Extract tool name from response
        tool_name = response.strip().lower()
        
        # Check if response is a valid tool and hasn't been used
        for valid_tool in self.tools.keys():
            if valid_tool in tool_name and valid_tool not in tools_already_used:
                return valid_tool
                
        if "none" in tool_name:
            return None
        
        # Default to None if no valid tool found
        return None
    
    def _generate_response(self, state: PatientAgentState) -> PatientAgentState:
        """Generate a conversational response based on current state."""
        system_prompt = """
        You are an AI assistant for a healthcare platform helping patients connect with doctors, especially in rural areas.
        Your tone should be helpful, clear, and empathetic. Avoid medical jargon unless explaining a concept.
        
        Current conversation stage: {current_stage}
        
        Based on the stage and available information, generate a natural, helpful response to the patient:
        
        - INITIAL_GREETING: Welcome them warmly and ask what health concern brought them here.
        - GATHERING_INFORMATION: Ask questions to better understand their health issue and needs.
        - SUGGESTING_SPECIALTY: Explain the recommended medical specialty(ies) and ask if they want doctor recommendations.
        - RECOMMENDING_DOCTORS: Present doctor options clearly, highlighting relevant factors (distance, availability).
        - BOOKING_APPOINTMENT: Help confirm appointment details (date/time).
        - CONFIRMATION: Confirm booking details and provide next steps.
        - COMPLETED: Thank them and provide helpful closing information.
        
        User information: {user_info}
        Health issue details: {health_issue}
        Specialty recommendations: {specialty_recommendations}
        Selected specialty: {selected_specialty}
        Doctor recommendations: {doctor_recommendations}
        Selected doctor: {selected_doctor}
        Appointment details: {appointment_details}
        Extracted appointment preferences: {appointment_preferences}
        
        Keep your response conversational and friendly, but concise.
        """
        
        # Format state info for prompt
        state_info = {
            "current_stage": state.current_stage.value,
            "user_info": json.dumps(state.user_info, indent=2) if state.user_info else "Not available",
            "health_issue": json.dumps(state.health_issue, indent=2) if state.health_issue else "Not available",
            "specialty_recommendations": json.dumps(state.specialty_recommendation, indent=2) if state.specialty_recommendation else "Not available",
            "selected_specialty": state.selected_specialty or "Not selected",
            "doctor_recommendations": f"{len(state.doctor_recommendations)} doctors available" if state.doctor_recommendations else "None",
            "selected_doctor": json.dumps(state.selected_doctor, indent=2) if state.selected_doctor else "None",
            "appointment_details": json.dumps(state.appointment_details, indent=2) if state.appointment_details else "None",
            "appointment_preferences": json.dumps({k: v for k, v in state.extracted_info.items() if k.startswith("appointment_")}, indent=2)
        }
        
        # Create messages for LLM
        messages = [
            {"role": "system", "content": system_prompt.format(**state_info)}
        ]
        
        # Add conversation history (last 5 messages)
        recent_messages = state.messages[-5:] if len(state.messages) > 5 else state.messages
        messages.extend(recent_messages)
        
        # Call LLM for response generation
        response = groq_llama_invoke(messages)
        
        # Add the response to state messages
        state.messages.append({
            "role": "assistant",
            "content": response
        })
        
        return state
    
    def _generate_output(self, state: PatientAgentState) -> PatientOutputSchema:
        """Generate the final output from the current state."""
        # Extract the last assistant message
        last_message = next((msg["content"] for msg in reversed(state.messages) 
                            if msg["role"] == "assistant"), "")
        
        # Create suggested actions based on current stage
        suggested_actions = None
        if state.current_stage == ConversationStage.SUGGESTING_SPECIALTY and state.specialty_recommendation:
            suggested_actions = [
                {"action": "select_specialty", "text": f"Select {specialty}"} 
                for specialty in state.specialty_recommendation[:3]
            ]
            suggested_actions.append({"action": "request_doctors", "text": "Find doctors"})
        
        elif state.current_stage == ConversationStage.RECOMMENDING_DOCTORS and state.doctor_recommendations:
            suggested_actions = [
                {"action": "select_doctor", "doctor_id": doc["doctor_id"], 
                 "text": f"Select Dr. {doc['name']}"}
                for doc in state.doctor_recommendations[:3]
            ]
        
        # Create output
        output = PatientOutputSchema(
            user_id=state.user_id,
            response_type="appointment_confirmation" if state.appointment_details else "text",
            message=last_message,
            suggested_actions=suggested_actions,
            appointment_details=state.appointment_details,
            requires_further_input=not state.conversation_complete,
            current_stage=state.current_stage.value
        )
        
        return output
    
    # Tool implementations
    def retrieve_user_context(self, state: PatientAgentState) -> PatientAgentState:
        """Retrieve user context including previous conversations and medical history."""
        print(f"Retrieving context for user: {state.user_id}")
        
        # Fetch user profile from service
        user_profile = self.services.patient_profile_service(patient_id=state.user_id)
        
        if user_profile:
            state.user_info = user_profile
        
        return state
    
    def extract_health_information(self, state: PatientAgentState) -> PatientAgentState:
        """Extract health information from user messages."""
        print("Extracting health information from conversation")
        
        # Prepare prompt for LLM to extract information
        system_prompt = """
        You are an AI assistant for a healthcare platform. Extract all relevant health information 
        from the patient's messages. Focus on:
        
        1. Symptoms and health concerns described
        2. Duration of symptoms
        3. Severity of symptoms
        4. Any relevant medical history mentioned
        5. Any date/time preferences for appointments
        6. Any doctor preferences mentioned
        
        Return the information as a JSON object with these fields where information is available.
        If certain information isn't mentioned, exclude those fields.
        """
        
        # Create messages for LLM
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add user messages only
        for msg in state.messages:
            if msg["role"] == "user":
                messages.append(msg)
        
        # Call LLM to extract information
        response = groq_llama_invoke(messages)
        
        # Parse the extracted information
        try:
            # Find JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                extracted_info = json.loads(json_str)
                state.extracted_info.update(extracted_info)
                
                # Update health issue with extracted info
                if "symptoms" in extracted_info:
                    state.health_issue["symptoms"] = extracted_info["symptoms"]
                if "duration" in extracted_info:
                    state.health_issue["duration"] = extracted_info["duration"]
                if "severity" in extracted_info:
                    state.health_issue["severity"] = extracted_info["severity"]
                
                print(f"Extracted health info: {extracted_info}")
        except Exception as e:
            print(f"Failed to parse health information: {e}")
        
        return state
    
    def recommend_specialty(self, state: PatientAgentState) -> PatientAgentState:
        """Recommend medical specialties based on extracted health information."""
        print("Recommending medical specialties")
        
        # Prepare the prompt for specialty recommendation
        system_prompt = """
        You are an AI assistant specializing in healthcare triage. Based on the patient's symptoms 
        and health information, recommend the most appropriate medical specialties they should consult.
        
        Health information: {health_info}
        Patient history: {patient_history}
        
        Return a JSON object with:
        1. "specialties": A list of recommended specialties in order of relevance
        2. "explanations": A brief explanation for each recommendation 
        3. "urgency": An urgency assessment (low, medium, high)
        """
        
        # Format health info for prompt
        health_info_str = json.dumps(state.health_issue)
        patient_history_str = json.dumps(state.user_info.get("medical_history", []))
        
        # Create messages for LLM
        messages = [
            {"role": "system", "content": system_prompt.format(
                health_info=health_info_str, 
                patient_history=patient_history_str
            )}
        ]
        
        # Call LLM for specialty recommendation
        response = groq_llama_invoke(messages)
        
        # Parse recommendation
        try:
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                recommendation = json.loads(json_str)
                
                if "specialties" in recommendation:
                    state.specialty_recommendation = recommendation["specialties"]
                    
                    # Save explanations and urgency if available
                    if "explanations" in recommendation:
                        state.health_issue["specialty_explanations"] = recommendation["explanations"]
                    if "urgency" in recommendation:
                        state.health_issue["urgency"] = recommendation["urgency"]
                
                print(f"Recommended specialties: {state.specialty_recommendation}")
            else:
                # Fallback
                state.specialty_recommendation = ["General Medicine"]
                print("No proper JSON found, defaulting to General Medicine")
        except Exception as e:
            print(f"Error parsing specialty recommendation: {e}")
            state.specialty_recommendation = ["General Medicine"]
        
        # Update stage if needed
        if state.current_stage == ConversationStage.GATHERING_INFORMATION:
            state.current_stage = ConversationStage.SUGGESTING_SPECIALTY
        
        return state
    
    def fetch_doctor_recommendations(self, state: PatientAgentState) -> PatientAgentState:
        """Fetch doctor recommendations based on specialty and location."""
        print(f"Fetching doctor recommendations for specialty: {state.selected_specialty}")
        
        # Use first recommendation if no selection made
        if not state.selected_specialty and state.specialty_recommendation:
            state.selected_specialty = state.specialty_recommendation[0]
        
        if not state.selected_specialty:
            print("No specialty selected, cannot fetch doctor recommendations")
            return state
        
        # Get patient location
        patient_location = state.user_info.get("location", {"lat": 0, "lng": 0})
        
        # Determine urgency level
        urgency_level = state.health_issue.get("urgency", "normal")
        
        # Call doctor matching service
        doctor_results = self.services.doctor_matching_service(
            specialty=state.selected_specialty,
            patient_location=patient_location,
            urgency_level=urgency_level
        )
        
        if "doctors" in doctor_results:
            state.doctor_recommendations = doctor_results["doctors"]
            print(f"Found {len(state.doctor_recommendations)} matching doctors")
        else:
            print("No doctors found for the selected specialty")
            state.doctor_recommendations = []
        
        # Update stage if needed
        if state.current_stage == ConversationStage.SUGGESTING_SPECIALTY:
            state.current_stage = ConversationStage.RECOMMENDING_DOCTORS
        
        return state
    
    def filter_doctor_recommendations(self, state: PatientAgentState) -> PatientAgentState:
        """Filter doctor recommendations based on patient preferences."""
        if not state.doctor_recommendations:
            return state
        
        print("Filtering doctor recommendations based on user preferences")
        
        # Extract user preferences using LLM
        system_prompt = """
        You are an AI assistant for a healthcare platform. Analyze the patient's messages 
        to identify any preferences they've expressed about doctor selection, such as:
        
        1. Gender preference
        2. Experience level preference
        3. Location preference (e.g., "close to home")
        4. Availability preference (e.g., "available this week")
        5. Hospital/facility preference
        
        Return a JSON object with the identified preferences.
        """
        
        # Create messages for LLM
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add only user messages
        for msg in state.messages:
            if msg["role"] == "user":
                messages.append(msg)
        
        # Call LLM to extract preferences
        response = groq_llama_invoke(messages)
        
        # Try to extract preferences
        try:
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                preferences = json.loads(json_str)
                
                # Simple filtering based on preferences
                filtered_doctors = []
                for doctor in state.doctor_recommendations:
                    # Score each doctor based on preferences
                    match_score = 0
                    
                    # Distance preference
                    if "location" in preferences:
                        loc_pref = preferences["location"].lower()
                        if "close" in loc_pref or "near" in loc_pref:
                            # Lower distance is better
                            if doctor.get("distance_km", 100) < 10:
                                match_score += 3
                            elif doctor.get("distance_km", 100) < 20:
                                match_score += 2
                            elif doctor.get("distance_km", 100) < 30:
                                match_score += 1
                    
                    # Rating preference
                    if "rating" in preferences or "experienced" in str(preferences).lower():
                        if doctor.get("rating", 0) >= 4.5:
                            match_score += 3
                        elif doctor.get("rating", 0) >= 4.0:
                            match_score += 2
                        elif doctor.get("rating", 0) >= 3.5:
                            match_score += 1
                    
                    # Availability preference
                    if "availability" in preferences:
                        avail_pref = preferences["availability"].lower()
                        if "soon" in avail_pref or "this week" in avail_pref:
                            if doctor.get("available_slots") and len(doctor.get("available_slots", [])) > 0:
                                match_score += 2
                    
                    # Add score to doctor
                    doctor["match_score"] = match_score
                    filtered_doctors.append(doctor)
                
                # Sort by match score
                filtered_doctors.sort(key=lambda x: x.get("match_score", 0), reverse=True)
                
                # Update recommendations if we have results
                if filtered_doctors:
                    state.doctor_recommendations = filtered_doctors
                    print(f"Filtered and ranked {len(filtered_doctors)} doctors")
                    
                # Save preferences for reference
                state.extracted_info["doctor_preferences"] = preferences
                
            else:
                print("No preference JSON found in response")
        except Exception as e:
            print(f"Error parsing doctor preferences: {e}")
        
        return state
    
    def extract_appointment_details(self, state: PatientAgentState) -> PatientAgentState:
        """Extract appointment details from user messages."""
        print("Extracting appointment details")
        
        system_prompt = """
        You are an AI assistant for a healthcare appointment scheduler. Extract any appointment 
        date and time preferences from the patient's messages. Look for:
        
        1. Specific dates (e.g., "next Monday", "May 5th", "tomorrow")
        2. Time preferences (e.g., "morning", "afternoon", "evening", "at 2pm")
        3. Day preferences (e.g., "weekdays only", "weekend")
        
        Convert relative dates to actual dates based on today's date: {today_date}
        
        Return a JSON object with "appointment_date" and "appointment_time" fields if found.
        Use ISO format for dates (YYYY-MM-DD) and 24-hour format for times (HH:MM).
        """
        
        today_date = datetime.now().strftime("%Y-%m-%d")
        
        # Create messages for LLM
        messages = [
            {"role": "system", "content": system_prompt.format(today_date=today_date)}
        ]
        
        # Add conversation history
        for msg in state.messages:
            if msg["role"] == "user":
                messages.append(msg)
        
        # Call LLM to extract appointment details
        response = groq_llama_invoke(messages)
        
        # Try to extract appointment details
        try:
            json_start = response.find('{')
            json_end = response.rfind('}')
            
            if json_start >= 0 and json_end >= 0:
                json_str = response[json_start:json_end+1]
                appointment_details = json.loads(json_str)
                
                # Update state with extracted details
                if "appointment_date" in appointment_details:
                    state.extracted_info["appointment_date"] = appointment_details["appointment_date"]
                if "appointment_time" in appointment_details:
                    state.extracted_info["appointment_time"] = appointment_details["appointment_time"]
                    
                print(f"Extracted appointment details: {appointment_details}")
            else:
                print("No appointment details found in response")
        except Exception as e:
            print(f"Error parsing appointment details: {e}")
        
        return state
    
    def book_appointment(self, state: PatientAgentState) -> PatientAgentState:
        """Book an appointment with the selected doctor."""
        print("Booking appointment")
        
        if not state.selected_doctor:
            print("No doctor selected, cannot book appointment")
            return state
        
        # Get appointment details
        date = state.extracted_info.get("appointment_date")
        time = state.extracted_info.get("appointment_time")
        
        # If date or time is missing, use doctor's available slots
        if not date or not time:
            # Use the first available slot if available
            if "available_slots" in state.selected_doctor and state.selected_doctor["available_slots"]:
                first_day = state.selected_doctor["available_slots"][0]
                date = first_day["date"]
                if first_day["slots"]:
                    time = first_day["slots"][0]
        
        # Book the appointment
        if date and time:
            patient_id = state.user_id
            doctor_id = state.selected_doctor["doctor_id"]
            
            appointment_result = self.services.appointment_booking_service(
                action="book",
                patient_id=patient_id,
                doctor_id=doctor_id,
                date=date,
                time=time
            )
            
            if appointment_result["status"] == "success":
                state.appointment_details = appointment_result
                print(f"Appointment booked successfully: {date} at {time}")
                
                # Update stage
                state.current_stage = ConversationStage.CONFIRMATION
            else:
                print(f"Failed to book appointment: {appointment_result.get('message')}")
        else:
            print("Missing date or time for appointment")
        
        return state
    
    def send_confirmation(self, state: PatientAgentState) -> PatientAgentState:
        """Send confirmation notification to the patient."""
        if not state.appointment_details:
            print("No appointment details available for confirmation")
            return state
        
        print("Sending appointment confirmation")
        
        # Send notification
        notification_result = self.services.notification_service(
            recipient_type="patient",
            recipient_id=state.user_id,
            notification_type="appointment_confirmation",
            content={
                "appointment_id": state.appointment_details["appointment_id"],
                "doctor": state.appointment_details["doctor"],
                "date": state.appointment_details["date"],
                "time": state.appointment_details["time"],
                "location": state.appointment_details["hospital"]
            }
        )
        
        print(f"Notification sent: {notification_result}")
        
        # Mark conversation as complete
        state.conversation_complete = True
        state.current_stage = ConversationStage.COMPLETED
        
        return state

# Main function to run the agent
def run_patient_agent(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run the patient agent with the given input data."""
    agent = PatientAgent()
    return agent.invoke(input_data)

# Example usage
if __name__ == "__main__":
    # Example input
    example_input = {
        "user_id": "P12345",
        "message_type": "text",
        "message_content": "Hi, I've been having a headache for the past 3 days and it's getting worse",
        "timestamp": datetime.now().isoformat(),
    }
    
    # Run agent
    result = run_patient_agent(example_input)
    print("\nPatient Agent Response:")
    print(json.dumps(result, indent=2))