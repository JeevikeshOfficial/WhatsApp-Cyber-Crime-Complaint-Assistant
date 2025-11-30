from flask import Flask, request, send_from_directory, jsonify, session
from flask_cors import CORS
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import os
from dotenv import load_dotenv
from database import Database
from validators import Validators
from pdf_generator import PDFGenerator
import requests
import secrets
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Needed for session management
CORS(app)  # Enable Cross-Origin Resource Sharing

# Twilio Configuration
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER')
NGROK_URL = os.getenv('NGROK_URL', 'http://localhost:5001')

# Initialize Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Initialize Database
db = Database()
db.create_users_table()  # Ensure users table exists

# Conversation States
STATE_START = 'start'
STATE_MONEY_LOSS = 'money_loss'
STATE_NAME = 'name'
STATE_MOBILE = 'mobile'
STATE_DOB = 'dob'
STATE_FATHER_NAME = 'father_name'
STATE_DISTRICT = 'district'
STATE_PIN_CODE = 'pin_code'
STATE_TRANSACTION_COUNT = 'transaction_count'
STATE_TRANS_DATE = 'trans_date'
STATE_TRANS_TIME = 'trans_time'
STATE_TRANS_BANK = 'trans_bank'
STATE_TRANS_ACCOUNT = 'trans_account'
STATE_TRANS_AMOUNT = 'trans_amount'
STATE_TRANS_ID = 'trans_id'
STATE_CONFIRM = 'confirm'
STATE_EDIT = 'edit'


def upload_pdf_temp(pdf_buffer, phone_number, complaint_id):
    """Save PDF temporarily to a local folder"""
    filename = f"complaint_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    filepath = os.path.join('temp_pdfs', filename)
    
    # Create temp folder if it doesn't exist
    os.makedirs('temp_pdfs', exist_ok=True)
    
    with open(filepath, 'wb') as f:
        f.write(pdf_buffer.getvalue())
    
    return filepath, filename


def send_pdf_to_whatsapp(phone_number, pdf_filename, complaint_id):
    """Send PDF file to WhatsApp via Twilio"""
    try:
        # Create public URL for PDF
        pdf_public_url = f"{NGROK_URL}/download/{pdf_filename}"
        
        # Send PDF with caption
        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=f"📄 Your Cyber Crime Complaint Form\n",
            media_url=[pdf_public_url],
            to=phone_number
        )
        
        return True, message.sid
    except Exception as e:
        print(f"Error sending PDF: {e}")
        return False, str(e)


def check_session_timeout(phone_number):
    """Check if session has timed out (30 minutes)"""
    state, data = db.get_session(phone_number)
    
    if state and data:
        last_activity = datetime.fromisoformat(data.get('last_activity', datetime.now().isoformat()))
        if datetime.now() - last_activity > timedelta(minutes=30):
            db.delete_session(phone_number)
            return True, "Due to inactivity on the channel, your session has timed out. Just type 'Hi' to restart your conversation."
    
    return False, None


def format_summary_message(session_data):
    """Format a summary of all collected data"""
    summary = "📋 *SUMMARY OF YOUR COMPLAINT*\n\n"
    summary += "👤 *PERSONAL INFORMATION:*\n"
    summary += f"1.1 Name: {session_data.get('name', 'N/A')}\n"
    summary += f"1.2 Mobile: {session_data.get('mobile_no', 'N/A')}\n"
    summary += f"1.3 DOB: {session_data.get('dob', 'N/A')}\n"
    summary += f"1.4 Father's Name: {session_data.get('father_name', 'N/A')}\n"
    summary += f"1.5 District: {session_data.get('district', 'N/A')}\n"
    summary += f"1.6 PIN Code: {session_data.get('pin_code', 'N/A')}\n\n"
    
    summary += "💳 *TRANSACTION DETAILS:*\n"
    transactions = session_data.get('transactions', [])
    for idx, trans in enumerate(transactions, 1):
        summary += f"\n📌 Transaction #{idx}:\n"
        summary += f"2.{idx}.1 Date: {trans.get('date', 'N/A')}\n"
        summary += f"2.{idx}.2 Time: {trans.get('time', 'N/A')}\n"
        summary += f"2.{idx}.3 Bank: {trans.get('bank_name', 'N/A')}\n"
        summary += f"2.{idx}.4 Account: {trans.get('account_no', 'N/A')}\n"
        summary += f"2.{idx}.5 Amount: {trans.get('amount', 'N/A')}\n"
        summary += f"2.{idx}.6 Trans ID: {trans.get('transaction_id', 'N/A')}\n"
    
    return summary


def edit_field(session_data, field_num, new_value):
    """Edit a specific field based on serial number"""
    try:
        parts = field_num.split('.')
        
        # Personal information fields (1.x)
        if len(parts) == 2 and parts[0] == '1':
            field_map = {
                '1': 'name',
                '2': 'mobile_no',
                '3': 'dob',
                '4': 'father_name',
                '5': 'district',
                '6': 'pin_code'
            }
            
            field_key = field_map.get(parts[1])
            
            if field_key:
                # Validate based on field type
                if field_key == 'name' or field_key == 'father_name':
                    is_valid, result = Validators.validate_name(new_value)
                elif field_key == 'mobile_no':
                    is_valid, result = Validators.validate_mobile(new_value)
                elif field_key == 'dob':
                    is_valid, result = Validators.validate_dob(new_value)
                elif field_key == 'district':
                    is_valid, result = Validators.validate_district(new_value)
                elif field_key == 'pin_code':
                    is_valid, result = Validators.validate_pincode(new_value)
                else:
                    return False, "Invalid field"
                
                if is_valid:
                    session_data[field_key] = result
                    return True, f"✅ Field {field_num} updated: {result}"
                else:
                    return False, result
        
        # Transaction fields (2.x.y)
        elif len(parts) == 3 and parts[0] == '2':
            trans_num = int(parts[1]) - 1
            field_num_trans = parts[2]
            
            if trans_num < 0 or trans_num >= len(session_data.get('transactions', [])):
                return False, "Invalid transaction number"
            
            field_map_trans = {
                '1': ('date', Validators.validate_date),
                '2': ('time', Validators.validate_time),
                '3': ('bank_name', Validators.validate_bank_name),
                '4': ('account_no', Validators.validate_account_number),
                '5': ('amount', Validators.validate_amount),
                '6': ('transaction_id', Validators.validate_transaction_id)
            }
            
            if field_num_trans in field_map_trans:
                field_key, validator = field_map_trans[field_num_trans]
                is_valid, result = validator(new_value)
                
                if is_valid:
                    session_data['transactions'][trans_num][field_key] = result
                    return True, f"✅ Trans #{trans_num + 1} field {field_num_trans} updated: {result}"
                else:
                    return False, result
        
        return False, "Invalid field number. Use 1.1-1.6 for personal info or 2.X.1-2.X.6 for transactions"
    
    except Exception as e:
        return False, f"Error editing field: {str(e)}"


@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook endpoint for Twilio WhatsApp messages"""
    # Get incoming message details
    incoming_msg = request.form.get('Body', '').strip()
    from_number = request.form.get('From', '')
    
    # Clean expired sessions
    db.clean_expired_sessions(30)
    
    # Check for timeout
    is_timeout, timeout_msg = check_session_timeout(from_number)
    if is_timeout:
        resp = MessagingResponse()
        resp.message(timeout_msg)
        return str(resp)
    
    # Get current session state
    state, session_data = db.get_session(from_number)
    
    # Update last activity
    session_data['last_activity'] = datetime.now().isoformat()
    
    # Initialize response
    resp = MessagingResponse()
    reply = ""
    new_state = state
    
    # Handle conversation flow
    if not state or incoming_msg.lower() in ['hi', 'hello', 'start']:
        # Start conversation
        reply = "👋 Hello! Welcome to Cyber Crime Complaint Registration Bot.\n\n"
        reply += "Have you suffered a *money loss* due to cyber crime?\n\n"
        reply += "Reply:\n1️⃣ *Yes* - Register a complaint\n2️⃣ *No* - Track existing complaint"
        new_state = STATE_MONEY_LOSS
        db.save_session(from_number, new_state, session_data)
    
    elif state == STATE_MONEY_LOSS:
        if incoming_msg.lower() in ['yes', '1', 'yes.']:
            reply = "Let's register your complaint. I'll collect some information from you.\n\n"
            reply += "📝 *Personal Information*\n\n"
            reply += "Please enter your *full name*:\n"
            reply += "_Example: Rajesh Kumar or JEEVIKESH S or jeevikesh .S_"
            new_state = STATE_NAME
            db.save_session(from_number, new_state, session_data)
        
        elif incoming_msg.lower() in ['no', '2', 'no.']:
            reply = "To track your complaint, please visit the official NCRP website:\n\n"
            reply += "🔗 https://cybercrime.gov.in\n\n"
            reply += "Type 'Hi' anytime to start a new complaint registration."
            db.delete_session(from_number)
            new_state = None
        
        else:
            reply = "Please reply with *Yes* or *No*.\n\n"
            reply += "Have you suffered a money loss due to cyber crime?"
            new_state = STATE_MONEY_LOSS
    
    elif state == STATE_NAME:
        is_valid, result = Validators.validate_name(incoming_msg)
        if is_valid:
            session_data['name'] = result
            reply = "Please enter your *mobile number* (10 digits):"
            new_state = STATE_MOBILE
            db.save_session(from_number, new_state, session_data)
        else:
            reply = f"❌ {result}\n\nPlease enter a valid name:"
            new_state = STATE_NAME
    
    elif state == STATE_MOBILE:
        is_valid, result = Validators.validate_mobile(incoming_msg)
        if is_valid:
            session_data['mobile_no'] = result
            reply = "Please enter your *Date of Birth* (D-M-YYYY):\n"
            reply += "_Examples: 2-3-2001 or 02-03-2001 or 2-03-2001_"
            new_state = STATE_DOB
            db.save_session(from_number, new_state, session_data)
        else:
            reply = f"❌ {result}\n\nPlease enter a valid mobile number:"
            new_state = STATE_MOBILE
    
    elif state == STATE_DOB:
        is_valid, result = Validators.validate_dob(incoming_msg)
        if is_valid:
            session_data['dob'] = result
            reply = "Please enter your *Father's Name*:"
            new_state = STATE_FATHER_NAME
            db.save_session(from_number, new_state, session_data)
        else:
            reply = f"❌ {result}\n\nPlease enter date in D-M-YYYY format:"
            new_state = STATE_DOB
    
    elif state == STATE_FATHER_NAME:
        is_valid, result = Validators.validate_name(incoming_msg)
        if is_valid:
            session_data['father_name'] = result
            reply = "Please enter your *District*:"
            new_state = STATE_DISTRICT
            db.save_session(from_number, new_state, session_data)
        else:
            reply = f"❌ {result}\n\nPlease enter a valid name:"
            new_state = STATE_FATHER_NAME
    
    elif state == STATE_DISTRICT:
        is_valid, result = Validators.validate_district(incoming_msg)
        if is_valid:
            session_data['district'] = result
            reply = "Please enter your *PIN Code* (6 digits):"
            new_state = STATE_PIN_CODE
            db.save_session(from_number, new_state, session_data)
        else:
            reply = f"❌ {result}\n\nPlease enter a valid district name:"
            new_state = STATE_DISTRICT
    
    elif state == STATE_PIN_CODE:
        is_valid, result = Validators.validate_pincode(incoming_msg)
        if is_valid:
            session_data['pin_code'] = result
            reply = "💳 *Transaction Details*\n\n"
            reply += "How many *fraudulent transactions* were made?\n"
            reply += "_Enter a number (e.g., 2)_"
            new_state = STATE_TRANSACTION_COUNT
            db.save_session(from_number, new_state, session_data)
        else:
            reply = f"❌ {result}\n\nPlease enter a valid PIN code:"
            new_state = STATE_PIN_CODE
    
    elif state == STATE_TRANSACTION_COUNT:
        is_valid, result = Validators.validate_number(incoming_msg, "Transaction count")
        if is_valid:
            session_data['transaction_count'] = result
            session_data['transactions'] = []
            session_data['current_transaction'] = 0
            
            reply = f"📝 *Transaction #1*\n\n"
            reply += "Enter *Transaction Date* (D-M-YYYY):\n"
            reply += "_Examples: 25-10-2024 or 2-3-2024_"
            new_state = STATE_TRANS_DATE
            db.save_session(from_number, new_state, session_data)
        else:
            reply = f"❌ {result}\n\nPlease enter a valid number:"
            new_state = STATE_TRANSACTION_COUNT
    
    elif state == STATE_TRANS_DATE:
        is_valid, result = Validators.validate_date(incoming_msg)
        if is_valid:
            current_trans = session_data.get('current_transaction', 0)
            if len(session_data['transactions']) <= current_trans:
                session_data['transactions'].append({})
            
            session_data['transactions'][current_trans]['date'] = result
            reply = "Enter *Transaction Time*:\n"
            reply += "_Examples: 14:30, 2:30 PM, 02:03 pm, 2:3 PM_"
            new_state = STATE_TRANS_TIME
            db.save_session(from_number, new_state, session_data)
        else:
            reply = f"❌ {result}\n\nPlease enter date in D-M-YYYY format:"
            new_state = STATE_TRANS_DATE
    
    elif state == STATE_TRANS_TIME:
        is_valid, result = Validators.validate_time(incoming_msg)
        if is_valid:
            current_trans = session_data.get('current_transaction', 0)
            session_data['transactions'][current_trans]['time'] = result
            
            reply = "Enter *Bank Name*:"
            new_state = STATE_TRANS_BANK
            db.save_session(from_number, new_state, session_data)
        else:
            reply = f"❌ {result}\n\nPlease enter time (Examples: 14:30, 2:30 PM, 02:03 pm):"
            new_state = STATE_TRANS_TIME
    
    elif state == STATE_TRANS_BANK:
        is_valid, result = Validators.validate_bank_name(incoming_msg)
        if is_valid:
            current_trans = session_data.get('current_transaction', 0)
            session_data['transactions'][current_trans]['bank_name'] = result
            
            reply = "Enter *Bank Account Number*:\n"
            reply += "_Formats:\n• Generic: 9-18 digits (123456789012)\n• SBI: 17 digits with leading zeros\n• ICICI: 12 digits (123456789012)_"
            new_state = STATE_TRANS_ACCOUNT
            db.save_session(from_number, new_state, session_data)
        else:
            reply = f"❌ {result}\n\nPlease enter a valid bank name:"
            new_state = STATE_TRANS_BANK
    
    elif state == STATE_TRANS_ACCOUNT:
        is_valid, result = Validators.validate_account_number(incoming_msg)
        if is_valid:
            current_trans = session_data.get('current_transaction', 0)
            session_data['transactions'][current_trans]['account_no'] = result
            
            reply = "Enter *Amount Debited* (in ₹):"
            new_state = STATE_TRANS_AMOUNT
            db.save_session(from_number, new_state, session_data)
        else:
            reply = f"❌ {result}\n\nPlease enter a valid account number:"
            new_state = STATE_TRANS_ACCOUNT
    
    elif state == STATE_TRANS_AMOUNT:
        is_valid, result = Validators.validate_amount(incoming_msg)
        if is_valid:
            current_trans = session_data.get('current_transaction', 0)
            session_data['transactions'][current_trans]['amount'] = result
            
            reply = "Enter *Transaction ID / Reference Number*:\n"
            reply += "_Formats:\n• Account #: 9-18 digits (123456789012)\n• SBI: 17 digits with zeros\n• UPI: Alphanumeric (1234ABCD5678EFGH)\n• Generic: TXN1234567890_"
            new_state = STATE_TRANS_ID
            db.save_session(from_number, new_state, session_data)
        else:
            reply = f"❌ {result}\n\nPlease enter a valid amount:"
            new_state = STATE_TRANS_AMOUNT
    
    elif state == STATE_TRANS_ID:
        is_valid, result = Validators.validate_transaction_id(incoming_msg)
        if is_valid:
            current_trans = session_data.get('current_transaction', 0)
            session_data['transactions'][current_trans]['transaction_id'] = result
            
            # Check if more transactions are pending
            session_data['current_transaction'] += 1
            next_trans = session_data['current_transaction']
            total_trans = session_data['transaction_count']
            
            if next_trans < total_trans:
                reply = f"📝 *Transaction #{next_trans + 1}*\n\n"
                reply += "Enter *Transaction Date* (D-M-YYYY):"
                new_state = STATE_TRANS_DATE
                db.save_session(from_number, new_state, session_data)
            else:
                # All transactions collected, show summary
                summary = format_summary_message(session_data)
                
                # Send summary first
                resp.message(summary)
                
                # Ask for confirmation - YES to generate PDF, NO to edit
                confirm_msg = "📋 Do you want to generate PDF or edit information?\n\n"
                confirm_msg += "Reply:\n*Yes* - to generate PDF\n*No* - to edit information"
                resp.message(confirm_msg)
                
                new_state = STATE_CONFIRM
                db.save_session(from_number, new_state, session_data)
                
                return str(resp)
        else:
            reply = f"❌ {result}\n\nPlease enter a valid transaction ID:"
            new_state = STATE_TRANS_ID
    
    elif state == STATE_CONFIRM:
        # YES = Generate PDF, NO = Edit
        if incoming_msg.lower() in ['yes', 'confirm']:
            # YES - Generate PDF and send to WhatsApp
            reply = "✅ Generating your complaint PDF..."
            resp.message(reply)
            
            # Prepare complaint data
            complaint_data = {
                'phone_number': from_number,
                'name': session_data['name'],
                'mobile_no': session_data['mobile_no'],
                'dob': session_data['dob'],
                'father_name': session_data['father_name'],
                'district': session_data['district'],
                'pin_code': session_data['pin_code'],
                'transactions': session_data['transactions']
            }
            
            # Save to database
            complaint_id = db.save_complaint(complaint_data)
            
            # Generate PDF
            pdf_buffer = PDFGenerator.generate_complaint_pdf(complaint_data)
            pdf_path, pdf_filename = upload_pdf_temp(pdf_buffer, from_number.replace('whatsapp:', ''), complaint_id)
            
            # Send PDF to WhatsApp
            success, msg_id = send_pdf_to_whatsapp(from_number, pdf_filename, complaint_id)
            
            if success:
                # Success message
                success_msg = f"✅ *DATA COLLECTED SUCCESSFUL!*\n\n"
#                success_msg += f"📋 Complaint ID: *{complaint_id}*\n\n"
                success_msg += "📞 For further assistance:\n"
                success_msg += "🔗 https://cybercrime.gov.in\n\n"
                success_msg += "Thank you for using our service! Stay safe online! 🛡️\n\n"
                success_msg += "_Type 'Hi' to register a new complaint._"
                resp.message(success_msg)
            else:
                # Fallback if PDF sending fails
                fallback_msg = f"✅ Complaint registered with ID: {complaint_id}\n\n"
                fallback_msg += "⚠️ PDF saved locally. Please contact support."
                resp.message(fallback_msg)
            
            db.delete_session(from_number)
            new_state = None
            
            return str(resp)
        
        elif incoming_msg.lower() in ['no', 'edit']:
            # NO - Allow editing before PDF generation
            reply = "✏️ *EDIT YOUR INFORMATION*\n\n"
            reply += "Use format: *serial_number = new_value*\n\n"
            reply += "*Examples of Editing:*\n"
            reply += "• 1.1 = JOHN SMITH\n"
            reply += "• 1.3 = 01-01-1995\n"
            reply += "• 2.1.2 = 02:03 PM\n"
            reply += "• 2.1.4 = 123456789012\n"
            reply += "• 2.1.6 = TXN1234567890\n\n"
            reply += "Type *'done'* when finished\n"
            reply += "Type *'summary'* to view all data"
            new_state = STATE_EDIT
            db.save_session(from_number, new_state, session_data)
        
        else:
            reply = "Please reply with *Yes* to generate PDF or *No* to edit information."
            new_state = STATE_CONFIRM
    
    elif state == STATE_EDIT:
        if incoming_msg.lower() == 'done':
            # Show updated summary
            summary = format_summary_message(session_data)
            resp.message(summary)
            
            confirm_msg = "Generate PDF with updated data?\n\n"
            confirm_msg += "Reply:\n*Yes* - to generate PDF\n*No* - to edit more"
            resp.message(confirm_msg)
            
            new_state = STATE_CONFIRM
            db.save_session(from_number, new_state, session_data)
            
            return str(resp)
        
        elif incoming_msg.lower() == 'summary':
            reply = format_summary_message(session_data)
            reply += "\n\n*To edit:* type serial_number = new_value\n"
            reply += "Examples: 1.1 = New Name or 2.1.2 = 02:03 PM\n"
            reply += "Type 'done' when finished"
            new_state = STATE_EDIT
        
        else:
            # Parse edit command (format: serial_number = new_value)
            if '=' in incoming_msg:
                parts = incoming_msg.split('=', 1)
                field_num = parts[0].strip()
                new_value = parts[1].strip()
                
                success, message = edit_field(session_data, field_num, new_value)
                
                if success:
                    reply = message + "\n\n"
                    reply += "Continue editing or type 'done' to finish.\n"
                    reply += "Type 'summary' to review all data."
                    db.save_session(from_number, STATE_EDIT, session_data)
                else:
                    reply = f"❌ {message}\n\n"
                    reply += "Format: *serial_number = new_value*\n"
                    reply += "Examples:\n• 1.1 = JOHN SMITH\n• 2.1.2 = 02:03 PM\n• 2.1.4 = 123456789012"
                    new_state = STATE_EDIT
            else:
                reply = "❌ Invalid format!\n\n"
                reply += "Use: *serial_number = new_value*\n\n"
                reply += "*Personal Info Examples:*\n"
                reply += "1.1 = Rajesh Kumar\n"
                reply += "1.3 = 02-03-2001\n\n"
                reply += "*Transaction Examples:*\n"
                reply += "2.1.2 = 02:03 PM\n"
                reply += "2.1.4 = 123456789012\n"
                reply += "2.1.6 = TXN1234567890\n\n"
                reply += "Type 'done' when finished"
                new_state = STATE_EDIT
    
    else:
        reply = "Something went wrong. Please type 'Hi' to restart."
        db.delete_session(from_number)
        new_state = None
    
    # Send response
    resp.message(reply)
    
    return str(resp)


@app.route('/download/<filename>')
def download_pdf(filename):
    """Serve PDF files for download"""
    pdf_dir = os.path.join(os.getcwd(), 'temp_pdfs')
    try:
        return send_from_directory(pdf_dir, filename, as_attachment=True)
    except Exception as e:
        return f"File not found: {e}", 404


@app.route('/complaints')
def get_complaints():
    """API endpoint to get all complaints for the admin dashboard."""
    complaints = db.get_all_complaints()
    return jsonify(complaints)


@app.route('/complaints/<int:complaint_id>/claim', methods=['POST'])
def claim_complaint(complaint_id):
    """API endpoint for an attender to claim a case or admin to assign it."""
    data = request.get_json()
    handler = data.get('handler')
    status = data.get('status')

    if not handler or not status:
        return jsonify({'error': 'Missing handler or status'}), 400

    success = db.update_complaint_handler_status(complaint_id, handler, status)

    if success:
        return jsonify({'message': f'Complaint {complaint_id} updated successfully.'}), 200
    else:
        return jsonify({'error': 'Failed to update complaint in database'}), 500


@app.route('/complaints/<int:complaint_id>/status', methods=['POST'])
def update_status(complaint_id):
    """API endpoint to update a case's status and transactions."""
    data = request.get_json()
    status = data.get('status')
    transactions = data.get('transactions') # This can be None

    success = db.update_complaint_status(complaint_id, status, transactions)
    if success:
        return jsonify({'message': f'Complaint {complaint_id} status updated.'}), 200
    else:
        return jsonify({'error': 'Failed to update complaint status'}), 500

@app.route('/register', methods=['POST'])
def register_user():
    """API endpoint to register a new user."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    
    if not all([username, password, role]):
        return jsonify({'error': 'Missing username, password, or role'}), 400
    
    if db.get_user(username):
        return jsonify({'error': 'Username already exists'}), 409
    
    db.add_user(username, password, role)
    
    return jsonify({'message': f'User {username} registered successfully as {role}'}), 201


@app.route('/login', methods=['POST'])
def login_user():
    """API endpoint for user login."""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    
    user = db.get_user(username)
    
    if user and user['role'] == role and db.check_password(user['password_hash'], password):
        # Store user info in session
        session['user'] = {'username': user['username'], 'role': user['role']}
        return jsonify({'message': 'Login successful', 'user': session['user']}), 200
    else:
        return jsonify({'error': 'Invalid credentials or role'}), 401


@app.route('/users/attenders')
def get_attenders():
    """API endpoint to get all users with the 'attender' role."""
    attenders = db.get_users_by_role('attender')
    # We only need the usernames
    attender_usernames = [user['username'] for user in attenders]
    return jsonify(attender_usernames)


@app.route('/<path:filename>')
def serve_static(filename):
    """Serves static files like admin.html, attender.html."""
    return send_from_directory('.', filename)


@app.route('/')
def root():
    """Redirect root to login page."""
    return send_from_directory('.', 'login.html')


@app.route('/login.html')
def login_page():
    """Serves the login.html page as the default page."""
    return send_from_directory('.', 'login.html')


if __name__ == '__main__':
    # Clean up old sessions on startup
    db.clean_expired_sessions(30)
    
    # Run Flask app on port 5001 (changed from 5000)
    app.run(debug=True, port=5001)
