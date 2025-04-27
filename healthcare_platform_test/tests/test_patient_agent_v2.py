import sys
import os
import json
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

# Add src to path
src_path = Path(__file__).resolve().parent.parent / "src"
sys.path.append(str(src_path))

# Import dummy services
from services.dummy_services_v2 import DummyServices

# Import LLM invoker
from groq_llama_helper import groq_llama_invoke, langchain_to_groq_messages

# LangGraph & LangChain
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field

# Initialize services
services = DummyServices()

class PatientAgentState(BaseModel):
    """Complete state of the patient conversation."""
    user_id: str
    messages: List[Dict[str, str]] = Field(default_factory=list)  # Now list of {role, content}
    captured_info: Dict[str, Any] = Field(default_factory=dict)
    current_stage: str = "start"
    previous_context: Optional[Dict[str, Any]] = None
    final_response: Optional[str] = None
    tool_outputs: List[Dict[str, Any]] = Field(default_factory=list)

def fetch_user_profile(state: PatientAgentState) -> PatientAgentState:
    print("\nFetching user profile...")
    profile = services.fetch_user_profile(state.user_id)
    state.previous_context = profile.get("previous_context", {})
    state.messages += profile.get("previous_messages", [])
    return state

def detect_resume_or_new_convo(state: PatientAgentState) -> PatientAgentState:
    if state.previous_context and state.previous_context.get("incomplete_conversation", False):
        # If old unfinished conversation
        system_prompt = "The user had an incomplete conversation last time. Ask if they want to continue or start fresh."
        prompt_messages = [{"role": "system", "content": system_prompt}]
        # prompt_messages += langchain_to_groq_messages(state.messages)
        response = groq_llama_invoke(prompt_messages)
        
        # Here assume simple logic: if user says "continue", pick up from previous stage
        if "continue" in response.lower():
            state.current_stage = state.previous_context.get("current_stage", "start")
        else:
            state.current_stage = "gather_issue"
    else:
        state.current_stage = "gather_issue"
    
    return state

def gather_issue_details(state: PatientAgentState) -> PatientAgentState:
    print("\nGathering issue details...")
    
    system_prompt = "Talk to the patient and collect all details about their symptoms, preferences, appointment needs."
    prompt_messages = [{"role": "system", "content": system_prompt}]
    # prompt_messages += langchain_to_groq_messages(state.messages)
    response = groq_llama_invoke(prompt_messages)
    
    # Here we can simulate info extraction (more sophisticated logic can be added)
    state.captured_info["issue_summary"] = response
    state.current_stage = "suggest_field"
    return state


def suggest_medical_field(state: PatientAgentState) -> PatientAgentState:
    print("\nSuggesting medical specialty...")
    
    system_prompt = "Based on the patient's issue summary, recommend an appropriate doctor specialty."
    prompt_messages = [{"role": "system", "content": system_prompt}]
    prompt_messages += [{"role": "user", "content": state.captured_info["issue_summary"]}]
    response = groq_llama_invoke(prompt_messages)
    
    state.captured_info["recommended_field"] = response
    state.current_stage = "post_field_choice"
    return state


def handle_user_choice_post_field(state: PatientAgentState) -> PatientAgentState:
    print("\nHandling user decision after field suggestion...")
    
    system_prompt = f"We suggested {state.captured_info['recommended_field']} specialty. Ask if user wants to see doctor recommendations or not."
    prompt_messages = [{"role": "system", "content": system_prompt}]
    # prompt_messages += langchain_to_groq_messages(state.messages)
    response = groq_llama_invoke(prompt_messages)
    
    if "recommend" in response.lower():
        state.current_stage = "recommend_doctor"
    else:
        state.current_stage = "end_conversation"
    return state



def recommend_doctors_loop(state: PatientAgentState) -> PatientAgentState:
    print("\nRecommending doctors...")
    
    doctor_list = services.get_doctor_list(specialty=state.captured_info.get("recommended_field"))
    state.tool_outputs.append({"tool_name": "doctor_list", "output": doctor_list})
    
    system_prompt = "Present the following doctor options to the patient and ask if they want to select one or see more."
    context_doctors = json.dumps(doctor_list)
    
    prompt_messages = [{"role": "system", "content": system_prompt}]
    prompt_messages += [{"role": "user", "content": context_doctors}]
    response = groq_llama_invoke(prompt_messages)
    
    if "select" in response.lower():
        state.current_stage = "doctor_selected"
    else:
        state.current_stage = "recommend_doctor"
    
    return state

def handle_doctor_selection(state: PatientAgentState) -> PatientAgentState:
    print("\nHandling doctor selection...")
    # Assume selected doctor info captured
    selected_doctor = {"doctor_id": "doc123", "name": "Dr. Sharma"}
    state.captured_info["selected_doctor"] = selected_doctor
    state.current_stage = "book_appointment"
    return state


def book_appointment(state: PatientAgentState) -> PatientAgentState:
    print("\nBooking appointment...")
    appointment_info = {
        "user_id": state.user_id,
        "doctor_id": state.captured_info["selected_doctor"]["doctor_id"],
        "preferred_time": state.captured_info.get("preferred_time", "Next Available")
    }
    booking_response = services.book_appointment_service(appointment_info)
    state.tool_outputs.append({"tool_name": "book_appointment", "output": booking_response})
    state.current_stage = "confirm_and_end"
    return state


def confirm_and_end(state: PatientAgentState) -> PatientAgentState:
    print("\nConfirming appointment and ending conversation...")
    booking = next((to["output"] for to in state.tool_outputs if to["tool_name"] == "book_appointment"), {})
    state.final_response = f"Your appointment is confirmed! Details: {json.dumps(booking, indent=2)}"
    return state


def create_patient_agent_v2() -> StateGraph:
    graph = StateGraph(PatientAgentState)
    
    # Nodes
    graph.add_node("fetch_user_profile", fetch_user_profile)
    graph.add_node("detect_resume", detect_resume_or_new_convo)
    graph.add_node("gather_issue", gather_issue_details)
    graph.add_node("suggest_field", suggest_medical_field)
    graph.add_node("post_field_choice", handle_user_choice_post_field)
    graph.add_node("recommend_doctor", recommend_doctors_loop)
    graph.add_node("doctor_selected", handle_doctor_selection)
    graph.add_node("book_appointment", book_appointment)
    graph.add_node("confirm_and_end", confirm_and_end)
    
    # Edges
    graph.add_edge(START, "fetch_user_profile")
    graph.add_edge("fetch_user_profile", "detect_resume")
    graph.add_edge("detect_resume", "gather_issue")
    graph.add_edge("gather_issue", "suggest_field")
    graph.add_edge("suggest_field", "post_field_choice")
    graph.add_edge("post_field_choice", "recommend_doctor")
    graph.add_edge("recommend_doctor", "recommend_doctor")
    graph.add_edge("recommend_doctor", "doctor_selected")
    graph.add_edge("doctor_selected", "book_appointment")
    graph.add_edge("book_appointment", "confirm_and_end")
    graph.add_edge("confirm_and_end", END)
    
    compiled_graph = graph.compile()
    return compiled_graph

def main():
    print("Welcome to the Patient Agent 👩‍⚕️👨‍⚕️!")
    print("Type 'exit' to quit at any time.\n")

    # Initialize
    patient_agent = create_patient_agent_v2()
    user_id = "user123"
    state = PatientAgentState(user_id=user_id)
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("\nAgent: Goodbye! Take care. 👋")
            break
        
        state.messages.append({"role": "user", "content": user_input})
        
        # Agent runs
        new_state = patient_agent.invoke(state)
        
        print(f"\nAgent: {new_state.final_response}")
        
        state.messages.append({"role": "assistant", "content": new_state.final_response})
        
        state.captured_info = new_state.captured_info
        state.context = new_state.context
        state.tool_outputs = new_state.tool_outputs
        state.current_stage = new_state.current_stage

if __name__ == "__main__":
    main()
