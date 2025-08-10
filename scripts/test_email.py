#!/usr/bin/env python3
"""
Email sending test script
Uses identical code as unified_research_analysis.py for consistency
"""

import os
import smtplib
import traceback
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

def test_email_sending():
    """Test email sending with exact same code as unified-research-analysis"""
    try:
        test_message = os.getenv('TEST_MESSAGE', 'This is a test email from Credit Research workflow system.')
        recipient_email = os.getenv('RECIPIENT_EMAIL', '')
        sender_name = os.getenv('SENDER_NAME', 'Credit Research Bot (Test)')
        
        # SMTP config check with debugging (SAME AS MAIN WORKFLOW)
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        
        print(f"🔍 SMTP Config Debug:")
        print(f"  SMTP_SERVER: {'✅ Set' if smtp_server else '❌ Missing'}")
        print(f"  SMTP_PORT: {smtp_port}")
        print(f"  SMTP_USER: {'✅ Set' if smtp_user else '❌ Missing'}")
        print(f"  SMTP_PASSWORD: {'✅ Set' if smtp_password else '❌ Missing'}")
        
        if not all([smtp_server, smtp_user, smtp_password]):
            print("⚠️ Incomplete SMTP config, cannot send test email")
            print("📋 Required GitHub Secrets:")
            print("  - SMTP_SERVER (e.g., smtp.gmail.com)")
            print("  - SMTP_USER (your email address)")  
            print("  - SMTP_PASSWORD (app-specific password)")
            print("  - SMTP_PORT (usually 587)")
            return False
        
        # Use default recipient if none provided
        if not recipient_email:
            recipient_email = smtp_user  # Send to self as test
        
        # Create email (SAME AS MAIN WORKFLOW)
        msg = MIMEMultipart()
        msg['From'] = formataddr((sender_name, smtp_user))
        msg['To'] = recipient_email
        msg['Subject'] = f"Email Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Email content
        email_body = f"""
📧 Email Sending Test

🕒 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
📝 Message: {test_message}
🔧 SMTP Server: {smtp_server}:{smtp_port}
👤 From: {smtp_user}
📨 To: {recipient_email}

✅ If you receive this email, SMTP configuration is working correctly!

---
This is an automated test email from the Credit Research workflow system.
"""
        
        msg.attach(MIMEText(email_body, 'plain', 'utf-8'))
        
        # Send email with improved connection handling (SAME AS MAIN WORKFLOW)
        print(f"📤 Sending test email to {msg['To']}...")
        
        # Try different SMTP approaches based on server
        smtp_methods = []
        
        if smtp_port == 465:
            # SSL connection for port 465
            smtp_methods.append(('SMTP_SSL', lambda: smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=60)))
        elif smtp_port == 587:
            # STARTTLS for port 587
            smtp_methods.append(('SMTP+STARTTLS', lambda: smtplib.SMTP(smtp_server, smtp_port, timeout=60)))
        else:
            # Try both methods for unknown ports
            smtp_methods.extend([
                ('SMTP+STARTTLS', lambda: smtplib.SMTP(smtp_server, smtp_port, timeout=60)),
                ('SMTP_SSL', lambda: smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=60))
            ])
        
        last_error = None
        for method_name, server_factory in smtp_methods:
            try:
                print(f"🔗 Trying {method_name} connection to {smtp_server}:{smtp_port}")
                
                with server_factory() as server:
                    server.set_debuglevel(1)  # Enable detailed SMTP debug output
                    
                    # Only call starttls for non-SSL connections
                    if method_name == 'SMTP+STARTTLS':
                        print("🔐 Starting TLS encryption")
                        server.starttls()
                    
                    print("🔑 Attempting login")
                    server.login(smtp_user, smtp_password)
                    print("✅ SMTP login successful")
                    
                    print("📨 Sending test message")
                    server.send_message(msg)
                    print("📨 Test message sent successfully")
                    break  # Success, exit loop
                    
            except smtplib.SMTPAuthenticationError as e:
                last_error = f"SMTP Authentication failed: {e}"
                print(f"❌ {method_name}: {last_error}")
                break  # Auth error, don't retry other methods
            except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, ConnectionRefusedError, OSError) as e:
                last_error = f"SMTP Connection failed ({method_name}): {e}"
                print(f"⚠️ {method_name}: {last_error}")
                continue  # Try next method
            except Exception as e:
                last_error = f"SMTP Error ({method_name}): {e}"
                print(f"❌ {method_name}: {last_error}")
                continue  # Try next method
        else:
            # All methods failed
            raise Exception(last_error or "All SMTP connection methods failed")
        
        print("✅ Test email sent successfully!")
        print(f"📧 Email delivered to: {recipient_email}")
        print("🎉 SMTP configuration is working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Email test failed: {e}")
        print("🔍 Full error details:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Starting Email Sending Test...")
    success = test_email_sending()
    
    if success:
        print("\n✅ EMAIL TEST PASSED")
        print("The same email code should work in unified-research-analysis.yml")
    else:
        print("\n❌ EMAIL TEST FAILED") 
        print("Check SMTP configuration and GitHub Secrets")
        exit(1)