import re
from datetime import datetime
import phonenumbers
from phonenumbers import NumberParseException

class Validators:
    
    @staticmethod
    def validate_name(name):
        """Validate name - allows alphabets, spaces, and dots in various formats"""
        if not name or len(name.strip()) < 2:
            return False, "Name must be at least 2 characters long"
        
        if len(name.strip()) > 50:
            return False, "Name must not exceed 50 characters"
        
        # Allow alphabets, spaces, and dots (for initials like S. or .S)
        if not re.match(r"^[a-zA-Z\s\.]+$", name.strip()):
            return False, "Name should contain only alphabets, spaces, and dots (for initials)"
        
        # Normalize: capitalize first letter of each word
        parts = name.strip().split()
        normalized_parts = []
        
        for part in parts:
            if part == '.':  # Skip standalone dots
                continue
            # Handle cases like ".S" or "S." or "S"
            if '.' in part:
                # Keep the dot format as is but ensure letters are capitalized
                part_clean = part.replace('.', '')
                if part_clean:
                    if part.startswith('.'):
                        part = '.' + part_clean[0].upper()
                    else:
                        part = part_clean[0].upper() + '.'
                normalized_parts.append(part)
            else:
                normalized_parts.append(part.capitalize())
        
        normalized_name = ' '.join(normalized_parts)
        return True, normalized_name
    
    @staticmethod
    def validate_mobile(mobile):
        """Validate Indian mobile number"""
        # Remove spaces and special characters
        mobile = re.sub(r'[\s\-\(\)]', '', mobile)
        
        # Check if it's a valid Indian mobile number
        try:
            # Try parsing as Indian number
            if not mobile.startswith('+'):
                mobile = '+91' + mobile if len(mobile) == 10 else '+' + mobile
            
            parsed_number = phonenumbers.parse(mobile, "IN")
            
            if not phonenumbers.is_valid_number(parsed_number):
                return False, "Invalid mobile number format"
            
            # Format the number
            formatted = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            return True, formatted
            
        except NumberParseException:
            return False, "Invalid mobile number. Please enter a valid 10-digit number"
    
    @staticmethod
    def validate_dob(dob):
        """Validate date of birth - flexible format (D-M-YYYY, DD-MM-YYYY, D-MM-YYYY, DD-M-YYYY)"""
        try:
            # Split and parse flexibly
            parts = dob.split('-')
            if len(parts) != 3:
                return False, "Invalid date format. Use D-M-YYYY or DD-MM-YYYY (e.g., 2-3-2001 or 02-03-2001)"
            
            try:
                day = int(parts[0])
                month = int(parts[1])
                year = int(parts[2])
                
                # Validate ranges
                if day < 1 or day > 31:
                    return False, "Day must be between 1 and 31"
                if month < 1 or month > 12:
                    return False, "Month must be between 1 and 12"
                if year < 1900 or year > datetime.now().year:
                    return False, "Year must be between 1900 and current year"
                
                birth_date = datetime(year, month, day)
                
            except ValueError as e:
                return False, f"Invalid date values. {str(e)}"
            
            # Check if date is not in future
            if birth_date > datetime.now():
                return False, "Date of birth cannot be in the future"
            
            # Check if age is at least 18
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            if age < 18:
                return False, "Complainant must be at least 18 years old"
            
            if age > 120:
                return False, "Invalid date of birth"
            
            # Return in standardized format: DD-MM-YYYY
            return True, f"{day:02d}-{month:02d}-{year}"
            
        except Exception as e:
            return False, f"Invalid date format. Please use D-M-YYYY (e.g., 2-3-2001 or 02-03-2001)"
    
    @staticmethod
    def validate_district(district):
        """Validate district name"""
        if not district or len(district.strip()) < 2:
            return False, "District name must be at least 2 characters long"
        
        if len(district.strip()) > 50:
            return False, "District name must not exceed 50 characters"
        
        if not re.match(r"^[a-zA-Z\s]+$", district.strip()):
            return False, "District name should contain only alphabets and spaces"
        
        return True, district.strip().title()
    
    @staticmethod
    def validate_pincode(pincode):
        """Validate Indian PIN code (6 digits)"""
        pincode = str(pincode).strip()
        
        if not re.match(r"^[1-9][0-9]{5}$", pincode):
            return False, "Invalid PIN code. Must be 6 digits and cannot start with 0"
        
        return True, pincode
    
    @staticmethod
    def validate_number(number, field_name="Number"):
        """Validate if input is a positive number"""
        try:
            num = int(number)
            if num <= 0:
                return False, f"{field_name} must be a positive number"
            if num > 100:
                return False, f"{field_name} seems too large. Please enter a valid number"
            return True, num
        except ValueError:
            return False, f"Please enter a valid number for {field_name}"
    
    @staticmethod
    def validate_date(date_str):
        """Validate transaction date - flexible format (D-M-YYYY, DD-MM-YYYY, etc.)"""
        try:
            # Split and parse flexibly
            parts = date_str.split('-')
            if len(parts) != 3:
                return False, "Invalid date format. Use D-M-YYYY or DD-MM-YYYY (e.g., 2-3-2024 or 02-03-2024)"
            
            try:
                day = int(parts[0])
                month = int(parts[1])
                year = int(parts[2])
                
                # Validate ranges
                if day < 1 or day > 31:
                    return False, "Day must be between 1 and 31"
                if month < 1 or month > 12:
                    return False, "Month must be between 1 and 12"
                if year < 1900 or year > datetime.now().year:
                    return False, "Year must be between 1900 and current year"
                
                trans_date = datetime(year, month, day)
                
            except ValueError as e:
                return False, f"Invalid date values. {str(e)}"
            
            if trans_date > datetime.now():
                return False, "Transaction date cannot be in the future"
            
            # Check if date is not too old (within last 5 years)
            years_diff = (datetime.now() - trans_date).days / 365
            if years_diff > 5:
                return False, "Transaction date seems too old (more than 5 years)"
            
            # Return in standardized format: DD-MM-YYYY
            return True, f"{day:02d}-{month:02d}-{year}"
            
        except Exception as e:
            return False, f"Invalid date format. Use D-M-YYYY (e.g., 2-3-2024 or 02-03-2024)"
    
    @staticmethod
    def validate_time(time_str):
        """Validate time in multiple formats: HH:MM, H:MM, HH:M, H:M with optional AM/PM"""
        time_str = time_str.strip()
        
        # Remove extra spaces
        time_str = re.sub(r'\s+', ' ', time_str)
        
        # Patterns to match various time formats
        patterns = [
            # 12-hour format with AM/PM
            (r'^(\d{1,2}):(\d{1,2})\s*(AM|PM|am|pm|Am|Pm|aM|pM)$', True),
            # 24-hour format
            (r'^(\d{1,2}):(\d{1,2})$', False)
        ]
        
        for pattern, has_meridiem in patterns:
            match = re.match(pattern, time_str)
            if match:
                try:
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    
                    if has_meridiem:
                        meridiem = match.group(3).upper()
                        
                        # Validate 12-hour format
                        if hour < 1 or hour > 12:
                            return False, "Hour must be between 1 and 12 for 12-hour format"
                        
                        if minute < 0 or minute > 59:
                            return False, "Minutes must be between 0 and 59"
                        
                        # Convert to standardized format: HH:MM AM/PM
                        formatted_time = f"{hour:02d}:{minute:02d} {meridiem}"
                        return True, formatted_time
                    else:
                        # Validate 24-hour format
                        if hour < 0 or hour > 23:
                            return False, "Hour must be between 0 and 23 for 24-hour format"
                        
                        if minute < 0 or minute > 59:
                            return False, "Minutes must be between 0 and 59"
                        
                        # Convert 24-hour to 12-hour format
                        if hour == 0:
                            formatted_time = f"12:{minute:02d} AM"
                        elif hour < 12:
                            formatted_time = f"{hour:02d}:{minute:02d} AM"
                        elif hour == 12:
                            formatted_time = f"12:{minute:02d} PM"
                        else:
                            formatted_time = f"{hour-12:02d}:{minute:02d} PM"
                        
                        return True, formatted_time
                
                except ValueError:
                    continue
        
        return False, "Invalid time format. Use HH:MM (24-hour) or HH:MM AM/PM (12-hour). Examples: 14:30, 2:30 PM, 02:03 pm"
    
    @staticmethod
    def validate_bank_name(bank_name):
        """Validate bank name"""
        if not bank_name or len(bank_name.strip()) < 2:
            return False, "Bank name must be at least 2 characters long"
        
        if len(bank_name.strip()) > 100:
            return False, "Bank name must not exceed 100 characters"
        
        return True, bank_name.strip().upper()
    
    @staticmethod
    def validate_account_number(account_no):
        """
        Validate bank account number based on Indian bank standards:
        - Generic Account: 9-18 digits
        - SBI Account: 17 digits (with leading zeros)
        - ICICI Account: 12 digits
        """
        account_no = re.sub(r'\s', '', str(account_no))
        
        # Check SBI format (17 digits with leading zeros)
        sbi_pattern = r'^0{1,6}[0-9]{11,16}$'  # 17 digits total with leading zeros
        if re.match(sbi_pattern, account_no):
            return True, account_no
        
        # Check ICICI format (12 digits)
        icici_pattern = r'^[0-9]{12}$'
        if re.match(icici_pattern, account_no):
            return True, account_no
        
        # Check generic format (9-18 digits)
        generic_pattern = r'^[0-9]{9,18}$'
        if re.match(generic_pattern, account_no):
            return True, account_no
        
        return False, "Invalid account number. Formats:\n• Generic: 9-18 digits\n• SBI: 17 digits with leading zeros\n• ICICI: 12 digits"
    
    @staticmethod
    def validate_amount(amount):
        """Validate transaction amount"""
        try:
            amount_float = float(amount)
            if amount_float <= 0:
                return False, "Amount must be greater than 0"
            if amount_float > 1000000000:  # 1 crore max
                return False, "Amount seems too large. Please verify"
            return True, f"₹{amount_float:.2f}"
        except ValueError:
            return False, "Please enter a valid amount (numbers only)"
    
    @staticmethod
    def validate_transaction_id(trans_id):
        """
        Validate transaction ID based on Indian banking formats:
        
        Formats supported:
        1. Bank Account Number: 9-18 digits numeric only (123456789012)
        2. SBI Account: 17 digits numeric with leading zeros (00000012345678901 23)
        3. ICICI Account: 12 digits numeric (123456789012)
        4. Transaction ID: Alphanumeric, varies by bank/platform (TXN1234567890)
        5. UPI Transaction: Alphanumeric, unique per transaction (1234ABCD5678EFGH)
        """
        trans_id = str(trans_id).strip()
        
        if len(trans_id) < 8 or len(trans_id) > 50:
            return False, "Transaction ID must be between 8-50 characters"
        
        # Remove spaces for validation
        trans_id_clean = trans_id.replace(' ', '')
        
        # Check various valid formats
        valid_patterns = [
            # Bank Account Numbers (9-18 numeric digits)
            (r'^[0-9]{9,18}$', "Numeric Account Number"),
            
            # SBI format (17 digits with leading zeros)
            (r'^0{1,6}[0-9]{11,16}$', "SBI Account Format"),
            
            # ICICI format (12 digits)
            (r'^[0-9]{12}$', "ICICI Account Format"),
            
            # UPI format (alphanumeric)
            (r'^[0-9A-Z]{8,50}$', "UPI Transaction ID"),
            
            # Transaction ID with letters and numbers
            (r'^[A-Z]{3,}[0-9]{6,}$', "Generic Transaction ID"),
            
            # Special characters allowed (dash, underscore)
            (r'^[A-Z0-9\-_]{8,50}$', "Extended Format"),
        ]
        
        for pattern, format_name in valid_patterns:
            if re.match(pattern, trans_id_clean, re.IGNORECASE):
                return True, trans_id_clean.upper()
        
        return False, """Invalid transaction ID format. Examples:
• Bank Account: 123456789012 (9-18 digits)
• SBI Account: 00000012345678901 23 (17 digits with leading zeros)
• ICICI Account: 123456789012 (12 digits)
• Transaction ID: TXN1234567890
• UPI: 1234ABCD5678EFGH"""
