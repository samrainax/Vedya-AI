class TwilioMock:
    """Mock implementation of Twilio's WhatsApp API for testing purposes"""
    
    def __init__(self):
        self.sent_messages = []
        self.received_messages = []
        self.callbacks = {}
    
    def send_message(self, to, body, media_url=None):
        """Mock sending a message to a WhatsApp number"""
        message = {
            'to': to,
            'body': body,
            'media_url': media_url,
            'sid': f'mock_message_{len(self.sent_messages) + 1}'
        }
        self.sent_messages.append(message)
        return message
    
    def simulate_incoming_message(self, from_number, body, media_url=None):
        """Simulate receiving a message from a WhatsApp number"""
        message = {
            'From': from_number,
            'Body': body,
            'MediaUrl': media_url,
            'SmsMessageSid': f'mock_incoming_{len(self.received_messages) + 1}'
        }
        self.received_messages.append(message)
        
        # If there's a callback registered for this number, call it
        if from_number in self.callbacks:
            self.callbacks[from_number](message)
        
        return message
    
    def register_callback(self, phone_number, callback_function):
        """Register a callback function to be called when a message is received from a specific number"""
        self.callbacks[phone_number] = callback_function
    
    def clear_history(self):
        """Clear the message history"""
        self.sent_messages = []
        self.received_messages = []
    
    def get_conversation_history(self, phone_number):
        """Get the conversation history with a specific phone number"""
        conversation = []
        
        # Add sent messages to this number
        for msg in self.sent_messages:
            if msg['to'] == phone_number:
                conversation.append({
                    'direction': 'outbound',
                    'body': msg['body'],
                    'media_url': msg['media_url'],
                    'timestamp': 'mock_timestamp'
                })
        
        # Add received messages from this number
        for msg in self.received_messages:
            if msg['From'] == phone_number:
                conversation.append({
                    'direction': 'inbound',
                    'body': msg['Body'],
                    'media_url': msg['MediaUrl'],
                    'timestamp': 'mock_timestamp'
                })
        
        # Sort by mock timestamp (in a real implementation, we would sort by actual timestamp)
        return conversation
