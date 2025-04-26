# Vedya-AI

A WhatsApp-based healthcare platform connecting rural patients with doctors.

## Overview

Vedya-AI is a platform that uses WhatsApp as the primary interface to connect patients with limited internet access to appropriate healthcare providers. The system uses AI agents to understand patient needs, collect information, and match them with suitable doctors.

## Components

- **Patient Interface**: WhatsApp integration with AI agent
- **Doctor Interface**: Web/mobile dashboard with AI agent support
- **Core Services**: Database, matching service, notification service, calendar service
- **AI Framework**: LangChain/LangGraph implementation for intelligent agents

## Technology Stack

- **Backend**: Django
- **Frontend**: React
- **Database**: MongoDB
- **LLM**: Meta's Llama model
- **WhatsApp API**: Twilio

## Project Structure

- `AI/`: Contains AI agents, models, tools, and utility functions
- `Backend/`: Django backend services
- `Frontend/`: React dashboard application

## Setup Instructions

### Prerequisites

- Python 3.x
- Node.js and npm
- MongoDB
- Git

### Backend Setup

1. Create and activate a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   cd Backend
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the Backend directory with the following variables:
   ```
   SECRET_KEY=your_django_secret_key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # MongoDB connection
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_NAME=vedya
   
   # Twilio credentials
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   
   # LLM settings
   LLAMA_MODEL_PATH=models/llama-2-7b
   ```

4. Run migrations and start the server:
   ```
   cd vedya
   python manage.py migrate
   python manage.py runserver
   ```

### Frontend Setup

1. Install dependencies:
   ```
   cd Frontend
   npm install
   ```

2. Start the development server:
   ```
   npm start
   ```

3. The frontend will be available at http://localhost:3000

### AI Components Setup

1. Install the necessary AI dependencies (these are included in the Backend requirements.txt):
   ```
   pip install langchain langchain-core langchaingraph
   ```

2. Download the Llama model files (if using locally):
   - Follow Meta's instructions to obtain the Llama model weights
   - Place them in a directory specified in your .env file

## Running the Application

1. Start the backend server:
   ```
   cd Backend/vedya
   python manage.py runserver
   ```

2. Start the frontend development server:
   ```
   cd Frontend
   npm start
   ```

3. Access the doctor dashboard at http://localhost:3000
   - Default login credentials:
     - Email: doctor@example.com
     - Password: password

## License

This project is licensed under the MIT License - see the LICENSE file for details.