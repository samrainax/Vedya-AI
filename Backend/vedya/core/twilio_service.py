import os
from twilio.rest import Client
from django.conf import settings

class TwilioService:
    """Service for interacting with Twilio's WhatsApp API"""
    
    def __init__(self):
        # Initialize Twilio client with credentials from settings
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.whatsapp_number = settings.TWILIO_PHONE_NUMBER
        
        # Initialize client
        self.client = Client(self.account_sid, self.auth_token)
    
    def send_whatsapp_message(self, to_number, message, media_url=None):
        """Send a WhatsApp message via Twilio"""
        # Format the 'to' number for WhatsApp
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
        
        # Format the 'from' number for WhatsApp
        from_number = f'whatsapp:{self.whatsapp_number}'
        
        # Send the message
        message_params = {
            'body': message,
            'from_': from_number,
            'to': to_number
        }
        
        # Add media URL if provided
        if media_url:
            message_params['media_url'] = [media_url]
        
        # Send the message and return the SID
        sent_message = self.client.messages.create(**message_params)
        return sent_message.sid
    
    def get_media_content(self, media_sid):
        """Retrieve media content from a message"""
        media = self.client.messages(media_sid).media.list()[0]
        return media.uri
