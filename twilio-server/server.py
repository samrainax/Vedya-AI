import json
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

app = Flask(__name__)

account_sid = 'ACb4d0869c9dc485199faf9731faf6588d'
auth_token = 'f350f80f78f42fa2964b559c2f1d96e8'
client = Client(account_sid, auth_token)

# State management
STATE_CLASSIFY = 1
STATE_RECOMMEND = 2
STATE_BOOK = 3

# User state tracking
users_state = {}
users_data = {}  # Store current user data in memory

kb_categoriser = '''General Medicine, Orthopedics, Cardiology, Gynecology and Obstetrics, Pediatrics'''


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


curr_category=""
curr_doctor=""
def fetch_recommendations(category):
    if category in hospital_doctors:
        return hospital_doctors[category]
    return []

def book_appointment(doctor):
    if doctor in doctor_available_slots:
        return doctor_available_slots[doctor]
    return []

def generate_classification_prompt(incoming_msg):
    return f'''You are Vedya, a receptionist at a hospital. You need to understand which category of health the user's issue falls into.

User's message: {incoming_msg}

Available categories: {kb_categoriser}

Give your response strictly in this format:
{{
    "bot_response": "your response in 2-3 lines",
    "category": "category if found out else null"
}}
'''

def generate_recommendation_prompt(doctors_list):
    return f'''You are Vedya, a receptionist at a hospital. You need to recommend a doctor to the user.

Available doctors:
{json.dumps(doctors_list, indent=2)}

Give your response in a friendly manner, explaining each doctor's qualifications and experience. End with asking which doctor they would like to book an appointment with.
'''

def generate_booking_prompt(available_slots):
    return f'''You are Vedya, a receptionist at a hospital. You need to help the user book an appointment.

Available time slots:
{json.dumps(available_slots, indent=2)}

Ask the user which time slot they would prefer for their appointment.
'''

def generate_reply(incoming_msg, phone_number):
    if phone_number not in users_state:
        users_state[phone_number] = STATE_CLASSIFY
        users_data[phone_number] = {"category": None, "doctor": None}

    current_state = users_state[phone_number]
    user_data = users_data[phone_number]

    # Load or create user message history
    try:
        with open(f'users/{phone_number}.json', 'r') as f:
            message_history = json.load(f)
    except FileNotFoundError:
        message_history = {'phone_number': phone_number, 'messages': []}

    # Prepare the appropriate prompt based on state
    if current_state == STATE_CLASSIFY:
        prompt = generate_classification_prompt(incoming_msg)
    elif current_state == STATE_RECOMMEND:
        doctors = fetch_recommendations(user_data["category"])
        prompt = generate_recommendation_prompt(doctors)
    elif current_state == STATE_BOOK:
        slots = book_appointment(user_data["doctor"])
        prompt = generate_booking_prompt(slots)

    # Get response from LLM
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": incoming_msg}
    ]

    completion = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=messages,
        temperature=1.0,
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

    # Update state based on response
    if current_state == STATE_CLASSIFY:
        try:
            response_data = json.loads(response_text)
            if response_data.get("category"):
                user_data["category"] = response_data["category"]
                users_state[phone_number] = STATE_RECOMMEND
                response_text = response_data["bot_response"]
        except json.JSONDecodeError:
            pass
    elif current_state == STATE_RECOMMEND:
        # Check if user selected a doctor
        for doctor in hospital_doctors.get(user_data["category"], []):
            if doctor["name"].lower() in incoming_msg.lower():
                user_data["doctor"] = doctor["name"]
                users_state[phone_number] = STATE_BOOK
                break

    # Save message history
    message_history['messages'].append({
        'timestamp': request.form.get('Timestamp'),
        'message': incoming_msg,
        'response': response_text
    })
    
    with open(f'users/{phone_number}.json', 'w') as f:
        json.dump(message_history, f)

    return response_text

@app.route('/incoming', methods=['POST'])
def incoming_message():
    incoming_msg = request.form.get('Body')
    phone_number = request.form.get('From')
    
    response = MessagingResponse()
    reply = generate_reply(incoming_msg, phone_number)
    response.message(reply)
    
    return str(response)

if __name__ == '__main__':
    app.run(debug=True)