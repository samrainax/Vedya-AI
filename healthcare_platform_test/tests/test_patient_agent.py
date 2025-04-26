import sys
import os
from typing import Dict, List, Any, Optional, Union
import json
from pathlib import Path

# Add the src directory to the path so we can import from it
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.append(str(src_path))

from services.dummy_services import DummyServices
from utils.schema import PatientInputSchema, PatientOutputSchema

from langchain_community.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langgraph.graph import StateGraph, END, START
import enum

# Configure the path to your Llama model
LLAMA_MODEL_PATH = "..\models\llama-2-7b-chat.Q2_K.gguf"  # Update this path

# Initialize dummy services
services = DummyServices()

# Define the state structure for the patient agent graph
class PatientAgentState(BaseModel):
    """State for the Patient Agent graph."""
    messages: List[Union[HumanMessage, AIMessage]] = Field(default_factory=list)
    current_intent: Optional[str] = None
    patient_info: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    next_steps: Optional[str] = None
    final_response: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_outputs: List[Dict[str, Any]] = Field(default_factory=list)

# Intents for patient interactions
class PatientIntent(str, enum.Enum):
    NEW_APPOINTMENT = "new_appointment"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    FOLLOW_UP = "follow_up"
    GENERAL_INQUIRY = "general_inquiry"
    SYMPTOM_CHECK = "symptom_check"
    EMERGENCY = "emergency"
    UNCLEAR = "unclear"

# Define nodes for the patient agent graph
def patient_intent_classification(state: PatientAgentState) -> PatientAgentState:
    """Classify the patient's intent from their message."""
    messages = state.messages
    
    # Prepare the prompt for intent classification
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant for a healthcare platform serving rural patients.
        Classify the patient's intent based on their message into one of these categories:
        - NEW_APPOINTMENT: Patient wants to book a new doctor appointment
        - RESCHEDULE: Patient wants to change an existing appointment
        - CANCEL: Patient wants to cancel an appointment
        - FOLLOW_UP: Patient wants follow-up on previous visit/treatment
        - GENERAL_INQUIRY: General healthcare questions
        - SYMPTOM_CHECK: Patient is describing symptoms and wants advice
        - EMERGENCY: Patient describes urgent medical situation
        - UNCLEAR: Intent is not clear from the message

        Respond with just the intent category.
        """),
        MessagesPlaceholder(variable_name="messages")
    ])
    
    # Use Llama to classify intent
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
    llm = LlamaCpp(
        model_path=LLAMA_MODEL_PATH,
        temperature=0.1,
        max_tokens=100,
        top_p=0.95,
        callback_manager=callback_manager,
        verbose=False,
    )
    
    response = llm.invoke(prompt.invoke({"messages": messages}).to_string())
    
    # Extract intent from response
    intent = response.strip()
    print(f"\nClassified intent: {intent}")
    
    if intent in [e.value for e in PatientIntent]:
        state.current_intent = intent
    else:
        state.current_intent = PatientIntent.UNCLEAR.value
    
    return state

def patient_information_extraction(state: PatientAgentState) -> PatientAgentState:
    """Extract relevant patient information from the conversation."""
    messages = state.messages
    current_intent = state.current_intent
    
    # Prepare the prompt for information extraction
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are an AI assistant for a healthcare platform.
        Extract relevant information from the patient's message based on their intent: {current_intent}.
        
        For NEW_APPOINTMENT or SYMPTOM_CHECK:
        - Extract all symptoms mentioned
        - Extract any time preferences for the appointment
        - Extract any doctor preferences
        - Extract any location constraints
        
        For RESCHEDULE or CANCEL:
        - Extract details about the existing appointment
        - Extract any new time preferences (for reschedule)
        
        Return the information as a JSON object with appropriate fields.
        """),
        MessagesPlaceholder(variable_name="messages")
    ])
    
    # Use Llama for extraction
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
    llm = LlamaCpp(
        model_path=LLAMA_MODEL_PATH,
        temperature=0.1,
        max_tokens=500,
        top_p=0.95,
        callback_manager=callback_manager,
        verbose=False,
    )
    
    response = llm.invoke(prompt.invoke({"messages": messages}).to_string())
    
    print(f"\nExtracted information response: {response}")
    
    # Try to parse JSON from response
    try:
        # Find JSON in response (it might be embedded in explanation text)
        json_start = response.find('{')
        json_end = response.rfind('}')
        
        if json_start >= 0 and json_end >= 0:
            json_str = response[json_start:json_end+1]
            extracted_info = json.loads(json_str)
            state.patient_info.update(extracted_info)
            print(f"\nSuccessfully parsed patient info: {extracted_info}")
        else:
            raise ValueError("No JSON object found in response")
    except Exception as e:
        print(f"\nFailed to parse JSON: {e}")
        # If JSON parsing fails, create a basic structure based on text analysis
        if current_intent == PatientIntent.NEW_APPOINTMENT.value or current_intent == PatientIntent.SYMPTOM_CHECK.value:
            # Simple extraction for demo purposes
            message_text = messages[-1].content.lower()
            symptoms = []
            
            symptom_keywords = ["pain", "ache", "fever", "cough", "breathing", "headache", "chest"]
            for keyword in symptom_keywords:
                if keyword in message_text:
                    symptoms.append(keyword)
            
            state.patient_info.update({
                "symptoms": symptoms if symptoms else ["unclear symptoms"], 
                "time_preference": "not specified",
                "doctor_preference": "not specified"
            })
            print(f"\nFallback extraction: {state.patient_info}")
    
    return state

def determine_required_tools(state: PatientAgentState) -> PatientAgentState:
    """Determine which tools need to be called based on intent and extracted info."""
    intent = state.current_intent
    tool_calls = []
    
    # Get patient profile for context in almost all cases
    tool_calls.append({
        "tool_name": "patient_profile",
        "tool_input": {}
    })
    
    # Add tool calls based on intent
    if intent in [PatientIntent.NEW_APPOINTMENT.value, PatientIntent.SYMPTOM_CHECK.value]:
        if "symptoms" in state.patient_info:
            tool_calls.append({
                "tool_name": "symptom_analysis",
                "tool_input": {
                    "symptoms": state.patient_info.get("symptoms", []),
                    "patient_info": {}  # Will be populated after profile is fetched
                }
            })
    
    elif intent == PatientIntent.RESCHEDULE.value:
        # Tool calls for rescheduling would be added here
        pass
    
    # Update the state with the required tool calls
    state.tool_calls = tool_calls
    return state

def execute_tools(state: PatientAgentState) -> PatientAgentState:
    """Execute the tools specified in the state using dummy services."""
    tool_outputs = []
    
    print("\nExecuting tools:")
    for tool_call in state.tool_calls:
        tool_name = tool_call["tool_name"]
        tool_input = tool_call["tool_input"]
        
        print(f"- Executing {tool_name} with input: {tool_input}")
        
        # Use the dummy services to execute the tools
        if tool_name == "patient_profile":
            output = services.patient_profile_service(**tool_input)
            
            # Update symptom analysis tool with patient info if it exists
            for i, tc in enumerate(state.tool_calls):
                if tc["tool_name"] == "symptom_analysis":
                    state.tool_calls[i]["tool_input"]["patient_info"] = output
        
        elif tool_name == "symptom_analysis":
            output = services.symptom_analysis_service(**tool_input)
        
        elif tool_name == "doctor_matching":
            output = services.doctor_matching_service(**tool_input)
        
        elif tool_name == "appointment_booking":
            output = services.appointment_booking_service(**tool_input)
        
        elif tool_name == "notification":
            output = services.notification_service(**tool_input)
        
        else:
            output = {"status": "error", "message": f"Unknown tool: {tool_name}"}
        
        tool_outputs.append({
            "tool_name": tool_name,
            "output": output
        })
        
        print(f"- {tool_name} output: {json.dumps(output, indent=2)}")
    
    state.tool_outputs = tool_outputs
    return state

def make_decision(state: PatientAgentState) -> PatientAgentState:
    """Make decisions based on tool outputs."""
    intent = state.current_intent
    tool_outputs = {to["tool_name"]: to["output"] for to in state.tool_outputs}
    
    # Update context with gathered information
    state.context.update(tool_outputs)
    
    print(f"\nMaking decision based on intent: {intent}")
    
    # Make decisions based on intent
    if intent == PatientIntent.NEW_APPOINTMENT.value:
        symptom_analysis = tool_outputs.get("symptom_analysis", {})
        specialties = symptom_analysis.get("suggested_specialties", ["General Medicine"])
        
        print(f"Recommended specialties: {specialties}")
        
        # Add doctor matching tool call for the next step
        patient_location = {}
        if "patient_profile" in tool_outputs:
            patient_location = tool_outputs["patient_profile"].get("location", {})
        
        state.tool_calls = [{
            "tool_name": "doctor_matching",
            "tool_input": {
                "specialty": specialties[0],
                "patient_location": patient_location,
                "urgency_level": symptom_analysis.get("urgency_level", "normal")
            }
        }]
        
        state.next_steps = "find_doctors"
        
    elif intent == PatientIntent.SYMPTOM_CHECK.value:
        # Similar logic for symptom check intent
        state.next_steps = "provide_health_advice"
    
    else:
        state.next_steps = "generate_response"
    
    print(f"Next steps: {state.next_steps}")
    
    return state

def handle_appointment_booking(state: PatientAgentState) -> PatientAgentState:
    """Handle the appointment booking process."""
    # Execute doctor matching if that's the next step
    if state.next_steps == "find_doctors":
        print("\nFinding matching doctors")
        state = execute_tools(state)
        
        # Add the doctor matching results to context
        doctor_results = next((to["output"] for to in state.tool_outputs 
                             if to["tool_name"] == "doctor_matching"), {})
        state.context["matched_doctors"] = doctor_results
        
        # Generate a response with the doctor options
        state.next_steps = "present_doctor_options"
    
    return state

def generate_patient_response(state: PatientAgentState) -> PatientAgentState:
    """Generate a natural language response for the patient."""
    print("\nGenerating response to patient")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant for a healthcare platform serving rural patients.
        Based on the conversation context and the information gathered, generate a helpful,
        clear, and concise response in a friendly tone. The patients are mostly from rural
        areas with limited technology access, so keep language simple and instructions clear.
        
        If presenting doctor options, format them clearly with numbering.
        If asking for additional information, be specific about what you need.
        If providing medical information, keep it simple and non-technical.
        
        Context information is provided to help you create a personalized response.
        """),
        MessagesPlaceholder(variable_name="messages"),
        ("system", "Context information: {context}")
    ])
    
    # Use Llama for response generation
    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
    llm = LlamaCpp(
        model_path=LLAMA_MODEL_PATH,
        temperature=0.7,
        max_tokens=1000,
        top_p=0.95,
        callback_manager=callback_manager,
        verbose=False,
    )
    
    context_str = json.dumps(state.context, indent=2)
    print(f"Using context: {context_str[:200]}...")  # Print just the beginning to avoid clutter
    
    response = llm.invoke(prompt.invoke({
        "messages": state.messages,
        "context": context_str
    }).to_string())
    
    state.final_response = response
    return state

def conditional_edge_for_patient(state: PatientAgentState) -> str:
    """Determine the next node based on the state's next_steps value."""
    if state.next_steps == "find_doctors" or state.next_steps == "present_doctor_options":
        return "handle_appointment"
    else:
        return "generate_response"

# Define the patient agent graph
def create_patient_agent() -> StateGraph:
    """Create the patient agent graph."""
    # Define the graph
    workflow = StateGraph(PatientAgentState)
    
    # Add nodes to the graph
    workflow.add_node("intent_classification", patient_intent_classification)
    workflow.add_node("information_extraction", patient_information_extraction)
    workflow.add_node("determine_tools", determine_required_tools)
    workflow.add_node("execute_tools", execute_tools)
    workflow.add_node("make_decision", make_decision)
    workflow.add_node("handle_appointment", handle_appointment_booking)
    workflow.add_node("generate_response", generate_patient_response)
    
    # Add edges to connect the nodes
    workflow.add_edge(START, "intent_classification")
    workflow.add_edge("intent_classification", "information_extraction")
    workflow.add_edge("information_extraction", "determine_tools")
    workflow.add_edge("determine_tools", "execute_tools")
    workflow.add_edge("execute_tools", "make_decision")
    workflow.add_edge("make_decision", "generate_response")
    # workflow.add_edge("handle_appointment", "generate_response")
    workflow.add_edge("generate_response", END)
    
    # Compile the graph
    patient_graph = workflow.compile()
    
    return patient_graph

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

def process_patient_input(input_data: PatientInputSchema) -> PatientAgentState:
    """Process input from WhatsApp and create initial agent state."""
    initial_state = PatientAgentState()
    
    # Add the user message to the state
    initial_state.messages.append(HumanMessage(content=input_data.message_content))
    
    # Add previous context if available
    if input_data.previous_context:
        initial_state.context.update(input_data.previous_context)
    
    return initial_state

def format_patient_output(final_state: PatientAgentState) -> PatientOutputSchema:
    """Format the agent's final state into output for WhatsApp."""
    output = PatientOutputSchema(
        user_id="user123",  # This would come from the input in real implementation
        response_type="text",
        message=final_state.final_response
    )
    
    # Add appointment details if available
    if "matched_doctors" in final_state.context:
        output.response_type = "options"
        output.suggested_actions = [
            {"type": "book", "doctor_id": doc["doctor_id"], "label": f"Book with {doc['name']}"}
            for doc in final_state.context["matched_doctors"].get("doctors", [])[:3]
        ]
    
    # Add appointment confirmation if booking was done
    for tool_output in final_state.tool_outputs:
        if tool_output["tool_name"] == "appointment_booking" and tool_output["output"]["status"] == "success":
            output.response_type = "appointment_confirmation"
            output.appointment_details = tool_output["output"]
    
    return output

def patient_agent_interface(input_data: dict) -> dict:
    """Main interface for the Patient Agent."""
    print(f"\n--- Processing patient message: {input_data['message_content']} ---\n")
    
    # Parse input
    patient_input = PatientInputSchema(**input_data)
    
    # Process input and initialize state
    initial_state = process_patient_input(patient_input)
    
    # Run the agent graph
    patient_agent = create_patient_agent()
    final_state = patient_agent.invoke(initial_state)
    
    # Format output
    output = format_patient_output(final_state)
    
    print(f"\n--- Final response ---\n{output.message}\n")
    
    return output.dict()

if __name__ == "__main__":
    # Check if Llama model exists
    if not os.path.exists(LLAMA_MODEL_PATH):
        print(f"Error: Llama model not found at {LLAMA_MODEL_PATH}")
        print("Please update the LLAMA_MODEL_PATH variable to point to your downloaded model.")
        sys.exit(1)
    
    # Example patient inputs for testing
    test_inputs = [
        {
            "user_id": "user123",
            "message_type": "text",
            "message_content": "I've been having chest pain and difficulty breathing for the last two days.",
            "timestamp": "2025-04-24T14:30:00Z"
        },
        {
            "user_id": "user123",
            "message_type": "text",
            "message_content": "I need to reschedule my appointment with Dr. Singh tomorrow.",
            "timestamp": "2025-04-24T14:35:00Z"
        },
        {
            "user_id": "user123",
            "message_type": "text",
            "message_content": "I have a fever and headache. What should I do?",
            "timestamp": "2025-04-24T14:40:00Z"
        }
    ]
    
    # Test each input
    for i, test_input in enumerate(test_inputs):
        print(f"\n\n{'='*80}")
        print(f"TEST CASE {i+1}: {test_input['message_content']}")
        print(f"{'='*80}\n")
        
        result = patient_agent_interface(test_input)
        print(f"\nOutput schema: {json.dumps(result, indent=2)}")
        print(f"\n{'='*80}\n")