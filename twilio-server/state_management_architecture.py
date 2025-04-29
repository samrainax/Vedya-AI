import os
import json

users_state = {}  # Dictionary to track state per phone number

kb_categoriser = '''General Medicine, Orthopedics, Cardiology'''

from groq import Groq

GROQ_API_KEY = "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"

client = Groq(api_key=GROQ_API_KEY)

def load_doctor_data():
    base_path = os.path.join(os.path.dirname(__file__), '../db/doctors')
    doctor_files = ['general_medicine.json', 'orthopedics.json', 'cardiology.json']
    hospital_doctors = {}

    for file_name in doctor_files:
        category = file_name.split('.')[0].replace('_', ' ').title()
        file_path = os.path.join(base_path, file_name)
        with open(file_path, 'r') as file:
            doctors = json.load(file)
            hospital_doctors[category] = doctors

    return hospital_doctors

# Load data dynamically
hospital_doctors = load_doctor_data()

curr_category = ""
curr_doctor = ""
selected_slot = ""
selected_date = ""

def fetch_recommendations(curr_category):
    return hospital_doctors[curr_category]

def update_doctor_appointment(doctor_name, phone_number, date):
    base_path = os.path.join(os.path.dirname(__file__), '../db/doctors')
    doctor_files = ['general_medicine.json', 'orthopedics.json', 'cardiology.json']

    for file_name in doctor_files:
        file_path = os.path.join(base_path, file_name)
        with open(file_path, 'r') as file:
            doctors = json.load(file)

        for doctor in doctors:
            if doctor['name'] == doctor_name:
                doctor['booked_appointments'].append({
                    'with': phone_number,
                    'date': date
                })
                with open(file_path, 'w') as file:
                    json.dump(doctors, file, indent=4)
                return

def book_appointment(curr_doctor):
    for category, doctors in hospital_doctors.items():
        for doctor in doctors:
            if doctor['name'] == curr_doctor:
                return doctor['slots']

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

def generate_reply(incoming_msg, phone_number=""):
    global users_state, curr_category, curr_doctor, selected_slot, selected_date
    prompt = ""
    print(f"\n[DEBUG] Current State for {phone_number}: {users_state[phone_number]}")
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

    if users_state[phone_number] == 1:
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

    elif users_state[phone_number] == 2:
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
            available_dates = list(book_appointment(curr_doctor).keys())
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

    elif users_state[phone_number] == 3:
        print(f"\n[STATE 3] Fetching slots for doctor: {curr_doctor}")
        available_slots = book_appointment(curr_doctor)
        print(f"[DEBUG] Available slots: {available_slots}")
        
        # If we don't have a selected date yet, try to extract it
        if not selected_date:
            selected_date = extract_date(incoming_msg)
            if selected_date and selected_date in book_appointment(curr_doctor):
                available_slots = book_appointment(curr_doctor)[selected_date]
                slots_list = "\n".join([f"{i+1}. {slot}" for i, slot in enumerate(available_slots)])
                return f"Great! Here are the available time slots for {selected_date}:\n{slots_list}\nPlease let me know which time slot you prefer."
            
            # If no date extracted, show available dates
            available_dates = list(book_appointment(curr_doctor).keys())
            dates_list = "\n".join([f"{i+1}. {date}" for i, date in enumerate(available_dates)])
            return f"Here are the available dates for {curr_doctor}:\n{dates_list}\nPlease let me know which date you prefer."
        
        # If we have a selected date but no slot, try to extract the slot
        if selected_date and not selected_slot:
            selected_slot = extract_time_slot(incoming_msg, book_appointment(curr_doctor)[selected_date])
            if selected_slot:
                print(f"\n[STATE TRANSITION] Slot selected: {selected_slot} on {selected_date}")
                users_state[phone_number] = 1  # Reset state for next booking
                print("[DEBUG] Moving back to State 1: Category Selection")
                return f"Appointment booked with {curr_doctor} on {selected_date} at {selected_slot}"
            
            # If no slot extracted, show available slots again
            available_slots = book_appointment(curr_doctor)[selected_date]
            slots_list = "\n".join([f"{i+1}. {slot}" for i, slot in enumerate(available_slots)])
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

    if users_state[phone_number] == 1:
        if (parsed_response["category"] is not None and 
            parsed_response["category"] in hospital_doctors and 
            not parsed_response.get("needs_more_info", True)):
            
            if parsed_response.get("wants_recommendation") is False:
                print("\n[STATE TRANSITION] User doesn't want recommendations")
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
            
    elif users_state[phone_number] == 2:
        # Check if user mentioned a doctor's name using flexible matching
        selected_doctor = extract_doctor_name(incoming_msg, fetch_recommendations(curr_category))
        if selected_doctor:
            print(f"\n[STATE TRANSITION] Doctor selected: {selected_doctor}")
            curr_doctor = selected_doctor
            users_state[phone_number] = 3
            print("[DEBUG] Moving to State 3: Slot Selection")
            # Show available dates immediately after doctor confirmation
            available_dates = list(book_appointment(curr_doctor).keys())
            dates_list = "\n".join([f"{i+1}. {date}" for i, date in enumerate(available_dates)])
            return f"Great! Here are the available dates for Dr. {curr_doctor.split('Dr. ')[1]}:\n{dates_list}\nPlease let me know which date you prefer."
            
        if parsed_response["doctor"] is not None and parsed_response["doctor"] in book_appointment(curr_doctor):
            if parsed_response.get("wants_booking") is False:
                print("\n[STATE TRANSITION] User doesn't want to book appointment")
                return "Thank you for using our service. Feel free to reach out if you need any help in the future!"
                
            if parsed_response.get("wants_booking") is True:
                print(f"\n[STATE TRANSITION] Doctor selected: {parsed_response['doctor']}")
                curr_doctor = parsed_response["doctor"]
                users_state[phone_number] = 3
                print("[DEBUG] Moving to State 3: Slot Selection")
                # Show available dates immediately after doctor confirmation
                available_dates = list(book_appointment(curr_doctor).keys())
                dates_list = "\n".join([f"{i+1}. {date}" for i, date in enumerate(available_dates)])
                return f"Great! Here are the available dates for Dr. {curr_doctor.split('Dr. ')[1]}:\n{dates_list}\nPlease let me know which date you prefer."
            
            # If wants_booking is null, ask if they want to book
            return parsed_response["bot_response"]
            
    elif users_state[phone_number] == 3:
        # Handle date selection
        if "21st" in incoming_msg.lower() or "21" in incoming_msg:
            selected_date = "2024-03-21"
            available_slots = book_appointment(curr_doctor)[selected_date]
            slots_list = "\n".join([f"{i+1}. {slot}" for i, slot in enumerate(available_slots)])
            return f"Here are the available time slots for {selected_date}:\n{slots_list}\nPlease let me know which time slot you prefer."
        
        # Handle time slot selection
        if parsed_response.get("date") is not None and parsed_response["date"] in book_appointment(curr_doctor):
            available_slots = book_appointment(curr_doctor)[parsed_response["date"]]
            selected_slot = extract_time_slot(incoming_msg, available_slots)
            
            if selected_slot:
                print(f"\n[STATE TRANSITION] Slot selected: {selected_slot} on {parsed_response['date']}")
                users_state[phone_number] = 1  # Reset state for next booking
                print("[DEBUG] Moving back to State 1: Category Selection")
                update_doctor_appointment(curr_doctor, phone_number, parsed_response["date"])
                return f"Appointment booked with {curr_doctor} on {parsed_response['date']} at {selected_slot}"
            
            # If no time slot selected yet, show available slots
            slots_list = "\n".join([f"{i+1}. {slot}" for i, slot in enumerate(available_slots)])
            return f"Here are the available time slots for {parsed_response['date']}:\n{slots_list}\nPlease let me know which time slot you prefer."

        # If no date selected yet, show available dates
        available_dates = list(book_appointment(curr_doctor).keys())
        dates_list = "\n".join([f"{i+1}. {date}" for i, date in enumerate(available_dates)])
        return f"Here are the available dates for {curr_doctor}:\n{dates_list}\nPlease let me know which date you prefer."

    return parsed_response["bot_response"]

if __name__ == "__main__":
    print("\n=== Hospital Appointment Booking System ===")
    print("Type 'exit', 'quit', or 'bye' to end the conversation")
    print("bot: How can I help you today?")
    print()
    while True:
        user_input = input("You: ")
        phone_number = "1234567890"  # Dummy phone number for testing
        if phone_number not in users_state:
            users_state[phone_number] = 1
        if user_input.strip().lower() in ("exit", "quit", "bye"):
            print("bot: Goodbye!")
            break
        print("Vedya: ", end='')
        response = generate_reply(user_input, phone_number)
        print(response)
        if response == "Thank you for using our service. Feel free to reach out if you need any help in the future!":
            break
        print()
