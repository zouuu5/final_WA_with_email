import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import formatdate
from email import encoders
import dotenv
import streamlit as st

def load_email_config():
    """Load email configuration from environment file"""
    dotenv.load_dotenv("email.env")
    
    email_config = {
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', 587)),
        'sender_email': os.getenv('SENDER_EMAIL'),
        'sender_password': os.getenv('SENDER_PASSWORD')
    }
    
    return email_config

def send_pdf_report(recipient_email, pdf_buffer, filename, user_name=None):
    """
    Send the PDF report to the specified email address
    
    Args:
        recipient_email (str): The email address to send the report to
        pdf_buffer (BytesIO): The PDF report data
        filename (str): The filename for the attachment
        user_name (str, optional): The name of the user
    
    Returns:
        tuple: (success, message)
    """
    try:
        email_config = load_email_config()
        
        if not email_config['sender_email'] or not email_config['sender_password']:
            return False, "Email configuration is missing. Please contact the administrator."
        
        # Create message container
        msg = MIMEMultipart()
        msg['From'] = email_config['sender_email']
        msg['To'] = recipient_email
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = f"Your WhatsApp Chat Analysis Report"
        
        # Email body
        greeting = f"Hello {user_name}" if user_name else "Hello"
        body = f"""{greeting},

Attached is your WhatsApp Chat Analysis Report that you requested from my analysis tool.

Thank you for using my service!
-Bhoomika 

"""
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach the PDF
        pdf_buffer.seek(0)  # Reset buffer pointer to the beginning
        attachment = MIMEBase('application', 'pdf')
        attachment.set_payload(pdf_buffer.read())
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(attachment)
        
        # Connect to server and send email
        server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
        server.starttls()  # Secure the connection
        server.login(email_config['sender_email'], email_config['sender_password'])
        server.send_message(msg)
        server.quit()
        
        return True, "Report sent successfully to your email address!"
    
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def test_email_configuration():
    """Test if email configuration is properly set up"""
    config = load_email_config()
    if not config['sender_email'] or not config['sender_password']:
        return False
    return True