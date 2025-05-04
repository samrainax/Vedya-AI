from openai import OpenAI
import os

users_state = {}

kb_categoriser = '''General Medicine, Orthopedics, Cardiology'''

users_state = 0

# Get API key from environment variable, with fallback to hardcoded value for backward compatibility
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

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

def parse_llm_response(response_text):
    try:
        import json
        # Clean the response text to ensure proper JSON format
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text[response_text.find('{'):response_text.rfind('}')+1]
        
        # Handle nested JSON responses
        if '```' in response_text:
            # Extract the inner JSON
            inner_json = response_text[response_text.find('{'):response_text.rfind('}')+1]
            try:
                parsed = json.loads(inner_json)
            except json.JSONDecodeError:
                # If inner JSON fails, try the whole response
                parsed = json.loads(response_text)
        else:
            parsed = json.loads(response_text)
        
        # Convert string "null" to actual None
        for key in parsed:
            if parsed[key] == "null":
                parsed[key] = None
        
        # Ensure bot_response is never empty
        if not parsed.get("bot_response"):
            parsed["bot_response"] = "I'll help you with that. Let me find the right doctor for you."
        
        return parsed
    except json.JSONDecodeError:
        return {"bot_response": response_text, "category": None, "doctor": None, "slot": None}

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
    
    Return the information in this JSON format:
    {
        "name": "patient name",
        "number": "phone number"
        "concern": "concern in brief"
    }
    '''

    messages.insert(0, {"role": "system", "content": prompt})
    
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=messages,
        temperature=0.3,
        max_completion_tokens=1024,
        top_p=1.0,
        stream=True,
        stop=None,
    )

    response_chunks = []
    for chunk in completion:
        delta = chunk.choices[0].delta.content or ""
        response_chunks.append(delta)
    
    response_text = "".join(response_chunks)
    
    try:
        import json
        return json.loads(response_text)
    except json.JSONDecodeError:
        return {"name": "Unknown", "number": "0000000000"}

def create_appointment_object(patient_name, patient_number, doctor_name, appointment_date, appointment_time, patient_concern):
    """Create an appointment object with the given details"""
    # Generate a unique appointment ID (in production, this would come from a database)
    appointment_id = str(len(open('Backend/appointments.json').readlines()) + 1)
    
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
        # Read existing appointments
        with open('Backend/appointments.json', 'r') as file:
            appointments = json.load(file)
        
        # Append new appointment
        appointments.append(appointment)
        
        # Write back to file
        with open('Backend/appointments.json', 'w') as file:
            json.dump(appointments, file, indent=4)
        
        return True
    except Exception as e:
        print(f"Error saving appointment: {str(e)}")
        return False


def generate_reply(incoming_msg, phone_number=""):
    global curr_category, curr_doctor, selected_slot, selected_date
    prompt = ""

    print(f"\n[DEBUG] Current State: {users_state.get(phone_number, 0)}")
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
    if users_state.get(phone_number, 0) == 0:
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

        Conversation history:
        {generate_reply.conversation_history[-4:] if hasattr(generate_reply, 'conversation_history') else "No history"}

        Current booking status:
        - Category: {curr_category if curr_category else "None"}
        - Doctor: {curr_doctor if curr_doctor else "None"}
        - Date: {selected_date if selected_date else "None"}
        - Slot: {selected_slot if selected_slot else "None"}

        Give your response in this format (as a valid JSON object):
        {{
            "bot_response": "your friendly response",
            "next_state": 1 or 2 or 3 or null,
            "special_action": "cancel" or "modify" or "show" or "help" or "reset" or "exit" or null,
            "needs_context": true or false,
            "is_general_conversation": true or false
        }}

        Important:
        - Keep the conversation natural and friendly
        - Set "next_state" to 1 IMMEDIATELY when user mentions ANY health issue, including:
          * Physical symptoms (pain, discomfort, illness)
          * Mental health concerns
          * General health questions
          * Medical conditions
          * Health-related complaints
        - Set "is_general_conversation" to true for:
          * Casual greetings and small talk
          * General questions about the hospital
          * Simple acknowledgments (ok, thanks, etc.)
          * Follow-up questions
          * Any response that doesn't mention health issues
        - Only set "next_state" to 2 or 3 when user has already selected a category/doctor
        - For general conversation without health issues, keep "next_state" as null
        - If special action is needed, set "special_action" accordingly
        - If more context is needed, set "needs_context" to true
        '''
        messages[0]["content"] = prompt

        # Send to LLM for analysis
        messages.append({"role": "user", "content": incoming_msg})
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            temperature=0.3,
            max_completion_tokens=1024,
            top_p=1.0,
            stream=True,
            stop=None,
        )

        response_chunks = []
        print("\n[DEBUG] LLM Response:")
        for chunk in completion:
            delta = chunk.choices[0].delta.content or ""
            print(delta, end="", flush=True)
            response_chunks.append(delta)
        print()

        response_text = "".join(response_chunks)
        messages.append({"role": "assistant", "content": response_text})
        
        # Update conversation history
        generate_reply.conversation_history.extend([
            {"role": "user", "content": incoming_msg},
            {"role": "assistant", "content": response_text}
        ])

        # Parse moderator response
        parsed_response = parse_llm_response(response_text)
        
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
                users_state[phone_number] = 1
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
        if parsed_response.get("next_state"):
            users_state[phone_number] = parsed_response["next_state"]
            print(f"[DEBUG] Moderator routing to State {users_state[phone_number]}")
            return parsed_response["bot_response"]
        
        # If needs more context
        if parsed_response.get("needs_context", False):
            return parsed_response["bot_response"]
        
        # Default response - stay in general conversation
        return parsed_response["bot_response"]

    elif users_state.get(phone_number, 0) == 1:
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

        Categories:
        - General Medicine: For general health issues, stomach problems, fever, etc.
        - Orthopedics: For bone, joint, or muscle pain
        - Cardiology: For heart-related issues

        Give your response in this format (as a valid JSON object):
        {{
            "bot_response": "your response (never leave empty)",
            "category": "General Medicine" or "Orthopedics" or "Cardiology" or null,
            "needs_more_info": true or false,
            "wants_recommendation": true or false or null
        }}

        Important: 
        - After one follow-up question, always set "needs_more_info" to false and provide a category
        - After classification, ask if they want doctor recommendations
        - Set "wants_recommendation" to true if they want recommendations, false if they don't, null if not asked yet
        '''
        messages[0]["content"] = prompt

        # Send to LLM for analysis
        messages.append({"role": "user", "content": incoming_msg})
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=messages,
            temperature=0.3,
            max_completion_tokens=1024,
            top_p=1.0,
            stream=True,
            stop=None,
        )

        response_chunks = []
        print("\n[DEBUG] LLM Response:")
        for chunk in completion:
            delta = chunk.choices[0].delta.content or ""
            print(delta, end="", flush=True)
            response_chunks.append(delta)
        print()

        response_text = "".join(response_chunks)
        messages.append({"role": "assistant", "content": response_text})
        
        # Update conversation history
        generate_reply.conversation_history.extend([
            {"role": "user", "content": incoming_msg},
            {"role": "assistant", "content": response_text}
        ])

        # Parse moderator response
        parsed_response = parse_llm_response(response_text)
        
        # Handle category-related logic if we're in State 1
        if "category" in parsed_response and (parsed_response["category"] is not None and 
            parsed_response["category"] in hospital_doctors and 
            not parsed_response.get("needs_more_info", True)):
            
            if parsed_response.get("wants_recommendation") is False:
                print("\n[STATE TRANSITION] User doesn't want recommendations")
                users_state[phone_number] = 0  # Return to moderator
                curr_category = ""  # Reset category
                return "Thank you for using our service. Feel free to reach out if you need any help in the future!"
            
            if parsed_response.get("wants_recommendation") is True:
                print(f"\n[STATE TRANSITION] Category identified: {parsed_response['category']}")
                curr_category = parsed_response["category"]
                users_state[phone_number] = 2
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

    elif users_state.get(phone_number, 0) == 2:
        print(f"\n[STATE 2] Fetching doctors for category: {curr_category}")
        list_of_docs = fetch_recommendations(curr_category)
        print(f"[DEBUG] Available doctors: {list_of_docs}")
        
        # Format doctors list
        doctors_list = "\n".join([f"{i+1}. {doc['name']} - {doc['qualification']} ({doc['experience_years']} years experience)" 
                                for i, doc in enumerate(list_of_docs)])
        
        # Check if user mentioned a doctor's name using flexible matching
        selected_doctor = extract_doctor_name(incoming_msg, list_of_docs)
        if selected_doctor:
            print(f"\n[STATE TRANSITION] Doctor selected: {selected_doctor}")
            curr_doctor = selected_doctor
            users_state[phone_number] = 3
            print("[DEBUG] Moving to State 3: Slot Selection")
            # Show available dates immediately after doctor confirmation
            available_dates = list(doctor_available_slots[curr_doctor].keys())
            dates_list = "\n".join([f"{i+1}. {date}" for i, date in enumerate(available_dates)])
            return f"Great! Here are the available dates for Dr. {curr_doctor.split('Dr. ')[1]}:\n{dates_list}\nPlease let me know which date you prefer."
        
        prompt = f'''You are Vedya, you need to help the user choose a doctor from these options: 
        Available doctors in {curr_category}:
        {list_of_docs}

        Your task is to:
        1. Present ONLY these specific doctors with their qualifications
        2. Ask the user to choose one from these exact doctors
        3. Wait for their selection
        4. Only after they select a doctor, ask if they want to book an appointment

        Give your response in this format (as a valid JSON object):
        {{
            "bot_response": "your response in 2-3 lines",
            "doctor": "selected doctor name if chosen else null",
            "wants_booking": true or false or null
        }}

        Important:
        - Only use the doctors listed above
        - Do not make up any other doctors
        - If user mentions a doctor's name (full or partial), set "doctor" to the full doctor name
        - Only set "wants_booking" to true/false after they select a doctor
        - DO NOT ask if they want recommendations again - they already said yes
        '''
        messages[0]["content"] = prompt

        # Add previous conversation to provide context
        if hasattr(generate_reply, 'conversation_history'):
            messages.extend(generate_reply.conversation_history[-2:])  # Add last exchange for context

    elif users_state.get(phone_number, 0) == 3:
        print(f"\n[STATE 3] Fetching slots for doctor: {curr_doctor}")
        available_slots = book_appointment(curr_doctor)
        print(f"[DEBUG] Available slots: {available_slots}")
        
        # If we don't have a selected date yet, try to extract it
        if not selected_date:
            selected_date = extract_date(incoming_msg)
            if selected_date and selected_date in doctor_available_slots[curr_doctor]:
                available_slots = doctor_available_slots[curr_doctor][selected_date]
                slots_list = "\n".join([f"{i+1}. {slot}" for i, slot in enumerate(available_slots)])
                return f"Great! Here are the available time slots for {selected_date}:\n{slots_list}\nPlease let me know which time slot you prefer."
            
            # If no date extracted, show available dates
            available_dates = list(doctor_available_slots[curr_doctor].keys())
            dates_list = "\n".join([f"{i+1}. {date}" for i, date in enumerate(available_dates)])
            return f"Here are the available dates for {curr_doctor}:\n{dates_list}\nPlease let me know which date you prefer."
        
        # If we have a selected date but no slot, try to extract the slot
        if selected_date and not selected_slot:
            selected_slot = extract_time_slot(incoming_msg, doctor_available_slots[curr_doctor][selected_date])
            if selected_slot:
                print(f"\n[STATE TRANSITION] Slot selected: {selected_slot} on {selected_date}")

                patient_info = extract_patient_info(messages)

                appointment = create_appointment_object(
                    patient_name=patient_info.get("name", "Unknown"),
                    patient_number=patient_info.get("number", "0000000000"),
                    doctor_name=curr_doctor,
                    appointment_date=selected_date,
                    appointment_time=selected_slot,
                    patient_concern=patient_info.get("concern", curr_category)
                )

                if append_appointment_to_json(appointment):
                    print(f"[DEBUG] Appointment saved to appointments.json: {appointment}")

                print("[DEBUG] Moving back to State 0: Moderator")
                return f"Appointment booked with {curr_doctor} on {selected_date} at {selected_slot}"
            
            # If no slot extracted, show available slots again
            available_slots = doctor_available_slots[curr_doctor][selected_date]
            slots_list = "\n".join([f"{i+1}. {slot}" for i, slot in enumerate(available_slots)])

            # Reset all booking-related variables
            curr_category = ""
            curr_doctor = ""
            selected_date = ""
            selected_slot = ""
            users_state[phone_number] = 0  # Return to moderator
            return f"Here are the available time slots for {selected_date}:\n{slots_list}\nPlease let me know which time slot you prefer."

    print("\n[DEBUG] Sending message to LLM...")
    messages.append({"role": "user", "content": incoming_msg})
    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=messages,
        temperature=0.3,
        max_completion_tokens=1024,
        top_p=1.0,
        stream=True,
        stop=None,
    )

    response_chunks = []
    print("\n[DEBUG] LLM Response:")
    for chunk in completion:
        delta = chunk.choices[0].delta.content or ""
        print(delta, end="", flush=True)
        response_chunks.append(delta)
    print()

    response_text = "".join(response_chunks)
    messages.append({"role": "assistant", "content": response_text})
    
    # Update conversation history
    generate_reply.conversation_history.extend([
        {"role": "user", "content": incoming_msg},
        {"role": "assistant", "content": response_text}
    ])

    print("\n[DEBUG] Parsing LLM response...")
    parsed_response = parse_llm_response(response_text)
    print(f"[DEBUG] Parsed response: {parsed_response}")

    # if users_state == 1:
    #     # Only process category-related logic if we're in State 1
    #     if "category" in parsed_response and (parsed_response["category"] is not None and 
    #         parsed_response["category"] in hospital_doctors and 
    #         not parsed_response.get("needs_more_info", True)):
            
    #         if parsed_response.get("wants_recommendation") is False:
    #             print("\n[STATE TRANSITION] User doesn't want recommendations")
    #             users_state = 0  # Return to moderator
    #             curr_category = ""  # Reset category
    #             return "Thank you for using our service. Feel free to reach out if you need any help in the future!"
            
    #         if parsed_response.get("wants_recommendation") is True:
    #             print(f"\n[STATE TRANSITION] Category identified: {parsed_response['category']}")
    #             curr_category = parsed_response["category"]
    #             users_state = 2
    #             print("[DEBUG] Moving to State 2: Doctor Selection")
    #             # Return the doctor list directly
    #             list_of_docs = fetch_recommendations(curr_category)
    #             doctors_list = "\n".join([f"{i+1}. {doc['name']} - {doc['qualification']} ({doc['experience_years']} years experience)" 
    #                                     for i, doc in enumerate(list_of_docs)])
    #             return f"Here are our {curr_category} specialists:\n{doctors_list}\nPlease let me know which doctor you would like to consult."
            
    #         # If wants_recommendation is null, ask if they want recommendations
    #         return f"I've classified your concern under {parsed_response['category']}. Would you like me to recommend a doctor for your {parsed_response['category']} concern?"
        
    #     # For non-category related responses in State 1, return the bot response
    #     return parsed_response["bot_response"]

    # elif users_state == 2:
    #     # Check if user mentioned a doctor's name using flexible matching
    #     selected_doctor = extract_doctor_name(incoming_msg, fetch_recommendations(curr_category))
    #     if selected_doctor:
    #         print(f"\n[STATE TRANSITION] Doctor selected: {selected_doctor}")
    #         curr_doctor = selected_doctor
    #         users_state = 3
    #         print("[DEBUG] Moving to State 3: Slot Selection")
    #         # Show available dates immediately after doctor confirmation
    #         available_dates = list(doctor_available_slots[curr_doctor].keys())
    #         dates_list = "\n".join([f"{i+1}. {date}" for i, date in enumerate(available_dates)])
    #         return f"Great! Here are the available dates for Dr. {curr_doctor.split('Dr. ')[1]}:\n{dates_list}\nPlease let me know which date you prefer."
            
    #     if parsed_response["doctor"] is not None and parsed_response["doctor"] in doctor_available_slots:
    #         if parsed_response.get("wants_booking") is False:
    #             print("\n[STATE TRANSITION] User doesn't want to book appointment")
    #             users_state = 0  # Return to moderator
    #             curr_category = ""  # Reset category
    #             curr_doctor = ""    # Reset doctor
    #             return "Thank you for using our service. Feel free to reach out if you need any help in the future!"
                
    #         if parsed_response.get("wants_booking") is True:
    #             print(f"\n[STATE TRANSITION] Doctor selected: {parsed_response['doctor']}")
    #             curr_doctor = parsed_response["doctor"]
    #             users_state = 3
    #             print("[DEBUG] Moving to State 3: Slot Selection")
    #             # Show available dates immediately after doctor confirmation
    #             available_dates = list(doctor_available_slots[curr_doctor].keys())
    #             dates_list = "\n".join([f"{i+1}. {date}" for i, date in enumerate(available_dates)])
    #             return f"Great! Here are the available dates for Dr. {curr_doctor.split('Dr. ')[1]}:\n{dates_list}\nPlease let me know which date you prefer."
            
    #         # If wants_booking is null, ask if they want to book
    #         return parsed_response["bot_response"]
            
    # elif users_state == 3:
    #     # Handle date selection
    #     if "21st" in incoming_msg.lower() or "21" in incoming_msg:
    #         selected_date = "2024-03-21"
    #         available_slots = doctor_available_slots[curr_doctor][selected_date]
    #         slots_list = "\n".join([f"{i+1}. {slot}" for i, slot in enumerate(available_slots)])
    #         return f"Here are the available time slots for {selected_date}:\n{slots_list}\nPlease let me know which time slot you prefer."
        
    #     # Handle time slot selection
    #     if parsed_response.get("date") is not None and parsed_response["date"] in doctor_available_slots[curr_doctor]:
    #         available_slots = doctor_available_slots[curr_doctor][parsed_response["date"]]
    #         selected_slot = extract_time_slot(incoming_msg, available_slots)
            
    #         if selected_slot:
    #             print(f"\n[STATE TRANSITION] Slot selected: {selected_slot} on {parsed_response['date']}")
    #             # Reset all booking-related variables
    #             curr_category = ""
    #             curr_doctor = ""
    #             selected_date = ""
    #             selected_slot = ""
    #             users_state = 0  # Return to moderator
    #             print("[DEBUG] Moving back to State 0: Moderator")
    #             return f"Appointment booked with {curr_doctor} on {parsed_response['date']} at {selected_slot}"
            
    #         # If no time slot selected yet, show available slots
    #         slots_list = "\n".join([f"{i+1}. {slot}" for i, slot in enumerate(available_slots)])
    #         return f"Here are the available time slots for {parsed_response['date']}:\n{slots_list}\nPlease let me know which time slot you prefer."

    #     # If no date selected yet, show available dates
    #     available_dates = list(doctor_available_slots[curr_doctor].keys())
    #     dates_list = "\n".join([f"{i+1}. {date}" for i, date in enumerate(available_dates)])
    #     return f"Here are the available dates for {curr_doctor}:\n{dates_list}\nPlease let me know which date you prefer."

    return parsed_response["bot_response"]

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
