from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime

class PDFGenerator:
    
    @staticmethod
    def generate_complaint_pdf(data):
        """Generate PDF complaint form from data"""
        
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Title
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawCentredString(width / 2, height - 50, "CYBER CRIME COMPLAINT FORM")
        
        # Horizontal line
        pdf.line(50, height - 60, width - 50, height - 60)
        
        y_position = height - 100
        
        # Personal Information Section
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y_position, "1. PERSONAL INFORMATION")
        y_position -= 30
        
        pdf.setFont("Helvetica", 11)
        personal_info = [
            ("1.1", "Name of Complainant", data.get('name', 'N/A')),
            ("1.2", "Mobile No of Complainant", data.get('mobile_no', 'N/A')),
            ("1.3", "Date of Birth", data.get('dob', 'N/A')),
            ("1.4", "Father's Name", data.get('father_name', 'N/A')),
            ("1.5", "District", data.get('district', 'N/A')),
            ("1.6", "PIN Code", data.get('pin_code', 'N/A')),
        ]
        
        for serial, label, value in personal_info:
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(70, y_position, f"{serial}")
            pdf.setFont("Helvetica", 10)
            pdf.drawString(110, y_position, f"{label}:")
            pdf.drawString(280, y_position, str(value))
            y_position -= 20
        
        y_position -= 20
        
        # Transaction Details Section
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y_position, "2. TRANSACTION DETAILS")
        y_position -= 30
        
        transactions = data.get('transactions', [])
        
        for idx, trans in enumerate(transactions, 1):
            # Check if we need a new page
            if y_position < 100:
                pdf.showPage()
                y_position = height - 50
            
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(70, y_position, f"Transaction #{idx}")
            y_position -= 25
            
            pdf.setFont("Helvetica", 10)
            trans_details = [
                (f"2.{idx}.1", "Date", trans.get('date', 'N/A')),
                (f"2.{idx}.2", "Time", trans.get('time', 'N/A')),
                (f"2.{idx}.3", "Bank Name", trans.get('bank_name', 'N/A')),
                (f"2.{idx}.4", "Bank Account No", trans.get('account_no', 'N/A')),
                (f"2.{idx}.5", "Amount", trans.get('amount', 'N/A')),
                (f"2.{idx}.6", "Transaction ID", trans.get('transaction_id', 'N/A')),
            ]
            
            for serial, label, value in trans_details:
                pdf.setFont("Helvetica-Bold", 9)
                pdf.drawString(90, y_position, f"{serial}")
                pdf.setFont("Helvetica", 9)
                pdf.drawString(140, y_position, f"{label}:")
                pdf.drawString(280, y_position, str(value))
                y_position -= 18
            
            y_position -= 15
        
        # Footer
        y_position -= 20
        if y_position < 100:
            pdf.showPage()
            y_position = height - 50
        
        pdf.line(50, y_position, width - 50, y_position)
        y_position -= 20
        
        # Use regular Helvetica instead of Helvetica-Italic
        pdf.setFont("Helvetica", 9)
        pdf.drawString(50, y_position, f"Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")
        pdf.drawString(50, y_position - 15, "This is a computer-generated document for cyber crime complaint registration.")
        
        # Save the PDF
        pdf.save()
        
        buffer.seek(0)
        return buffer
