# Vedya AI - WhatsApp Doctor Assistant Backend

This is the backend infrastructure for Vedya AI, a WhatsApp-based personal assistant that enables doctor appointments using advanced LLM technology.

## Architecture Overview

The backend is built with the following core components:

1. **Django** - Web framework that manages HTTP requests, routes, and serves as the core server-side application
2. **MongoDB** - NoSQL database for storing conversations, user data, and appointments
3. **Twilio** - API integration for WhatsApp messaging
4. **LLaMA Model** - AI model for processing user messages and generating intelligent responses

## Project Structure

```
Backend/
├── apps/                      # Main application directory
│   ├── conversations/         # Manages conversation data and MongoDB interactions
│   │   ├── __init__.py
│   │   ├── models.py          # Defines MongoDB collections and schemas
│   │   ├── db.py              # Contains PyMongo database connection logic
│   │   └── services.py        # Business logic related to conversations
│   │
│   ├── twilio_integration/    # Handles Twilio API interactions
│   │   ├── __init__.py
│   │   ├── webhook.py         # Processes incoming messages from Twilio
│   │   ├── sender.py          # Sends messages back to users via Twilio
│   │   └── views.py           # API endpoints for doctors, patients, appointments
│   │
│   ├── llm_agent/             # Interfaces with the LLaMA model
│   │   ├── __init__.py
│   │   └── agent.py           # Core logic for interacting with the LLaMA model
│   │
│   └── shared/                # Contains shared utilities and configurations
│       ├── __init__.py
│       ├── settings.py        # Centralized settings for the project
│       └── utils.py           # Helper functions used across the project
│
├── config/                    # Project configuration
│   ├── __init__.py
│   ├── settings.py            # Django settings
│   ├── urls.py                # URL routing
│   ├── wsgi.py                # WSGI application
│   └── asgi.py                # ASGI application
│
├── manage.py                  # Django's command-line utility
├── requirements.txt           # Python dependencies
└── .env.example               # Example environment variables
```

## Setup Instructions

### Prerequisites

- Python 3.9+
- MongoDB
- Twilio account with WhatsApp sandbox access

### Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file based on `.env.example` and fill in your configuration values
4. Start the MongoDB service
5. Run the development server:
   ```
   python manage.py runserver
   ```

### Twilio WhatsApp Setup

1. Create a Twilio account and access the WhatsApp sandbox
2. Configure your Twilio webhook URL to point to:
   ```
   https://your-domain.com/api/webhook/twilio/
   ```
3. Test the integration by sending a message to your Twilio WhatsApp number

## Data Flow

1. User sends a WhatsApp message to the Twilio number
2. Twilio forwards the message to the Django webhook
3. The webhook stores the message in MongoDB and processes it with the LLM agent
4. The LLM agent generates a response and extracts any appointment-related actions
5. The response is sent back to the user via Twilio
6. If the user wants to book an appointment, the system initiates the booking flow

## API Endpoints

- `POST /api/webhook/twilio/` - Receives WhatsApp messages from Twilio
- `GET/POST /api/doctors/` - Manages doctor information
- `GET/PUT/DELETE /api/doctors/{id}/` - Manages specific doctor details
- `GET/POST /api/patients/` - Manages patient information
- `GET/PUT/DELETE /api/patients/{id}/` - Manages specific patient details
- `GET/POST /api/appointments/` - Lists and creates appointments
- `GET/PUT/DELETE /api/appointments/{id}/` - Manages specific appointments

## Environment Variables

Key environment variables that need to be configured:

- `MONGODB_URI` - MongoDB connection string
- `TWILIO_ACCOUNT_SID` - Twilio account SID
- `TWILIO_AUTH_TOKEN` - Twilio authentication token
- `TWILIO_PHONE_NUMBER` - Twilio WhatsApp-enabled phone number
- `LLAMA_MODEL_PATH` - Path to the LLaMA model

## Development

To contribute to this project:

1. Create a new branch for your feature
2. Implement and test your changes
3. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

# Notification Service

A Python service that handles appointment notifications for both patients and doctors via WhatsApp using Twilio.

## Features

- Monitor appointments and automatically create notifications
- Send notifications to both patients and doctors
- Configurable notification timing (currently 1 day before and 1 hour before appointments)
- Watch for changes in the appointments file and create new notifications accordingly
- RESTful API to access notifications

## Prerequisites

- Python 3.7+
- Twilio account with WhatsApp capabilities
- ngrok (for development)

## Installation

1. Install the required dependencies:

```bash
# For only the notification service
pip install -r requirements_notification.txt

# OR if you're running the full backend
pip install -r requirements.txt
```

2. Set up environment variables:

```bash
export TWILIO_ACCOUNT_SID=your_twilio_account_sid
export TWILIO_AUTH_TOKEN=your_twilio_auth_token
```

Alternatively, you can create a `.env` file in the Backend directory with these variables.

## Configuration

The service can be configured by modifying the following variables in `notification_service.py`:

- `NOTIFICATION_CONFIG`: Configure the timing for notifications (in seconds)
- Message templates: Customize the message templates for different notification types
- `PORT`: Change the HTTP server port (default: 8000)

## Running the Notification Service

Start the notification service with:

```bash
python notification_service.py
```

The service will:
1. Load existing notifications and appointments
2. Schedule pending notifications
3. Watch for changes in the appointments.json file
4. Start an HTTP server for API access

## Setting up ngrok for Twilio Webhooks

To receive messages from Twilio, you need to expose your service to the internet. For development, ngrok is an easy way to do this:

1. Install ngrok from [https://ngrok.com/download](https://ngrok.com/download)

2. Start ngrok on the same port as your notification service:

```bash
ngrok http 8000
```

3. Copy the HTTPS URL provided by ngrok (e.g., `https://a1b2c3d4.ngrok.io`)

4. Configure your Twilio WhatsApp sandbox:
   - Go to your [Twilio Console](https://www.twilio.com/console/sms/whatsapp/sandbox)
   - Set the "When a message comes in" webhook to your ngrok URL + `/notifications` (e.g., `https://a1b2c3d4.ngrok.io/notifications`)
   - Save your settings

## API Endpoints

- `GET /notifications`: Get all notifications
- `GET /notifications/{id}`: Get a specific notification
- `GET /appointments`: Get all appointments
- `POST /notifications`: Create a new notification
- `GET /health`: Health check endpoint

## File Structure

- `notification_service.py`: The main service
- `notifications.json`: Stores all notification data
- `appointments.json`: Stores appointment data that gets monitored
- `requirements.txt`: Main backend dependencies
- `requirements_notification.txt`: Dependencies specific to the notification service

## Updating the Server

When making changes to the notification service:

1. Stop the running service (Ctrl+C)
2. Make your changes to the code
3. Restart the service:

```bash
python notification_service.py
```

If you change the server port, remember to update your ngrok configuration as well.

## Troubleshooting

- Check the logs for detailed error messages and debugging information
- Ensure Twilio credentials are correct
- Make sure the appointment dates are in the future
- Verify that your ngrok tunnel is running and the webhook URL is correctly configured in Twilio