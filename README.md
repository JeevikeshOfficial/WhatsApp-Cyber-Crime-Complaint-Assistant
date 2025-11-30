# WhatsApp-Cyber-Crime-Complaint-Assistant
Flask-based WhatsApp chatbot that helps cybercrime victims register money-loss complaints, validates all inputs, stores structured cases in SQLite, generates a serial-numbered PDF, sends it back via Twilio, and offers a web dashboard for admins and attenders to manage and update complaints.

Quick Start
Prerequisites
Python 3.8+

Twilio Account with WhatsApp Business API

Ngrok (for local development)

Installation
bash
# Clone repository
git clone https://github.com/yourusername/whatsapp-cyber-complaint.git
cd whatsapp-cyber-complaint

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
Configuration
Create .env file:

text
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155552671
NGROK_URL=https://your-ngrok-url.ngrok.io
Run Application
bash
# Terminal 1: Start Ngrok
ngrok http 5001

# Terminal 2: Start Flask
python app.py
Access: http://localhost:5001/login.html

Project Structure
text
├── app.py                    # Flask app & WhatsApp webhook
├── database.py               # SQLite database operations
├── validators.py             # Input validation for all fields
├── pdf_generator.py          # PDF generation with ReportLab
├── login.html                # User login page
├── register.html             # User registration
├── admin.html                # Admin dashboard
├── attender.html             # Attender dashboard
├── api_fetch.js              # Frontend API calls
├── requirements.txt          # Python dependencies
└── complaints.db             # Auto-generated SQLite database
Features
WhatsApp Chatbot
Guided conversation with 30-minute session timeout

Collects personal info: Name, Mobile, DOB, Father's Name, District, PIN Code

Multi-transaction support with complete validation

Transaction details: Date, Time, Bank Name, Account No, Amount, Trans ID

Edit mode: Users can modify fields using serial numbers (1.1, 2.1.3, etc.)

PDF generation with serial-numbered fields

PDF delivery directly to WhatsApp via Twilio

Dashboards
Admin: View all complaints, assign handlers, update status

Attender: View assigned cases, update status, download PDFs

Database
Users: Username, password (hashed), role (admin/attender)

Complaints: Phone, personal info, transactions (JSON), status, handler

Sessions: Phone number, conversation state, session data, timestamp

---

API Endpoints
Endpoint	Method	Purpose
/webhook	POST	WhatsApp messages from Twilio
/register	POST	Register new user
/login	POST	User login
/complaints	GET	Get all complaints
/complaints/<id>/claim	POST	Assign handler & set status
/complaints/<id>/status	POST	Update status & transactions
/users/attenders	GET	Get all attenders
/download/<filename>	GET	Download PDF

---

Validation Rules
Personal Information
Name: 2-50 chars, alphabets/spaces/dots only

Mobile: 10-digit Indian number

DOB: D-M-YYYY format, age ≥ 18

District: 2-50 chars, alphabets/spaces only

PIN Code: 6 digits, cannot start with 0

Transaction Details
Date: D-M-YYYY, within last 5 years

Time: 24-hr (14:30) or 12-hr (2:30 PM) format

Bank Name: 2-100 chars, alphanumeric

Account No: 9-18 digits (SBI/ICICI/Generic formats)

Amount: > 0, max 1 crore

Trans ID: 8-50 chars, alphanumeric/UPI formats

---

Chatbot Workflow
User sends "Hi"

Bot asks: "Money loss due to cyber crime?" (Yes/No)

Yes → Register complaint

No → Redirect to cybercrime.gov.in

Collect personal information (6 fields)

Ask number of fraudulent transactions

Loop: Collect transaction details (6 fields each)

Show summary with serial numbers

Ask: "Generate PDF or edit information?"

Yes → Generate & send PDF

No → Enter edit mode

In edit mode: Type "serial_number = new_value" (e.g., "1.1 = John Smith")

Type "done" to finish editing

Success message with cybercrime.gov.in link

---

Dependencies
text
Flask - Web framework
Flask-Cors - Cross-origin requests
twilio - WhatsApp integration
python-dotenv - Environment variables
reportlab - PDF generation
requests - HTTP requests
phonenumbers - Mobile validation
werkzeug - Password hashing

---

Database Schema
Users Table
text
id (INTEGER PRIMARY KEY)
username (TEXT UNIQUE)
password_hash (TEXT)
role (TEXT) - 'admin' or 'attender'
created_at (TIMESTAMP)

---

Complaints Table
text
id (INTEGER PRIMARY KEY)
phone_number (TEXT)
name (TEXT)
mobile_no (TEXT)
dob (TEXT)
father_name (TEXT)
district (TEXT)
pin_code (TEXT)
transactions (JSON)
created_at (TIMESTAMP)
handler (TEXT)
status (TEXT) - 'Pending', 'In Progress', 'Resolved'

---

Sessions Table
text
phone_number (TEXT PRIMARY KEY)
state (TEXT)
data (JSON)
last_activity (TIMESTAMP)

---

Conversation States
start → money_loss → (Yes) → name → mobile → dob → father_name → district → pin_code → transaction_count → trans_date (loop) → trans_time (loop) → trans_bank (loop) → trans_account (loop) → trans_amount (loop) → trans_id (loop) → confirm → edit (optional) → PDF sent

---

Key Functions
app.py
webhook() - Main Twilio webhook handler

upload_pdf_temp() - Save PDF locally

send_pdf_to_whatsapp() - Send PDF via Twilio

check_session_timeout() - 30-min inactivity check

format_summary_message() - Format complaint summary

edit_field() - Handle field edits via serial numbers

database.py
save_complaint() - Store complaint

get_all_complaints() - Retrieve all complaints

update_complaint_handler_status() - Assign handler

update_complaint_status() - Update status

clean_expired_sessions() - Remove old sessions (30+ min)

validators.py
validate_name() - Name validation

validate_mobile() - Indian mobile number

validate_dob() - Date of birth (18+)

validate_date() - Transaction date

validate_time() - 24-hr or 12-hr time

validate_bank_name() - Bank name

validate_account_number() - Account number

validate_amount() - Transaction amount

validate_transaction_id() - Trans ID (UPI/Bank formats)

pdf_generator.py
generate_complaint_pdf() - Create PDF with serial numbers

---

Testing
Test WhatsApp Chatbot
Start Ngrok & Flask

Send "Hi" to Twilio WhatsApp number

Follow conversation flow

Receive PDF on WhatsApp

Test API
bash
# Register user
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"pass","role":"admin"}'

# Login
curl -X POST http://localhost:5001/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"pass","role":"admin"}'

# Get complaints
curl http://localhost:5001/complaints

---

Troubleshooting
Port 5001 already in use

bash
# Find & kill process
netstat -ano | findstr :5001
taskkill /PID <PID> /F
Twilio webhook not working

Verify Ngrok is running

Check webhook URL in Twilio Console matches Ngrok URL

Ensure Flask is running

WhatsApp message not received

Activate WhatsApp in Twilio Sandbox

Scan QR code with WhatsApp

Send sandbox activation code

Database locked

bash
# Restart Flask
pkill -f "python app.py"
python app.py

---

Production Notes
Use environment variables for credentials (never commit .env)

Enable HTTPS (not HTTP)

Use proper PDF storage (not local temp_pdfs)

Implement database backups

Add rate limiting

Monitor error logs

---
## About:

Developer:

Chatbot:

1 . Jeevikesh S - LinkedIn (https://www.linkedin.com/in/Jeevikesh-Srinivasan/)

2 . Balaguru J P - LinkedIn (https://www.linkedin.com/in/balaguru-j-p-62227a276/)

3. Sathivel B - LinkedIn (https://www.linkedin.com/in/sakthivel-b-bb3171350/)
   
Website:

1. Pragatheeswaran M - LinkedIn (https://www.linkedin.com/in/spm-pragatheeswaran-4a2824245/)

2. Tejaswini Balaji - LinkedIn (https://www.linkedin.com/in/tejaswini-balaji-826753300/)

3. Selvarani Palanivelrajaan - LinkedIn (https://www.linkedin.com/in/selvarani-palanivelrajaan/)

4. Janani 
---

Version
1.0.0 - November 2025
