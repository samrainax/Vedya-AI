import json
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from ..healthcare_platform_test.state_management_architecture import users_state, generate_reply
app = Flask(__name__)

account_sid = 'ACb4d0869c9dc485199faf9731faf6588d'
auth_token = 'f350f80f78f42fa2964b559c2f1d96e8'
client = Client(account_sid, auth_token)


@app.route('/incoming', methods=['POST'])
def incoming_message():
    incoming_msg = request.form.get('Body')
    phone_number = request.form.get('From')
    if phone_number not in users_state:
        users_state[phone_number] = 1
    response = MessagingResponse()
    reply = generate_reply(incoming_msg, phone_number)
    response.message(reply)
    
    return str(response)

if __name__ == '__main__':
    app.run(debug=True)