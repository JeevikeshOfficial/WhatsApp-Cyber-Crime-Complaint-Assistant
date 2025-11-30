import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import json

class Database:
    def __init__(self, db_name='complaints.db'):
        """Initialize database connection"""
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Create tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Sessions table for conversation state
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                phone_number TEXT PRIMARY KEY,
                state TEXT NOT NULL,
                data TEXT NOT NULL,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Complaints table for storing complaint data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT NOT NULL,
                name TEXT NOT NULL,
                mobile_no TEXT NOT NULL,
                dob TEXT NOT NULL,
                father_name TEXT NOT NULL,
                district TEXT NOT NULL,
                pin_code TEXT NOT NULL,
                transactions TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                handler TEXT,
                status TEXT DEFAULT 'Pending'
            )
        ''')
        
        # Users table for login credentials
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # This method is not needed as init_database() handles all tables.
    def create_users_table(self):
        self.init_database()

    def save_session(self, phone_number, state, data):
        """Save or update session data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO sessions (phone_number, state, data, last_activity)
            VALUES (?, ?, ?, ?)
        ''', (phone_number, state, json.dumps(data), datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_session(self, phone_number):
        """Retrieve session data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT state, data FROM sessions WHERE phone_number = ?
        ''', (phone_number,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            state = result['state']
            data = json.loads(result['data']) if result['data'] else {}
            return state, data
        return None, {}
    
    def delete_session(self, phone_number):
        """Delete session data"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM sessions WHERE phone_number = ?', (phone_number,))
        
        conn.commit()
        conn.close()
    
    def save_complaint(self, complaint_data):
        """Save complaint to database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO complaints 
            (phone_number, name, mobile_no, dob, father_name, district, pin_code, transactions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            complaint_data['phone_number'],
            complaint_data['name'],
            complaint_data['mobile_no'],
            complaint_data['dob'],
            complaint_data['father_name'],
            complaint_data['district'],
            complaint_data['pin_code'],
            json.dumps(complaint_data['transactions'])
        ))
        
        complaint_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return complaint_id
    
    def get_all_complaints(self):
        """Retrieve all complaints from the database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, phone_number, name, mobile_no, dob, father_name, district, pin_code, transactions, created_at, handler, status FROM complaints ORDER BY created_at DESC')
        
        rows = cursor.fetchall()
        conn.close()
        
        # Convert rows to a list of dictionaries
        complaints = [dict(row) for row in rows]
        return complaints

    def update_complaint_handler_status(self, complaint_id, handler_username, status):
        """Update the handler and status of a specific complaint."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE complaints SET handler = ?, status = ? WHERE id = ?",
                (handler_username, status, complaint_id)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Database error updating handler/status: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def update_complaint_status(self, complaint_id, new_status, updated_transactions_list=None):
        """Update the status and optionally the transactions of a specific complaint."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if updated_transactions_list is not None:
                transactions_json = json.dumps(updated_transactions_list)
                cursor.execute(
                    "UPDATE complaints SET status = ?, transactions = ? WHERE id = ?",
                    (new_status, transactions_json, complaint_id)
                )
            else:
                cursor.execute("UPDATE complaints SET status = ? WHERE id = ?", (new_status, complaint_id))
            conn.commit()
            return True
        except Exception as e:
            print(f"Database error updating status/transactions: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def add_user(self, username, password, role):
        """Add a new user with a hashed password."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        password_hash = generate_password_hash(password)
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        ''', (username, password_hash, role))
        
        conn.commit()
        conn.close()

    def get_user(self, username):
        """Retrieve a user by username."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None

    def check_password(self, password_hash, password):
        """Check if a password matches the stored hash."""
        return check_password_hash(password_hash, password)

    def get_users_by_role(self, role):
        """Retrieve all users with a specific role."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE role = ?', (role,))
        
        rows = cursor.fetchall()
        conn.close()
        
        users = [dict(row) for row in rows]
        return users

    def clean_expired_sessions(self, minutes=30):
        """Clean sessions inactive for more than specified minutes"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM sessions 
            WHERE last_activity < datetime('now', '-' || ? || ' minutes')
        ''', (minutes,))
        
        conn.commit()
        conn.close()
