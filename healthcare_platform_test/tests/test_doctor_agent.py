import sys
import os
from typing import Dict, List, Any, Optional, Union
import json
from pathlib import Path
from langchain_community.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langgraph.graph import StateGraph, END
import enum

src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.append(str(src_path))

from services.dummy_services import DummyServices
from utils.schema import DoctorInputSchema, DoctorOutputSchema


# Configure the path to your Llama model
LLAMA_MODEL_PATH = "models\llama-2-7b-chat.Q2_K.gguf"  # Update this path

# Initialize dummy services
services = DummyServices()

# Define the state structure for the doctor agent graph
class DoctorAgentState(BaseModel):
    """State for the Doctor Agent graph."""
    messages: List[Union[HumanMessage, AIMessage]] = Field(default_factory=list)
    current_intent: Optional[str] = None
    doctor_info: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    next_steps: Optional[str] = None
    final_response: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_outputs: List[Dict[str, Any]] = Field(default_factory=list)

# Doctor intents
class DoctorIntent(str, enum.Enum):
    VIEW_SCHEDULE = "view_schedule"
    PATIENT_INFO = "patient_info"
    RESCHEDULE = "reschedule"
    CANCEL = "cancel"
    UPDATE_AVAILABILITY = "update_availability"
    ADD_NOTES = "add_notes"
    GENERAL_QUERY = "general_query"
    UNCLEAR = "unclear"

# Define nodes for the doctor agent graph
def doctor_intent_classification(state: DoctorAgentState) -> DoctorAgentState:
    """Classify the doctor's intent from their message."""
    messages = state.messages
    
    # Prepare the prompt for intent classification
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant for a healthcare platform serving doctors.
        Classify the doctor's intent based on their message into one of these categories:
        - VIEW_SCHEDULE: Doctor wants to view their schedule or appointments
        - PATIENT_INFO: Doctor wants information about a patient
        - RESCHEDULE: Doctor wants to reschedule an appointment
        - CANCEL: Doctor wants to cancel an appointment
        - UPDATE_AVAILABILITY: Doctor wants to update their availability
        - ADD_NOTES: Doctor wants to add notes to a patient record
        - GENERAL_QUERY: General questions about the platform
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
    print(f"\nClassified doctor intent: {intent}")
    
    if intent in [e.value for e in DoctorIntent]:
        state.current_intent = intent
    else:
        state.current_intent = DoctorIntent.UNCLEAR.value
    
    return state

def doctor_information_extraction(state: DoctorAgentState) -> DoctorAgentState:
    """Extract relevant information from the doctor's message."""
    messages = state.messages
    current_intent = state.current_intent
    
    # Prepare the prompt for information extraction
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are an AI assistant for a healthcare platform.
        Extract relevant information from the doctor's message based on their intent: {current_intent}.
        
        For VIEW_SCHEDULE:
        - Extract date information if specified
        
        For PATIENT_INFO:
        - Extract patient name or ID
        - Extract what information they're looking for
        
        For RESCHEDULE or CANCEL:
        - Extract appointment ID or details
        - Extract new time/date (for reschedule)
        
        For UPDATE_AVAILABILITY:
        - Extract days and times to update
        
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
            state.doctor_info.update(extracted_info)
            print(f"\nSuccessfully parsed doctor info: {extracted_info}")
        else:
            raise ValueError("No JSON object found in response")
    except Exception as e:
        print(f"\nFailed to parse JSON: {e}")
        # If JSON parsing fails, create a basic structure based on text analysis
        message_text = messages[-1].content.lower()
        
        if current_intent == DoctorIntent.VIEW_SCHEDULE.value:
            if "today" in message_text:
                state.doctor_info["date"] = "today"
            elif "tomorrow" in message_text:
                state.doctor_info["date"] = "tomorrow"
            
        elif current_intent == DoctorIntent.PATIENT_INFO.value:
            # Look for patient identifiers
            if "john" in message_text:
                state.doctor_info["patient_id"] = "P12345"  # Hardcoded for demo
            else:
                state.doctor_info["patient_id"] = "unknown"
    
    return state

def determine_doctor_tools(state: DoctorAgentState) -> DoctorAgentState:
    """Determine which tools need to be called based on intent and extracted info."""
    intent = state.current_intent
    tool_calls = []
    
    # Get doctor profile for context in almost all cases
    tool_calls.append({
        "tool_name": "doctor_profile",
        "tool_input": {"doctor_id": "D101"}  # Hardcoded for demo
    })
    
    # Add tool calls based on intent
    if intent == DoctorIntent.VIEW_SCHEDULE.value:
        tool_calls.append({
            "tool_name": "doctor_schedule",
            "tool_input": {
                "doctor_id": "D101",
                "date": state.doctor_info.get("date"),
                "action": "view"
            }
        })
    
    elif intent == DoctorIntent.PATIENT_INFO.value:
        if "patient_id" in state.doctor_info:
            tool_calls.append({
                "tool_name": "patient_info",
                "tool_input": {
                    "patient_id": state.doctor_info["patient_id"]
                }
            })
    
    # Update the state with the required tool calls
    state.tool_calls = tool_calls
    return state

def execute_doctor_tools(state: DoctorAgentState) -> DoctorAgentState:
    """Execute the tools specified in the state using dummy services."""
    tool_outputs = []
    
    print("\nExecuting doctor tools:")
    for tool_call in state.tool_calls:
        tool_name = tool_call["tool_name"]
        tool_input = tool_call["tool_input"]
        
        print(f"- Executing {tool_name} with input: {tool_input}")
        
        # Use the dummy services to execute the tools
        if tool_name == "doctor_profile":
            output = services.doctor_profile_service(**tool_input)
        
        elif tool_name == "doctor_schedule":
            output = services.doctor_schedule_service(**tool_input)
        
        elif tool_name == "patient_info":
            output = services.patient_info_service(**tool_input)
        
        elif tool_name == "appointment_management":
            output = services.appointment_management_service(**tool_input)
        
        elif tool_name == "availability_management":
            output = services.availability_management_service(**tool_input)
        
        else:
            output = {"status": "error", "message": f"Unknown tool: {tool_name}"}
        
        tool_outputs.append({
            "tool_name": tool_name,
            "output": output
        })
        
        print(f"- {tool_name} output: {json.dumps(output, indent=2)}")
    
    state.tool_outputs = tool_outputs
    return state

def generate_doctor_response(state: DoctorAgentState) -> DoctorAgentState:
    """Generate a natural language response for the doctor."""
    print("\nGenerating response to doctor")
    
    # Update context with tool outputs
    for tool_output in state.tool_outputs:
        state.context[tool_output["tool_name"]] = tool_output["output"]
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant for a healthcare platform serving doctors.
        Based on the conversation context and the information gathered, generate a helpful,
        clear, and professional response. Focus on providing the doctor with exactly the
        information they need in a concise format.
        
        If showing schedule information, present it in a clear, organized way.
        If showing patient information, highlight key medical details.
        
        Context information is provided to help you create a relevant response.
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

# Define the doctor agent graph
def create_doctor_agent() -> StateGraph:
    """Create the doctor agent graph."""
    # Define the graph
    workflow = StateGraph(DoctorAgentState)
    
    # Add nodes to the graph
    workflow.add_node("intent_classification", doctor_intent_classification)
    workflow.add_node("information_extraction", doctor_information_extraction)
    workflow.add_node("determine_tools", determine_doctor_tools)
    workflow.add_node("execute_tools", execute_doctor_tools)
    workflow.add_node("generate_response", generate_doctor_response)
    
    # Add edges to connect the nodes
    workflow.add_edge("intent_classification", "information_extraction")
    workflow.add_edge("information_extraction", "determine_tools")
    workflow.add_edge("determine_tools", "execute_tools")
    workflow.add_edge("execute_tools", "generate_response")
    workflow.add_edge("generate_response", END)
    
    # Compile the graph
    doctor_graph = workflow.compile()
    
    return doctor_graph

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

def process_doctor_input(input_data: DoctorInputSchema) -> DoctorAgentState:
    """Process input from Doctor Dashboard and create initial agent state."""
    initial_state = DoctorAgentState()
    
    # Add the doctor message to the state
    initial_state.messages.append(HumanMessage(content=input_data.query_content))
    
    return initial_state

def format_doctor_output(final_state: DoctorAgentState) -> DoctorOutputSchema:
    """Format the agent's final state into output for Doctor Dashboard."""
    output = DoctorOutputSchema(
        doctor_id="D101",  # This would come from the input in real implementation
        response_type="text",
        message=final_state.final_response
    )
    
    # Set response type and data based on intent
    if final_state.current_intent == DoctorIntent.VIEW_SCHEDULE.value:
        output.response_type = "schedule"
        schedule_data = None
        for tool_output in final_state.tool_outputs:
            if tool_output["tool_name"] == "doctor_schedule":
                schedule_data = tool_output["output"]
                break
        
        if schedule_data:
            output.data = schedule_data
    
    elif final_state.current_intent == DoctorIntent.PATIENT_INFO.value:
        output.response_type = "patient_info"
        patient_data = None
        for tool_output in final_state.tool_outputs:
            if tool_output["tool_name"] == "patient_info":
                patient_data = tool_output["output"]
                break
        
        if patient_data:
            output.data = patient_data
    
    return output

def doctor_agent_interface(input_data: dict) -> dict:
    """Main interface for the Doctor Agent."""
    print(f"\n--- Processing doctor query: {input_data['query_content']} ---\n")
    
    # Parse input
    doctor_input = DoctorInputSchema(**input_data)
    
    # Process input and initialize state
    initial_state = process_doctor_input(doctor_input)
    
    # Run the agent graph
    doctor_agent = create_doctor_agent()
    final_state = doctor_agent.invoke(initial_state)
    
    # Format output
    output = format_doctor_output(final_state)
    
    print(f"\n--- Final response ---\n{output.message}\n")
    
    return output.dict()

if __name__ == "__main__":
    # Check if Llama model exists
    if not os.path.exists(LLAMA_MODEL_PATH):
        print(f"Error: Llama model not found at {LLAMA_MODEL_PATH}")
        print("Please update the LLAMA_MODEL_PATH variable to point to your downloaded model.")
        sys.exit(1)
    
    # Example doctor inputs for testing
    test_inputs = [
        {
            "doctor_id": "D101",
            "query_type": "schedule",
            "query_content": "Show me my appointments for today",
            "timestamp": "2025-04-24T09:30:00Z"
        },
        {
            "doctor_id": "D101",
            "query_type": "patient",
            "query_content": "I need information about patient John Doe",
            "timestamp": "2025-04-24T10:15:00Z"
        },
        {
            "doctor_id": "D101",
            "query_type": "availability",
            "query_content": "I want to update my availability for next week. I won't be available on Monday.",
            "timestamp": "2025-04-24T11:00:00Z"
        }
    ]
    
    # Test each input
    for i, test_input in enumerate(test_inputs):
        print(f"\n\n{'='*80}")
        print(f"TEST CASE {i+1}: {test_input['query_content']}")
        print(f"{'='*80}\n")
        
        result = doctor_agent_interface(test_input)
        print(f"\nOutput schema: {json.dumps(result, indent=2)}")
        print(f"\n{'='*80}\n")
