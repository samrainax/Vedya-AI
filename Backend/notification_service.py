import json
import time
import os
import uuid
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import logging
import traceback
from twilio.rest import Client
import watchdog.observers
import watchdog.events

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('notification_service')

# Configuration
NOTIFICATIONS_FILE = os.path.join(os.path.dirname(__file__), "notifications.json")
APPOINTMENTS_FILE = os.path.join(os.path.dirname(__file__), "appointments.json")
PORT = 8000
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "ACfccd00529c391c2289ad1b6c4d406fb2")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "82b8033781d6f70383fed5a42ed5119c")
TWILIO_PHONE_NUMBER = "whatsapp:+14155238886"  # Example Twilio WhatsApp number

# Notification intervals configuration (in seconds)
# You can customize these intervals by changing the values below.
# For example, to send a notification 2 days before, change "day_before" to 2 * 24 * 60 * 60
# To add a new interval (e.g., "week_before"), add a new key-value pair like:
# "week_before": 7 * 24 * 60 * 60,  # 1 week
NOTIFICATION_CONFIG = {
    "day_before": 24 * 60 * 60,  # 1 day
    "hour_before": 1,      # 1 hour (set to 1 second for testing)
}

# Notification message templates
# You can customize these templates to change the content of the messages sent to patients and doctors.
# Available placeholders:
# {patient_name} - The name of the patient
# {doctor_name} - The name of the doctor
# {appointment_time} - The time of the appointment
# {patient_concern} - The patient's medical concern
PATIENT_TEMPLATE_DAY_BEFORE = "Dear {patient_name},\n\nThis is a reminder that you have an appointment with {doctor_name} tomorrow at {appointment_time} for your concern: {patient_concern}. Please arrive 15 minutes before your scheduled time."
PATIENT_TEMPLATE_HOUR_BEFORE = "Dear {patient_name},\n\nThis is a reminder that your appointment with {doctor_name} is in one hour at {appointment_time}. We're looking forward to seeing you soon."

DOCTOR_TEMPLATE_DAY_BEFORE = "Dear {doctor_name},\n\nThis is a reminder that you have an appointment with patient {patient_name} tomorrow at {appointment_time}. The patient's concern is: {patient_concern}."
DOCTOR_TEMPLATE_HOUR_BEFORE = "Dear {doctor_name},\n\nThis is a reminder that your appointment with patient {patient_name} is in one hour at {appointment_time}."

# Output current configuration
logger.info(f"Starting notification service with:")
logger.info(f"TWILIO_ACCOUNT_SID: {TWILIO_ACCOUNT_SID[:5]}...{TWILIO_ACCOUNT_SID[-5:] if len(TWILIO_ACCOUNT_SID) > 10 else '***'}")
logger.info(f"TWILIO_PHONE_NUMBER: {TWILIO_PHONE_NUMBER}")
logger.info(f"Notifications file path: {NOTIFICATIONS_FILE}")
logger.info(f"Appointments file path: {APPOINTMENTS_FILE}")

# Scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# In-memory cache of notifications
notifications_cache = []
notification_jobs = {}

# In-memory cache of appointments
appointments_cache = []

def load_notifications():
    """Load notifications from JSON file."""
    try:
        if os.path.exists(NOTIFICATIONS_FILE):
            with open(NOTIFICATIONS_FILE, 'r') as f:
                try:
                    data = json.load(f)
                    return data
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing notifications file: {e}")
                    return []
        return []
    except Exception as e:
        logger.error(f"Error loading notifications: {e}")
        return []

def save_notifications(notifications):
    """Save notifications to JSON file."""
    try:
        with open(NOTIFICATIONS_FILE, 'w') as f:
            json.dump(notifications, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving notifications: {e}")

def load_appointments():
    """Load appointments from JSON file."""
    try:
        if os.path.exists(APPOINTMENTS_FILE):
            with open(APPOINTMENTS_FILE, 'r') as f:
                try:
                    data = json.load(f)
                    return data
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing appointments file: {e}")
                    return []
        return []
    except Exception as e:
        logger.error(f"Error loading appointments: {e}")
        return []

def parse_appointment_datetime(date_str, time_str):
    """Parse appointment date and time to a timestamp."""
    try:
        # Parse the date and time into a datetime object
        date_format = "%Y-%m-%d"
        time_format = "%I:%M %p"
        
        date_obj = datetime.strptime(date_str, date_format)
        time_obj = datetime.strptime(time_str, time_format)
        
        # Combine date and time
        appointment_datetime = datetime.combine(
            date_obj.date(),
            time_obj.time()
        )
        
        return appointment_datetime
    except Exception as e:
        logger.error(f"Error parsing appointment date and time: {e}")
        return None

def create_appointment_notifications(appointment):
    """Create notifications for a new appointment."""
    global notifications_cache
    
    appointment_id = appointment["appointmentId"]
    appointment_datetime = parse_appointment_datetime(appointment["appointmentDate"], appointment["appointmentTime"])
    
    if not appointment_datetime:
        logger.error(f"Could not create notifications for appointment {appointment_id}: Invalid date/time")
        return []
    
    new_notifications = []
    
    # Check if appointment is in the future
    now = datetime.now()
    if appointment_datetime < now:
        logger.warning(f"Appointment {appointment_id} is in the past, skipping notifications")
        return []
    
    # Create notifications for patient and doctor for day before and hour before
    for recipient_type in ["patient", "doctor"]:
        for timing_type, seconds_before in NOTIFICATION_CONFIG.items():
            notification_time = appointment_datetime - timedelta(seconds=seconds_before)
            
            logger.info(f"Notification time: {notification_time}, now: {now}, seconds before: {seconds_before}, appointment datetime: {appointment_datetime}")

            # Skip if the notification time is in the past
            if notification_time < now:
                logger.warning(f"Skipping {timing_type} notification for {recipient_type} as it's in the past")
                continue
            
            # Select the appropriate template
            if recipient_type == "patient":
                if timing_type == "day_before":
                    template = PATIENT_TEMPLATE_DAY_BEFORE
                else:
                    template = PATIENT_TEMPLATE_HOUR_BEFORE
                receiver_number = appointment["patientNumber"]
                recipient_name = appointment["patientName"]
            else:
                if timing_type == "day_before":
                    template = DOCTOR_TEMPLATE_DAY_BEFORE
                else:
                    template = DOCTOR_TEMPLATE_HOUR_BEFORE
                receiver_number = appointment["doctorNumber"]
                recipient_name = appointment["doctorName"]
            
            # Format the message
            message = template.format(
                patient_name=appointment["patientName"],
                doctor_name=appointment["doctorName"],
                appointment_time=appointment["appointmentTime"],
                patient_concern=appointment.get("patientConcern", "Not specified")
            )
            
            # Create notification object
            notification_id = str(uuid.uuid4())
            notification = {
                "id": notification_id,
                "appointmentId": appointment_id,
                "recipientType": recipient_type,
                "timingType": timing_type,
                "receiverWhatsappNumber": receiver_number,
                "message": message,
                "messagePushTimestamp": int(notification_time.timestamp()),
                "status": "scheduled",
                "createdAt": int(time.time())
            }
            
            # Add to new notifications list
            new_notifications.append(notification)
    
    # Add all new notifications to cache and save to file
    if new_notifications:
        for notification in new_notifications:
            # Check if the notification already exists
            existing = next((n for n in notifications_cache 
                           if n.get("appointmentId") == appointment_id and 
                              n.get("recipientType") == notification["recipientType"] and
                              n.get("timingType") == notification["timingType"]), None)
            
            if not existing:
                notifications_cache.append(notification)
                # Schedule the notification
                schedule_notification(notification)
            else:
                logger.info(f"Notification already exists for appointment {appointment_id}, {notification['recipientType']}, {notification['timingType']}")
        
        # Save the updated notifications to file
        save_notifications(notifications_cache)
    
    return new_notifications

def process_appointments():
    """Process appointments and create notifications for new appointments."""
    global appointments_cache
    
    # Load current appointments
    current_appointments = load_appointments()
    
    # Find new appointments by comparing with cached appointments
    existing_ids = set(app["appointmentId"] for app in appointments_cache)
    new_appointments = [app for app in current_appointments if app["appointmentId"] not in existing_ids]
    
    # Create notifications for new appointments
    for appointment in new_appointments:
        logger.info(f"Creating notifications for new appointment {appointment['appointmentId']}")
        create_appointment_notifications(appointment)
    
    # Update the cache
    appointments_cache = current_appointments

def send_notification(notification_id):
    """Send a notification via Twilio."""
    # Find notification in the cache
    notification = next((n for n in notifications_cache if n.get('id') == notification_id), None)
    
    if not notification:
        logger.error(f"Notification {notification_id} not found")
        return
    
    # Skip if already sent
    if notification.get('status') == 'sent':
        return
        
    try:
        # Log credentials being used (remove in production)
        logger.info(f"Using Twilio credentials - SID: {TWILIO_ACCOUNT_SID[:5]}...{TWILIO_ACCOUNT_SID[-5:]}")
        logger.info(f"Sending message to: {notification['receiverWhatsappNumber']}")
        
        # Create Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Format WhatsApp number correctly
        to_number = notification['receiverWhatsappNumber']
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
        
        # Send message via Twilio
        logger.info(f"Sending message from {TWILIO_PHONE_NUMBER} to {to_number}")
        message = client.messages.create(
            from_=TWILIO_PHONE_NUMBER,
            body=notification['message'],
            to=to_number
        )
        
        logger.info(f"Twilio message SID: {message.sid}")
        
        # Update status
        notification['status'] = 'sent'
        
        # Update the file
        save_notifications(notifications_cache)
        logger.info(f"Notification {notification_id} sent successfully")
    except Exception as e:
        logger.error(f"Failed to send notification {notification_id}: {str(e)}")
        error_details = str(e)
        notification['status'] = 'failed'
        notification['error'] = error_details
        save_notifications(notifications_cache)
        logger.error(f"Traceback: {traceback.format_exc()}")

def schedule_notification(notification):
    """Schedule a notification using APScheduler."""
    # Convert timestamp to datetime
    notification_time = datetime.fromtimestamp(notification['messagePushTimestamp'])
    
    # Schedule the job
    job = scheduler.add_job(
        send_notification,
        trigger=DateTrigger(run_date=notification_time),
        args=[notification['id']],
        id=f"notification_{notification['id']}"
    )
    
    notification_jobs[notification['id']] = job
    logger.info(f"Scheduled notification {notification['id']} for {notification_time}")

def initialize_service():
    """Initialize the notification service."""
    global notifications_cache
    global appointments_cache
    
    # Load notifications from file
    notifications_cache = load_notifications()
    
    # Load appointments from file
    appointments_cache = load_appointments()
    
    # Process appointments to create any missing notifications
    process_appointments()
    
    # Schedule unsent notifications
    current_time = time.time()
    logger.info(f"Loaded {len(notifications_cache)} notifications from file")
    scheduled_count = 0
    
    for notification in notifications_cache:
        if notification.get('status') == 'scheduled' and notification['messagePushTimestamp'] > current_time:
            schedule_notification(notification)
            scheduled_count += 1
        elif notification.get('status') == 'scheduled' and notification['messagePushTimestamp'] <= current_time:
            # Handle notifications that were scheduled but the service was down
            notification['status'] = 'pending'
            send_notification(notification['id'])
    
    logger.info(f"Scheduled {scheduled_count} notifications")

class AppointmentChangeHandler(watchdog.events.FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith(APPOINTMENTS_FILE):
            logger.info(f"Appointments file changed: {event.src_path}")
            process_appointments()

class NotificationHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.end_headers()
    
    def _read_json_body(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        return json.loads(post_data.decode('utf-8'))
    
    def _read_form_data(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        parsed_data = urllib.parse.parse_qs(post_data)
        # Convert from lists to single values
        return {k: v[0] if v and len(v) == 1 else v for k, v in parsed_data.items()}
    
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path.rstrip('/')  # Remove trailing slash
        
        # Get all notifications
        if path == '/notifications':
            self._set_headers()
            self.wfile.write(json.dumps(notifications_cache).encode())
            return
        
        # Get specific notification
        elif path.startswith('/notifications/') and len(path) > 14:
            notification_id = path.split('/')[-1]
            notification = next((n for n in notifications_cache if n.get('id') == notification_id), None)
            
            if notification:
                self._set_headers()
                self.wfile.write(json.dumps(notification).encode())
            else:
                self._set_headers(404)
                self.wfile.write(json.dumps({"error": "Notification not found"}).encode())
            return
        
        # Get all appointments
        elif path == '/appointments':
            self._set_headers()
            self.wfile.write(json.dumps(appointments_cache).encode())
            return
        
        # Health check
        elif path == '/health':
            self._set_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            return
        
        # Default - not found
        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Not found", "path": path}).encode())
    
    def do_POST(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path.rstrip('/')  # Remove trailing slash
        
        logger.info(f"POST request to path: {path}")
        logger.info(f"Headers: {self.headers}")
        
        # Handle notifications endpoint
        if path == '/notifications':
            try:
                # Check content type to determine how to parse the body
                content_type = self.headers.get('Content-Type', '')
                logger.info(f"Content-Type: {content_type}")
                
                if 'application/json' in content_type:
                    post_data = self._read_json_body()
                    logger.info(f"Received JSON data: {post_data}")
                elif 'application/x-www-form-urlencoded' in content_type:
                    # This handles Twilio webhook format
                    post_data = self._read_form_data()
                    logger.info(f"Received form data: {post_data}")
                    
                    # For Twilio webhooks, create a notification that will be sent immediately
                    if 'Body' in post_data and 'From' in post_data:
                        # Extract the phone number from the "From" field
                        from_number = post_data['From']
                        if from_number.startswith('whatsapp:'):
                            from_number = from_number[9:]  # Remove 'whatsapp:' prefix
                        
                        logger.info(f"Creating auto-response notification for {from_number}")
                        
                        # Create notification data
                        post_data = {
                            'receiverWhatsappNumber': from_number,
                            'message': f"Thanks for your message: '{post_data['Body']}'. We'll get back to you soon.",
                            'messagePushTimestamp': int(time.time())  # Send immediately
                        }
                else:
                    self._set_headers(400)
                    self.wfile.write(json.dumps({"error": "Unsupported content type"}).encode())
                    return
                
                # Validate required fields
                required_fields = ['receiverWhatsappNumber', 'message', 'messagePushTimestamp']
                for field in required_fields:
                    if field not in post_data:
                        self._set_headers(400)
                        self.wfile.write(json.dumps({"error": f"Missing required field: {field}"}).encode())
                        return
                
                # Generate a unique ID
                notification_id = str(uuid.uuid4())
                
                # Create notification object
                new_notification = {
                    "id": notification_id,
                    "receiverWhatsappNumber": post_data['receiverWhatsappNumber'],
                    "message": post_data['message'],
                    "messagePushTimestamp": post_data['messagePushTimestamp'],
                    "status": "scheduled",
                    "createdAt": int(time.time())
                }
                
                # Add to cache
                notifications_cache.append(new_notification)
                
                # Save to file
                save_notifications(notifications_cache)
                
                # Schedule if in the future
                current_time = time.time()
                if new_notification['messagePushTimestamp'] > current_time:
                    schedule_notification(new_notification)
                else:
                    # Send immediately if scheduled time has passed
                    new_notification['status'] = 'pending'
                    send_notification(notification_id)
                
                self._set_headers(201)
                self.wfile.write(json.dumps(new_notification).encode())
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            except Exception as e:
                logger.error(f"Error processing request: {str(e)}")
                logger.error(traceback.format_exc())
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not found", "path": path}).encode())

def run_server(port):
    """Run the HTTP server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, NotificationHandler)
    logger.info(f'Starting server on port {port}...')
    httpd.serve_forever()

def start_file_watcher():
    """Start a file watcher to monitor the appointments file."""
    observer = watchdog.observers.Observer()
    event_handler = AppointmentChangeHandler()
    observer.schedule(event_handler, os.path.dirname(APPOINTMENTS_FILE), recursive=False)
    observer.start()
    logger.info(f"Started file watcher for {APPOINTMENTS_FILE}")
    return observer

if __name__ == "__main__":
    # Initialize the service
    initialize_service()
    
    # Start the file watcher
    file_observer = start_file_watcher()
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=run_server, args=(PORT,))
    server_thread.daemon = True  # The thread will exit when the main thread exits
    server_thread.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down the notification service...")
        file_observer.stop()
        file_observer.join()
        scheduler.shutdown() 