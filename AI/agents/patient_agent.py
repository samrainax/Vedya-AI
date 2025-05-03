from groq import Groq
import os
from dotenv import load_dotenv
from patient_prompts import get_prompt_for_state
import json

# Load environment variables from .env file in Vedya AI folder
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

# Get API key from environment variables
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

class DoctorDB():
    def __init__(self):
        self.doctor_categories = ["General Medicine", "Orthopedics", "Cardiology"]
        self.hospital_doctors = {
            "General Medicine": [
                {"id": "GM001", "name": "Dr. Anil Kumar", "qualification": "MBBS, MD (General Medicine)", "experience_years": 12, "phone": "+91 98765 43210"},
                {"id": "GM002", "name": "Dr. Sneha Rathi", "qualification": "MBBS, DNB (Internal Medicine)", "experience_years": 8, "phone": "+91 98765 43211"}
            ],
            "Orthopedics": [
                {"id": "OR001", "name": "Dr. Ramesh Yadav", "qualification": "MBBS, MS (Orthopedics)", "experience_years": 10, "phone": "+91 98765 43212"},
                {"id": "OR002", "name": "Dr. Priya Mehra", "qualification": "MBBS, Diploma in Orthopedics", "experience_years": 6, "phone": "+91 98765 43213"},
                {"id": "OR003", "name": "Dr. Arvind Sharma", "qualification": "MBBS, MS (Ortho)", "experience_years": 15, "phone": "+91 98765 43214"}
            ],
            "Cardiology": [
                {"id": "CA001", "name": "Dr. Neeraj Sinha", "qualification": "MBBS, MD, DM (Cardiology)", "experience_years": 14, "phone": "+91 98765 43215"},
                {"id": "CA002", "name": "Dr. Pooja Bansal", "qualification": "MBBS, MD (Medicine), Fellowship in Cardiology", "experience_years": 9, "phone": "+91 98765 43216"}
            ]
        }
        self.doctor_available_slots = {
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

class PatientAgent:
    def __init__(self):
        self.state = -1
        self.current_category = ""
        self.wants_recommendations = False
        self.current_doctor = ""
        self.selected_date = ""
        self.selected_slot = ""
        self.messages = []
        self.doctor_db = DoctorDB()
    
    def _parse_json_response(self, response):
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"bot response": response, "next_state": None}
    
    def _detect_state_change(self, new_state):
        if new_state != self.state:
            self.state = new_state
            return True
        return False
        
    def run_patient_agent(self):
        while True:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                print("Exiting the conversation...")
                break
            
            if self.state == 0:
                message = self.converse(user_input)
                print(f"AI: {message}")

            elif self.state == 1:
                message = self.categorize(user_input)
                parsed_message = self._parse_json_response(message)
                if parsed_message.get("wants_recommendations").lower() == 'yes':
                    self.state = 2
                    self.current_category = parsed_message.get("category")
                    self.messages.append({"role": "system", "content": get_prompt_for_state(self.state).format()})
                elif parsed_message.get("wants_recommendations").lower() == 'no':
                    self.state = 0
                    self.messages.append({"role": "system", "content": get_prompt_for_state(self.state).format(current_state=self.state, current_category=self.current_category, 
                                                                current_doctor=self.current_doctor, selected_date=self.selected_date, 
                                                                selected_slot=self.selected_slot)})
                    self.current_category = parsed_message.get("category")
                print(f"AI: {parsed_message}")

    def recommed_doctors(self, user_input):
        self.messages.append({"role": "user", "content": user_input})

        response = self.client.chat.completions.create(
            model = "meta-llama/llama-4-scout-17b-16e-instruct",
            messages = self.messages,
            temperature = 0.2,
            max_tokens = 1024,
            top_p = 1,
            stream = False,
            stop = None,
        )

        message = response.choices[0].message.content.strip()
        self.messages.append({"role": "assistant", "content": message})
        return message

    def categorize(self, user_input):
        self.messages.append({"role": "user", "content": user_input})

        response = self.client.chat.completions.create(
            model = "meta-llama/llama-4-scout-17b-16e-instruct",
            messages = self.messages,
            temperature = 0.2,
            max_tokens = 1024,
            top_p = 1,
            stream = False,
            stop = None,
        )

        message = response.choices[0].message.content.strip()
        self.messages.append({"role": "assistant", "content": message})
        return message
    
    def converse(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model = "meta-llama/llama-4-scout-17b-16e-instruct",
            messages = self.messages,
            temperature = 0.2,
            max_tokens = 1024,
            top_p = 1,
            stream = False,
            stop = None,
        )

        message = response.choices[0].message.content.strip()
        parsed_message = self._parse_json_response(message)
        if self._detect_state_change(parsed_message):
            return parsed_message
        self.messages.append({"role": "assistant", "content": message})
        return parsed_message
    
if __name__ == "__main__":
    patient_agent = PatientAgent()
    patient_agent.run_patient_agent()
