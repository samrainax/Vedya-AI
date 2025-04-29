import json
from flask import Flask, request
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import state_management_architecture as sma
app = Flask(__name__)

account_sid = 'ACb4d0869c9dc485199faf9731faf6588d'
auth_token = '76a0c700d98b61dd91cedc558348aacb'
client = Client(account_sid, auth_token)

@app.route('/incoming', methods=['POST'])
def incoming_message():
    incoming_msg = request.form.get('Body')
    phone_number = request.form.get('From')
    if phone_number not in sma.users_state:
        sma.users_state[phone_number] = 1
    response = MessagingResponse()
    reply = sma.generate_reply(incoming_msg, phone_number)
    response.message(reply)
    
    return str(response)

@app.route('/status', methods=['GET', 'POST'])
def status():
    print('Status callback received')
    print(request.form)
    return 'Status callback received'
    

if __name__ == '__main__':
    app.run(debug=False)