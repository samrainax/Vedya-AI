import json
import os
from typing import Dict, List, Any, Optional, Tuple

# Global State Constants
STATE_INITIAL = 0
STATE_CATEGORY_SELECTION = 1
STATE_DOCTOR_SELECTION = 2
STATE_APPOINTMENT_BOOKING = 3
STATE_CONFIRMATION = 4

# Data Structures
users_state: Dict[str, Dict[str, Any]] = {}

kb_categories = [
    "General Medicine", 
    "Orthopedics", 
    "Cardiology", 
    "Gynecology and Obstetrics", 
    "Pediatrics"
]

hospital_doctors = {
    "General Medicine": [
        {"name": "Dr. Anil Kumar", "qualification": "MBBS, MD (General Medicine)", "experience_years": 12},
        {"name": "Dr. Sneha Rathi", "qualification": "MBBS, DNB (Internal Medicine)", "experience_years": 8}
    ],
    "Orthopedics": [
        {"name": "Dr. Ramesh Yadav", "qualification": "MBBS, MS (Orthopedics)", "experience_years": 10},
        {"name": "Dr. Priya Mehra", "qualification": "MBBS, Diploma in Orthopedics", "experience_years": 6},
        {"name": "Dr. Arvind Sharma", "qualification": "MBBS, MS (Ortho)", "experience_years": 15}
    ],
    "Cardiology": [
        {"name": "Dr. Neeraj Sinha", "qualification": "MBBS, MD, DM (Cardiology)", "experience_years": 14},
        {"name": "Dr. Pooja Bansal", "qualification": "MBBS, MD (Medicine), Fellowship in Cardiology", "experience_years": 9}
    ],
    "Gynecology and Obstetrics": [
        {"name": "Dr. Kavita Singh", "qualification": "MBBS, MS (Obstetrics & Gynecology)", "experience_years": 11},
        {"name": "Dr. Meenal Gupta", "qualification": "MBBS, DGO (Gynecology)", "experience_years": 7}
    ],
    "Pediatrics": [
        {"name": "Dr. Vivek Verma", "qualification": "MBBS, MD (Pediatrics)", "experience_years": 13},
        {"name": "Dr. Ananya Joshi", "qualification": "MBBS, DCH (Child Health)", "experience_years": 5},
        {"name": "Dr. Sameer Kapoor", "qualification": "MBBS, MD (Pediatrics)", "experience_years": 9}
    ]
}

doctor_available_slots = {
    "Dr. Anil Kumar": ["9:00 AM - 10:00 AM", "4:00 PM - 5:00 PM"],
    "Dr. Sneha Rathi": ["10:00 AM - 11:00 AM", "5:00 PM - 6:00 PM"],
    
    "Dr. Ramesh Yadav": ["9:00 AM - 11:00 AM", "3:00 PM - 4:00 PM"],
    "Dr. Priya Mehra": ["11:00 AM - 12:00 PM", "4:00 PM - 5:00 PM"],
    "Dr. Arvind Sharma": ["2:00 PM - 3:00 PM", "5:00 PM - 6:00 PM"],
    
    "Dr. Neeraj Sinha": ["9:30 AM - 10:30 AM", "3:30 PM - 4:30 PM"],
    "Dr. Pooja Bansal": ["11:30 AM - 12:30 PM", "5:00 PM - 6:00 PM"],
    
    "Dr. Kavita Singh": ["9:00 AM - 10:00 AM", "2:00 PM - 3:00 PM"],
    "Dr. Meenal Gupta": ["10:30 AM - 11:30 AM", "3:30 PM - 4:30 PM"],
    
    "Dr. Vivek Verma": ["9:00 AM - 10:00 AM", "4:00 PM - 5:00 PM"],
    "Dr. Ananya Joshi": ["10:00 AM - 11:00 AM", "5:00 PM - 6:00 PM"],
    "Dr. Sameer Kapoor": ["11:00 AM - 12:00 PM", "3:00 PM - 4:00 PM"]
}


def initialize_user(phone_number: str) -> None:
    """Initialize a new user in the system"""
    if phone_number not in users_state:
        users_state[phone_number] = {
            "state": STATE_INITIAL,
            "category": None,
            "doctor": None,
            "slot": None,
            "appointment_details": {}
        }
        
        # Create user file if it doesn't exist
        user_file = f'users/{phone_number}.json'
        if not os.path.exists('users'):
            os.makedirs('users')
            
        if not os.path.exists(user_file):
            with open(user_file, 'w') as f:
                json.dump({"messages": []}, f)


def fetch_recommendations(category: str) -> List[Dict[str, Any]]:
    """Fetch doctor recommendations based on category"""
    if category in hospital_doctors:
        return hospital_doctors[category]
    return []


def get_available_slots(doctor_name: str) -> List[str]:
    """Get available appointment slots for a doctor"""
    if doctor_name in doctor_available_slots:
        return doctor_available_slots[doctor_name]
    return []


def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """Parse the LLM's response to extract structured data"""
    try:
        # For responses in the format ["bot_response": "text", "category": "value"]
        if response_text.strip().startswith("[") and "bot_response" in response_text:
            # Clean up the text to make it valid JSON
            cleaned_text = response_text.replace("'", "\"")
            # Handle missing commas
            if "bot_response\": " in cleaned_text and "category\": " in cleaned_text:
                if "," not in cleaned_text.split("bot_response\": ")[1].split("category\": ")[0]:
                    cleaned_text = cleaned_text.replace("category\": ", ", \"category\": ")
            
            return json.loads(cleaned_text)
        
        # For doctor selection responses
        if "selected_doctor" in response_text.lower():
            for doctor in doctor_available_slots.keys():
                if doctor in response_text:
                    return {"bot_response": response_text, "selected_doctor": doctor}
        
        # For slot selection responses
        if "selected_slot" in response_text.lower():
            for doctor, slots in doctor_available_slots.items():
                for slot in slots:
                    if slot in response_text:
                        return {"bot_response": response_text, "selected_slot": slot}
        
        # Default case
        return {"bot_response": response_text}
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        return {"bot_response": response_text}


def get_prompt_for_state(phone_number: str) -> str:
    """Generate the appropriate prompt based on the user's state"""
    user_data = users_state[phone_number]
    state = user_data["state"]
    
    if state == STATE_INITIAL:
        return "You are Vedya, a friendly receptionist at a hospital. Introduce yourself briefly and ask how you can help the user today with their medical concerns."
    
    elif state == STATE_CATEGORY_SELECTION:
        categories_str = ", ".join(kb_categories)
        return f"""You are Vedya, a receptionist at a hospital. You need to conversate with the user and understand which category of health they fall in based on their symptoms or needs.

Available categories: {categories_str}

Give your response strictly in this format:
["bot_response": "your response in 2-3 lines",
"category": "category if found out else null" ]

Be empathetic but try to categorize their medical need into one of the available categories."""
    
    elif state == STATE_DOCTOR_SELECTION:
        category = user_data["category"]
        doctors = fetch_recommendations(category)
        doctors_info = "\n".join([f"- {doc['name']}, {doc['qualification']}, {doc['experience_years']} years of experience" for doc in doctors])
        
        return f"""You are Vedya, a helpful hospital receptionist. The user needs a doctor in the {category} department.

Available doctors:
{doctors_info}

Present these options to the user and ask them to select a doctor. Be friendly and helpful.
If the user selects a doctor, include "selected_doctor: [doctor name]" in your response.
"""
    
    elif state == STATE_APPOINTMENT_BOOKING:
        doctor = user_data["doctor"]
        slots = get_available_slots(doctor)
        slots_info = "\n".join([f"- {slot}" for slot in slots])
        
        return f"""You are Vedya, a helpful hospital receptionist. The user has selected {doctor}.

Available appointment slots for {doctor}:
{slots_info}

Please ask the user to select a convenient time slot. Be friendly and conversational.
If the user selects a slot, include "selected_slot: [slot]" in your response.
"""
    
    elif state == STATE_CONFIRMATION:
        doctor = user_data["doctor"]
        slot = user_data["slot"]
        
        return f"""You are Vedya, a helpful hospital receptionist. Confirm the appointment with these details:

Doctor: {doctor}
Time: {slot}

Ask if the user would like to confirm this appointment. If they confirm, thank them and let them know the appointment is booked.
If they want to change something, ask what they want to change (doctor or time slot).
"""
    
    # Default prompt
    return "You are Vedya, a helpful hospital receptionist. Continue the conversation naturally based on the user's previous messages."


def update_user_state(phone_number: str, parsed_response: Dict[str, Any]) -> None:
    """Update the user state based on the parsed response"""
    user_data = users_state[phone_number]
    current_state = user_data["state"]
    
    if current_state == STATE_CATEGORY_SELECTION and "category" in parsed_response:
        category = parsed_response["category"]
        if category and category in kb_categories:
            user_data["category"] = category
            user_data["state"] = STATE_DOCTOR_SELECTION
    
    elif current_state == STATE_DOCTOR_SELECTION and "selected_doctor" in parsed_response:
        doctor = parsed_response["selected_doctor"]
        if doctor in doctor_available_slots:
            user_data["doctor"] = doctor
            user_data["state"] = STATE_APPOINTMENT_BOOKING
    
    elif current_state == STATE_APPOINTMENT_BOOKING and "selected_slot" in parsed_response:
        slot = parsed_response["selected_slot"]
        available_slots = get_available_slots(user_data["doctor"])
        if slot in available_slots:
            user_data["slot"] = slot
            user_data["state"] = STATE_CONFIRMATION
    
    elif current_state == STATE_CONFIRMATION:
        if "confirm" in parsed_response.get("bot_response", "").lower():
            # Book the appointment
            user_data["appointment_details"] = {
                "doctor": user_data["doctor"],
                "slot": user_data["slot"],
                "status": "confirmed"
            }
            # Reset state for new conversation
            user_data["state"] = STATE_INITIAL


def save_user_data(phone_number: str, messages: List[Dict[str, str]]) -> None:
    """Save the user's conversation history"""
    user_file = f'users/{phone_number}.json'
    with open(user_file, 'w') as f:
        json.dump({"messages": messages}, f)


def load_user_data(phone_number: str) -> List[Dict[str, str]]:
    """Load the user's conversation history"""
    user_file = f'users/{phone_number}.json'
    if os.path.exists(user_file):
        with open(user_file, 'r') as f:
            user_data = json.load(f)
            return user_data.get('messages', [])
    return []


def get_llm_response(messages: List[Dict[str, str]], prompt: str) -> str:
    """Get a response from the LLM model"""
    try:
        # Import your preferred LLM client here
        # For example:
        # from openai import OpenAI
        # client = OpenAI()
        
        # Add system prompt
        system_message = {"role": "system", "content": prompt}
        
        # Take the last few messages for context
        recent_messages = messages[-8:] if len(messages) > 8 else messages
        
        # This is a placeholder for the actual LLM call
        # Replace with your actual LLM API call
        """
        completion = client.chat.completions.create(
            model="your-preferred-model",
            messages=[system_message] + recent_messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=1.0
        )
        return completion.choices[0].message.content
        """
        
        # For testing, return a mock response
        # In a real implementation, replace this with actual LLM call
        if "category" in prompt:
            return '["bot_response": "Based on your symptoms, it sounds like you need to see an Orthopedics specialist for your knee pain.", "category": "Orthopedics"]'
        elif "doctor" in prompt:
            return "I'd recommend Dr. Ramesh Yadav who has 10 years of experience in Orthopedics. Would you like to book an appointment with him? selected_doctor: Dr. Ramesh Yadav"
        elif "slot" in prompt:
            return "Dr. Ramesh Yadav has these available slots today: 9:00 AM - 11:00 AM and 3:00 PM - 4:00 PM. Which one works better for you? selected_slot: 9:00 AM - 11:00 AM"
        else:
            return "I'm Vedya, your hospital assistant. How can I help you today?"
    
    except Exception as e:
        print(f"Error getting LLM response: {e}")
        return "I'm sorry, I'm having trouble processing your request right now. Could you please try again?"


def generate_reply(incoming_msg: str, phone_number: str) -> str:
    """Generate a reply based on the incoming message"""
    # Initialize user if new
    initialize_user(phone_number)
    
    # Load user conversation history
    messages = load_user_data(phone_number)
    
    # If this is the first message, set initial state
    if not messages:
        users_state[phone_number]["state"] = STATE_CATEGORY_SELECTION
    
    # Add user message to history
    messages.append({"role": "user", "content": incoming_msg})
    
    # Get appropriate prompt based on current state
    prompt = get_prompt_for_state(phone_number)
    
    # Get response from LLM
    response_text = get_llm_response(messages, prompt)
    
    # Parse the response
    parsed_response = parse_llm_response(response_text)
    
    # Update user state based on the response
    update_user_state(phone_number, parsed_response)
    
    # Extract the bot's response message
    bot_response = parsed_response.get("bot_response", response_text)
    
    # Add bot response to conversation history
    messages.append({"role": "assistant", "content": bot_response})
    
    # Save updated conversation history
    save_user_data(phone_number, messages)
    
    return bot_response


# Example usage
if __name__ == "__main__":
    # Simulate a conversation
    phone_number = "1234567890"
    
    responses = [
        generate_reply("Hi, I need to see a doctor", phone_number),
        generate_reply("I've been having severe knee pain for the past week", phone_number),
        generate_reply("Yes, Dr. Ramesh Yadav sounds good", phone_number),
        generate_reply("The morning slot works for me", phone_number),
        generate_reply("Yes, please confirm the appointment", phone_number)
    ]
    
    print("\nConversation flow:")
    for i, response in enumerate(responses):
        print(f"Bot {i+1}: {response}\n")
    
    print("User state:", users_state[phone_number])