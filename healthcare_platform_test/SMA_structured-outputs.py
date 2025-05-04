from openai import OpenAI
import json
from typing import Optional, List, Dict, Any, Union

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

# Define structured output schemas
MODERATOR_SCHEMA = {
    "type": "object",
    "properties": {
        "bot_response": {"type": "string"},
        "next_state": {"type": ["integer", "null"], "enum": [0, 1, 2, 3, None]},
        "special_action": {"type": ["string", "null"], "enum": ["cancel", "modify", "show", "help", "reset", "exit", None]},
        "needs_context": {"type": "boolean"},
        "is_general_conversation": {"type": "boolean"}
    },
    "required": ["bot_response", "next_state", "special_action", "needs_context", "is_general_conversation"]
}

CATEGORIZER_SCHEMA = {
    "type": "object",
    "properties": {
        "bot_response": {"type": "string"},
        "category": {"type": ["string", "null"], "enum": ["General Medicine", "Orthopedics", "Cardiology", None]},
        "needs_more_info": {"type": "boolean"},
        "wants_recommendation": {"type": ["boolean", "null"]}
    },
    "required": ["bot_response", "category", "needs_more_info", "wants_recommendation"]
}

DOCTOR_SELECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "bot_response": {"type": "string"},
        "doctor": {"type": ["string", "null"]},
        "wants_booking": {"type": ["boolean", "null"]}
    },
    "required": ["bot_response", "doctor", "wants_booking"]
}

APPOINTMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "bot_response": {"type": "string"},
        "date": {"type": ["string", "null"]},
        "slot": {"type": ["string", "null"]}
    },
    "required": ["bot_response", "date", "slot"]
}

PATIENT_INFO_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "number": {"type": "string"},
        "concern": {"type": "string"}
    },
    "required": ["name", "number", "concern"]
}

# State initialization
users_state = 0
kb_categoriser = '''General Medicine, Orthopedics, Cardiology'''

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
    ]
}

doctor_available_slots = {
    "Dr. Anil Kumar": {
        "2024-03-20": ["9:00 AM - 10:00 AM", "4:00 PM - 5:00 PM"],
        "2024-03-21": ["10:00 AM - 11:00 AM", "3:00 PM - 4:00 PM"],
        "2024-03-22": ["9:00 AM - 10:00 AM", "4:00 PM - 5:00 PM"]
    },
    "Dr. Sneha Rathi": {
        "2024-03-20": ["10:00 AM - 11:00 AM", "5:00 PM - 6:00 PM"],
        "2024-03-21": ["9:00 AM - 10:00 AM", "4:00 PM - 5:00 PM"],
        "2024-03-22": ["11:00 AM - 12:00 PM", "5:00 PM - 6:00 PM"]
    },
    "Dr. Ramesh Yadav": {
        "2024-03-20": ["9:00 AM - 11:00 AM", "3:00 PM - 4:00 PM"],
        "2024-03-21": ["10:00 AM - 12:00 PM", "4:00 PM - 5:00 PM"],
        "2024-03-22": ["9:00 AM - 11:00 AM", "3:00 PM - 4:00 PM"]
    },
    "Dr. Priya Mehra": {
        "2024-03-20": ["11:00 AM - 12:00 PM", "4:00 PM - 5:00 PM"],
        "2024-03-21": ["9:00 AM - 10:00 AM", "3:00 PM - 4:00 PM"],
        "2024-03-22": ["10:00 AM - 11:00 AM", "4:00 PM - 5:00 PM"]
    },
    "Dr. Arvind Sharma": {
        "2024-03-20": ["2:00 PM - 3:00 PM", "5:00 PM - 6:00 PM"],
        "2024-03-21": ["1:00 PM - 2:00 PM", "4:00 PM - 5:00 PM"],
        "2024-03-22": ["2:00 PM - 3:00 PM", "5:00 PM - 6:00 PM"]
    },
    "Dr. Neeraj Sinha": {
        "2024-03-20": ["9:30 AM - 10:30 AM", "3:30 PM - 4:30 PM"],
        "2024-03-21": ["10:30 AM - 11:30 AM", "4:30 PM - 5:30 PM"],
        "2024-03-22": ["9:30 AM - 10:30 AM", "3:30 PM - 4:30 PM"]
    },
    "Dr. Pooja Bansal": {
        "2024-03-20": ["11:30 AM - 12:30 PM", "5:00 PM - 6:00 PM"],
        "2024-03-21": ["10:30 AM - 11:30 AM", "4:00 PM - 5:00 PM"],
        "2024-03-22": ["11:30 AM - 12:30 PM", "5:00 PM - 6:00 PM"]
    }
}

#place holders for the state management
curr_category = ""
curr_doctor = ""
selected_slot = ""
selected_date = ""

def fetch_recommendations(curr_category):
    return hospital_doctors[curr_category]

def book_appointment(curr_doctor):
    return doctor_available_slots[curr_doctor]

def extract_doctor_name(message, available_doctors):
    """Extract doctor name from message using flexible matching"""
    message = message.lower()
    
    # Try exact matches first
    for doc in available_doctors:
        if doc["name"].lower() in message:
            return doc["name"]
        if doc["name"].split("Dr. ")[1].lower() in message:
            return doc["name"]
    
    # Try partial matches
    for doc in available_doctors:
        last_name = doc["name"].split("Dr. ")[1].lower()
        if any(word in message for word in last_name.split()):
            return doc["name"]
    
    # Try fuzzy matching
    for doc in available_doctors:
        last_name = doc["name"].split("Dr. ")[1].lower()
        if any(word.startswith(last_name.split()[0][:3]) for word in message.split()):
            return doc["name"]
    
    return None

def extract_time_slot(message, available_slots):
    """Extract time slot from message using flexible matching"""
    message = message.lower()
    
    # Try exact matches first
    for slot in available_slots:
        if slot.lower() in message:
            return slot
    
    # Try partial matches
    for slot in available_slots:
        # Extract time components
        time_parts = slot.lower().split(' - ')
        if any(part in message for part in time_parts):
            return slot
    
    # Try fuzzy matching with time numbers
    time_numbers = {
        '9': '9:00 AM',
        '10': '10:00 AM',
        '11': '11:00 AM',
        '12': '12:00 PM',
        '1': '1:00 PM',
        '2': '2:00 PM',
        '3': '3:00 PM',
        '4': '4:00 PM',
        '5': '5:00 PM',
        '6': '6:00 PM'
    }
    
    for num, time in time_numbers.items():
        if num in message:
            # Find the closest matching slot
            for slot in available_slots:
                if time in slot:
                    return slot
    
    return None

def extract_date(message):
    """Extract date from message using flexible matching"""
    message = message.lower()
    
    # Map common date references to actual dates
    date_mapping = {
        '20': '2024-03-20',
        '20th': '2024-03-20',
        'twenty': '2024-03-20',
        '21': '2024-03-21',
        '21st': '2024-03-21',
        'twenty one': '2024-03-21',
        'twenty first': '2024-03-21',
        '22': '2024-03-22',
        '22nd': '2024-03-22',
        'twenty two': '2024-03-22',
        'twenty second': '2024-03-22',
        'last': '2024-03-22',
        'last one': '2024-03-22',
        'first': '2024-03-20',
        'second': '2024-03-21',
        'third': '2024-03-22'
    }
    
    # Try exact matches first
    for ref, date in date_mapping.items():
        if ref in message:
            return date
    
    return None

def extract_patient_info(messages):
    """Extract patient information from conversation history using LLM"""
    prompt = '''Extract patient information from the conversation history.
    Look for:
    1. Patient's name
    2. Patient's phone number
    3. Patient's concern in brief
    
    If any information is missing, use "Unknown" for name and "0000000000" for phone number.
    
    Respond with a JSON containing the following keys:
    - "name": the patient's name or "Unknown"
    - "number": the patient's phone number or "0000000000"
    - "concern": a brief description of the patient's concern or "General checkup"
    '''

    system_message = {"role": "system", "content": prompt}
    conversation_messages = messages.copy()
    conversation_messages.insert(0, system_message)
    
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=conversation_messages,
        temperature=0.3,
        max_completion_tokens=1024,
        top_p=1.0,
        response_format={"type": "json_object", "schema": PATIENT_INFO_SCHEMA},
        stream=False,
        stop=None,
    )

    try:
        patient_info = json.loads(completion.choices[0].message.content)
        # Ensure required fields are present
        if "name" not in patient_info:
            patient_info["name"] = "Unknown"
        if "number" not in patient_info:
            patient_info["number"] = "0000000000"
        if "concern" not in patient_info:
            patient_info["concern"] = "General checkup"
        return patient_info
    except json.JSONDecodeError:
        return {"name": "Unknown", "number": "0000000000", "concern": "General checkup"}

def create_appointment_object(patient_name, patient_number, doctor_name, appointment_date, appointment_time, patient_concern):
    """Create an appointment object with the given details"""
    # Generate a unique appointment ID
    try:
        import os
        appointments_file = 'appointments.json'
        
        # Create the file with empty array if it doesn't exist
        if not os.path.exists(appointments_file):
            with open(appointments_file, 'w') as f:
                f.write('[]')
                
        # Get current number of appointments
        with open(appointments_file, 'r') as f:
            appointment_id = str(len(f.readlines()) + 1)
    except Exception as e:
        print(f"[WARNING] Error accessing appointments file: {e}")
        appointment_id = "1"  # Default to 1 if we can't access the file
    
    # Create doctor mapping for IDs and numbers (in production, this would come from a database)
    doctor_mapping = {
        "Dr. Anil Kumar": {"id": "DOC001", "number": "1234567890"},
        "Dr. Sneha Rathi": {"id": "DOC002", "number": "1234567891"},
        "Dr. Ramesh Yadav": {"id": "DOC003", "number": "1234567892"},
        "Dr. Priya Mehra": {"id": "DOC004", "number": "1234567893"},
        "Dr. Arvind Sharma": {"id": "DOC005", "number": "1234567894"},
        "Dr. Neeraj Sinha": {"id": "DOC006", "number": "1234567895"},
        "Dr. Pooja Bansal": {"id": "DOC007", "number": "1234567896"}
    }
    
    # Get doctor details from mapping
    doctor_details = doctor_mapping.get(doctor_name, {"id": "DOC000", "number": "0000000000"})
    
    # Create the appointment object
    appointment = {
        "appointmentId": appointment_id,
        "patientId": "PAT" + appointment_id.zfill(5),  # Generate a dummy patient ID
        "patientName": patient_name,
        "patientNumber": patient_number,
        "doctorNumber": doctor_details["number"],
        "doctorId": doctor_details["id"],
        "doctorName": doctor_name,
        "appointmentDate": appointment_date,
        "appointmentTime": appointment_time,
        "appointmentStatus": "confirmed",
        "patientConcern": patient_concern
    }
    
    return appointment
    
def append_appointment_to_json(appointment):
    """Append the appointment object to appointments.json"""
    try:
        import json
        import os
        
        appointments_file = 'appointments.json'
        
        # Create the file with empty array if it doesn't exist
        if not os.path.exists(appointments_file):
            with open(appointments_file, 'w') as file:
                json.dump([], file)
        
        # Read existing appointments
        with open(appointments_file, 'r') as file:
            try:
                appointments = json.load(file)
            except json.JSONDecodeError:
                # File exists but isn't valid JSON
                appointments = []
        
        # Append new appointment
        appointments.append(appointment)
        
        # Write back to file
        with open(appointments_file, 'w') as file:
            json.dump(appointments, file, indent=4)
        
        return True
    except Exception as e:
        print(f"[ERROR] Error saving appointment: {str(e)}")
        return False


def generate_reply(incoming_msg, phone_number=""):
    global users_state, curr_category, curr_doctor, selected_slot, selected_date
    prompt = ""

    print(f"\n[DEBUG] Current State: {users_state}")
    print(f"[DEBUG] Current Category: {curr_category}")
    print(f"[DEBUG] Current Doctor: {curr_doctor}")
    print(f"[DEBUG] Selected Date: {selected_date}")
    print(f"[DEBUG] Selected Slot: {selected_slot}")

    # Initialize messages with system prompt
    messages = [
        {
            "role": "system",
            "content": prompt
        }
    ]

    # Add conversation history
    if hasattr(generate_reply, 'conversation_history'):
        messages.extend(generate_reply.conversation_history[-10:])  # Keep last 10 exchanges
    else:
        generate_reply.conversation_history = []

    # State 0: Moderator - Route to appropriate state based on query
    if users_state == 0:
        print("\n[STATE 0] Moderator analyzing query...")
        prompt = f'''You are Vedya, a friendly and helpful hospital receptionist. Your task is to:
        1. Engage in natural conversation with the user
        2. Transition to State 1 (categorizer) IMMEDIATELY when any health issue is mentioned
        3. Handle general queries and small talk
        4. Maintain a friendly and professional tone

        Available states:
        - State 1: Health concern classification (TRANSITION IMMEDIATELY when user mentions any health issue)
        - State 2: Doctor selection (ONLY when user has already selected a category and EXPLICITLY wants to choose a doctor)
        - State 3: Appointment booking (ONLY when user has already selected a doctor and EXPLICITLY wants to book a slot)

        Special cases to handle:
        - "cancel my appointment" -> Handle cancellation
        - "change my appointment" -> Handle modification
        - "show my appointments" -> Show booking history
        - "help" -> Show available commands
        - "start over" -> Reset to State 1
        - "exit" or "bye" -> End conversation

        Your task is to:
        1. Keep the conversation natural and friendly
        2. Set "next_state" to 1 IMMEDIATELY when user mentions ANY health issue
        3. Set "is_general_conversation" to true for casual talk
        4. Only set "next_state" to 2 or 3 when user has already selected a category/doctor
        5. If special action is needed, set "special_action" accordingly
        6. If more context is needed, set "needs_context" to true

        Respond with a JSON containing the following keys:
        - "bot_response": a helpful response to the user
        - "next_state": numerical value (0, 1, 2, 3, or null)
        - "special_action": string value (cancel, modify, show, help, reset, exit, or null)
        - "needs_context": boolean value
        - "is_general_conversation": boolean value
        '''
        messages[0]["content"] = prompt

        # Send to LLM for analysis with structured output
        messages.append({"role": "user", "content": incoming_msg})
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            temperature=0.3,
            max_completion_tokens=1024,
            top_p=1.0,
            response_format={"type": "json_object", "schema": MODERATOR_SCHEMA},
            stream=False,
            stop=None,
        )

        parsed_response = json.loads(completion.choices[0].message.content)
        print(f"\n[DEBUG] Structured Response: {parsed_response}")
        
        # Update conversation history
        generate_reply.conversation_history.extend([
            {"role": "user", "content": incoming_msg},
            {"role": "assistant", "content": completion.choices[0].message.content}
        ])
        
        # Handle special actions
        if parsed_response.get("special_action"):
            if parsed_response["special_action"] == "cancel":
                return "I'll help you cancel your appointment. Please provide your appointment details."
            elif parsed_response["special_action"] == "modify":
                return "I'll help you modify your appointment. Please provide your current appointment details."
            elif parsed_response["special_action"] == "show":
                return "Here are your recent appointments: [Appointment history would be shown here]"
            elif parsed_response["special_action"] == "help":
                return '''Here are the available commands:
                - "I need to see a doctor" -> Start new appointment
                - "Show me available doctors" -> View doctors list
                - "Book an appointment" -> Start booking process
                - "Cancel my appointment" -> Cancel existing appointment
                - "Change my appointment" -> Modify existing appointment
                - "Show my appointments" -> View appointment history
                - "Help" -> Show this help message
                - "Start over" -> Reset conversation
                - "Exit" or "Bye" -> End conversation'''
            elif parsed_response["special_action"] == "reset":
                users_state = 1
                curr_category = ""
                curr_doctor = ""
                selected_slot = ""
                selected_date = ""
                return "Let's start fresh. How can I help you today?"
            elif parsed_response["special_action"] == "exit":
                return "Thank you for using our service. Goodbye!"
        
        # Handle general conversation
        if parsed_response.get("is_general_conversation", False):
            return parsed_response["bot_response"]
        
        # Route to appropriate state only if there's clear intent
        if parsed_response.get("next_state") is not None:
            users_state = parsed_response["next_state"]
            print(f"[DEBUG] Moderator routing to State {users_state}")
            return parsed_response["bot_response"]
        
        # If needs more context
        if parsed_response.get("needs_context", False):
            return parsed_response["bot_response"]
        
        # Default response - stay in general conversation
        return parsed_response["bot_response"]

    elif users_state == 1:
        print("\n[STATE 1] Understanding user's health issue...")
        prompt = f'''You are Vedya, a receptionist at a hospital. Your task is to:
        1. Quickly understand the user's main health concern
        2. Ask ONLY ONE follow-up question if needed
        3. Classify into: {kb_categoriser}
        4. After classification, ask if they want doctor recommendations

        Follow these rules strictly:
        - If user mentions pain, ask only about location
        - If user mentions location, ask only about duration
        - After getting location or duration, immediately classify
        - Never ask the same question twice
        - Never ask more than one follow-up question
        - Check conversation history to avoid repeating questions
        - ALWAYS provide a bot_response, even when classifying
        - After classification, ask if they want doctor recommendations

        Respond with a JSON containing the following keys:
        - "bot_response": a helpful response to the user
        - "category": one of ["General Medicine", "Orthopedics", "Cardiology"] or null
        - "needs_more_info": boolean value 
        - "wants_recommendation": boolean value or null
        '''
        messages[0]["content"] = prompt

        # Send to LLM for analysis with structured output
        messages.append({"role": "user", "content": incoming_msg})
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            temperature=0.3,
            max_completion_tokens=1024,
            top_p=1.0,
            response_format={"type": "json_object", "schema": CATEGORIZER_SCHEMA},
            stream=False,
            stop=None,
        )

        parsed_response = json.loads(completion.choices[0].message.content)
        print(f"\n[DEBUG] Structured Response: {parsed_response}")
        
        # Update conversation history
        generate_reply.conversation_history.extend([
            {"role": "user", "content": incoming_msg},
            {"role": "assistant", "content": completion.choices[0].message.content}
        ])
        
        # Handle category-related logic if we're in State 1
        if "category" in parsed_response and (parsed_response["category"] is not None and 
            parsed_response["category"] in hospital_doctors and 
            not parsed_response.get("needs_more_info", True)):
            
            if parsed_response.get("wants_recommendation") is False:
                print("\n[STATE TRANSITION] User doesn't want recommendations")
                users_state = 0  # Return to moderator
                curr_category = ""  # Reset category
                return "Thank you for using our service. Feel free to reach out if you need any help in the future!"
            
            if parsed_response.get("wants_recommendation") is True:
                print(f"\n[STATE TRANSITION] Category identified: {parsed_response['category']}")
                curr_category = parsed_response["category"]
                users_state = 2
                print("[DEBUG] Moving to State 2: Doctor Selection")
                # Return the doctor list directly
                list_of_docs = fetch_recommendations(curr_category)
                doctors_list = "\n".join([f"{i+1}. {doc['name']} - {doc['qualification']} ({doc['experience_years']} years experience)" 
                                        for i, doc in enumerate(list_of_docs)])
                return f"Here are our {curr_category} specialists:\n{doctors_list}\nPlease let me know which doctor you would like to consult."
            
            # If wants_recommendation is null, ask if they want recommendations
            return f"I've classified your concern under {parsed_response['category']}. Would you like me to recommend a doctor for your {parsed_response['category']} concern?"
        
        # For non-category related responses in State 1, return the bot response
        return parsed_response["bot_response"]

    elif users_state == 2:
        print(f"\n[STATE 2] Fetching doctors for category: {curr_category}")
        list_of_docs = fetch_recommendations(curr_category)
        print(f"[DEBUG] Available doctors: {list_of_docs}")
        
        prompt = f'''You are Vedya, you need to help the user choose a doctor from these options: 
        Available doctors in {curr_category}:
        {list_of_docs}

        Your task is to:
        1. Present ONLY these specific doctors with their qualifications
        2. Ask the user to choose one from these exact doctors
        3. Wait for their selection
        4. Only after they select a doctor, ask if they want to book an appointment

        Important:
        - Only use the doctors listed above
        - Do not make up any other doctors
        - If user mentions a doctor's name (full or partial), set "doctor" to the full doctor name
        - Only set "wants_booking" to true/false after they select a doctor
        - DO NOT ask if they want recommendations again - they already said yes

        Respond with a JSON containing the following keys:
        - "bot_response": a helpful response to the user
        - "doctor": the full doctor name or null
        - "wants_booking": boolean value or null
        '''
        messages[0]["content"] = prompt

        # Send to LLM for analysis with structured output
        messages.append({"role": "user", "content": incoming_msg})
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            temperature=0.3,
            max_completion_tokens=1024,
            top_p=1.0,
            response_format={"type": "json_object", "schema": DOCTOR_SELECTION_SCHEMA},
            stream=False,
            stop=None,
        )

        parsed_response = json.loads(completion.choices[0].message.content)
        print(f"\n[DEBUG] Structured Response: {parsed_response}")
        
        # Update conversation history
        generate_reply.conversation_history.extend([
            {"role": "user", "content": incoming_msg},
            {"role": "assistant", "content": completion.choices[0].message.content}
        ])
        
        # Handle doctor selection
        if parsed_response.get("doctor"):
            # User selected a doctor
            doctor_name = parsed_response["doctor"]
            if doctor_name in [doc["name"] for doc in list_of_docs]:
                curr_doctor = doctor_name
                
                # Check if user wants to book an appointment
                if parsed_response.get("wants_booking") is True:
                    users_state = 3
                    print(f"[DEBUG] Moving to State 3: Appointment Booking for {curr_doctor}")
                    
                    # Show available dates
                    available_slots = book_appointment(curr_doctor)
                    dates_list = "\n".join([f"- {date}" for date in available_slots.keys()])
                    return f"Great! Here are the available dates for {curr_doctor}:\n{dates_list}\nPlease select a date."
                
                elif parsed_response.get("wants_booking") is False:
                    users_state = 0
                    return f"You've selected {curr_doctor}. If you change your mind about booking, just let me know."
                
                # If wants_booking is null, ask if they want to book
                return f"You've selected {curr_doctor}. Would you like to book an appointment with this doctor?"
        
        # No doctor selected yet
        return parsed_response["bot_response"]

    elif users_state == 3:
        print(f"\n[STATE 3] Fetching slots for doctor: {curr_doctor}")
        available_slots = book_appointment(curr_doctor)
        print(f"[DEBUG] Available slots: {available_slots}")
        
        prompt = f'''You are Vedya, helping the user book an appointment with {curr_doctor}.
        Available dates and slots:
        {available_slots}

        Your task is to:
        1. Present available dates
        2. After date selection, present available time slots
        3. Confirm the final booking

        Important:
        - Use exact dates from the available slots
        - Use exact time slots from the available slots
        - Set both date and slot to null until they are selected
        - After both are selected, confirm the booking

        Respond with a JSON containing the following keys:
        - "bot_response": a helpful response to the user
        - "date": the selected date in YYYY-MM-DD format or null
        - "slot": the selected time slot or null
        '''
        messages[0]["content"] = prompt

        # Check if we can extract date from message
        extracted_date = extract_date(incoming_msg)
        if extracted_date and extracted_date in available_slots and not selected_date:
            selected_date = extracted_date
            print(f"[DEBUG] Date extracted from message: {selected_date}")
        
        # Check if we can extract time slot from message
        if selected_date:
            extracted_slot = extract_time_slot(incoming_msg, available_slots[selected_date])
            if extracted_slot and not selected_slot:
                selected_slot = extracted_slot
                print(f"[DEBUG] Slot extracted from message: {selected_slot}")

        # Send to LLM for analysis with structured output
        messages.append({"role": "user", "content": incoming_msg})
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            temperature=0.3,
            max_completion_tokens=1024,
            top_p=1.0,
            response_format={"type": "json_object", "schema": APPOINTMENT_SCHEMA},
            stream=False,
            stop=None,
        )

        parsed_response = json.loads(completion.choices[0].message.content)
        print(f"\n[DEBUG] Structured Response: {parsed_response}")
        
        # Update conversation history
        generate_reply.conversation_history.extend([
            {"role": "user", "content": incoming_msg},
            {"role": "assistant", "content": completion.choices[0].message.content}
        ])
        
        # Handle appointment booking
        if parsed_response.get("date") and not selected_date:
            selected_date = parsed_response["date"]
        
        if parsed_response.get("slot") and not selected_slot:
            selected_slot = parsed_response["slot"]
        
        # If both date and slot are selected
        if selected_date and selected_slot:
            # Final confirmation - booking is complete
            print(f"[DEBUG] Appointment booked: {curr_doctor} on {selected_date} at {selected_slot}")
            
            # Extract patient info from conversation history
            patient_info = extract_patient_info(generate_reply.conversation_history)
            
            # Create appointment object
            appointment = create_appointment_object(
                patient_info.get("name", "Unknown"), 
                patient_info.get("number", "0000000000"), 
                curr_doctor, 
                selected_date, 
                selected_slot,
                patient_info.get("concern", "General checkup")
            )
            
            # Save appointment
            try:
                append_appointment_to_json(appointment)
                # Reset state
                users_state = 0
                curr_category = ""
                curr_doctor = ""
                selected_date = ""
                selected_slot = ""
                return f"Appointment confirmed with {curr_doctor} on {selected_date} at {selected_slot}. We'll see you then!"
            except Exception as e:
                print(f"[ERROR] Failed to save appointment: {e}")
                return f"Your appointment with {curr_doctor} on {selected_date} at {selected_slot} has been confirmed, but there was an issue saving it to our system. Please make a note of these details."
        
        # If only date is selected
        elif selected_date and not selected_slot:
            slots_list = "\n".join([f"- {slot}" for slot in available_slots[selected_date]])
            return f"For {selected_date}, {curr_doctor} has the following available slots:\n{slots_list}\nPlease select a time slot."
        
        # Default response
        return parsed_response["bot_response"]

    print("\n[DEBUG] No matching state found. Returning generic response.")
    return "I'll help you with that. Let me find the right doctor for you."

if __name__ == "__main__":
    print("\n=== Hospital Appointment Booking System ===")
    print("Type 'exit', 'quit', or 'bye' to end the conversation")
    print("bot: How can I help you today?")
    print()
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ("exit", "quit", "bye"):
            print("bot: Goodbye!")
            break
        print("Vedya: ", end='')
        response = generate_reply(user_input)
        print(response)
        if response == "Thank you for using our service. Feel free to reach out if you need any help in the future!":
            break
        print()
