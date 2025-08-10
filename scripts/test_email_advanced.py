#!/usr/bin/env python3
import os
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
import sys
import traceback
import time

def test_smtp_connection():
    """Test basic TCP connection to SMTP server"""
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    print(f"🔌 Testing TCP connection to {smtp_server}:{smtp_port}...")
    
    try:
        sock = socket.create_connection((smtp_server, smtp_port), timeout=30)
        sock.close()
        print(f"✅ TCP connection successful to {smtp_server}:{smtp_port}")
        return True
    except Exception as e:
        print(f"❌ TCP connection failed: {e}")
        return False

def get_smtp_config_suggestions():
    """Get SMTP configuration suggestions based on email domain"""
    smtp_user = os.getenv('SMTP_USER', '')
    domain = smtp_user.split('@')[-1].lower() if '@' in smtp_user else ''
    
    configs = {
        'outlook.com': {'server': 'smtp.office365.com', 'port': 587, 'tls': True},
        'hotmail.com': {'server': 'smtp.office365.com', 'port': 587, 'tls': True},
        'live.com': {'server': 'smtp.office365.com', 'port': 587, 'tls': True},
        'gmail.com': {'server': 'smtp.gmail.com', 'port': 587, 'tls': True},
        'qq.com': {'server': 'smtp.qq.com', 'port': 587, 'tls': True},
        '163.com': {'server': 'smtp.163.com', 'port': 25, 'tls': True},
        'yahoo.com': {'server': 'smtp.mail.yahoo.com', 'port': 587, 'tls': True},
    }
    
    if domain in configs:
        suggested = configs[domain]
        print(f"💡 Recommended config for {domain}:")
        print(f"   Server: {suggested['server']}")
        print(f"   Port: {suggested['port']}")
        print(f"   TLS: {suggested['tls']}")
        return suggested
    
    return None

def send_email_test():
    try:
        # SMTP config check with debugging
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')
        recipient_email = os.getenv('RECIPIENT_EMAIL') or smtp_user
        sender_name = os.getenv('SENDER_NAME', 'Credit Research Bot (Advanced Test)')
        test_message = os.getenv('TEST_MESSAGE', 'This is an advanced test email with detailed diagnostics.')

        print(f"🔍 Advanced SMTP Configuration Debug:")
        print(f"  SMTP_SERVER: {smtp_server if smtp_server else '❌ Missing'}")
        print(f"  SMTP_PORT: {smtp_port}")
        print(f"  SMTP_USER: {smtp_user if smtp_user else '❌ Missing'}")
        print(f"  SMTP_PASSWORD: {'✅ Set' if smtp_password else '❌ Missing'}")
        print(f"  RECIPIENT_EMAIL: {recipient_email if recipient_email else '❌ Missing'}")
        print(f"  Environment: GitHub Actions" if 'GITHUB_ACTIONS' in os.environ else f"  Environment: Local")

        if not all([smtp_server, smtp_user, smtp_password, recipient_email]):
            print("⚠️ Incomplete SMTP config, cannot proceed")
            return False

        # Get configuration suggestions
        get_smtp_config_suggestions()
        
        # Test basic TCP connection first
        if not test_smtp_connection():
            print("❌ Basic TCP connection failed - likely firewall/network issue")
            return False

        # Create email
        msg = MIMEMultipart()
        msg['From'] = formataddr((sender_name, smtp_user))
        msg['To'] = recipient_email
        msg['Subject'] = "Advanced Credit Research SMTP Test"

        # Include diagnostics in email body
        email_body = f"""
{test_message}

=== SMTP Test Diagnostics ===
Server: {smtp_server}:{smtp_port}
User: {smtp_user}
Environment: {"GitHub Actions" if 'GITHUB_ACTIONS' in os.environ else "Local"}
Test Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC')}
        """
        
        msg.attach(MIMEText(email_body.strip(), 'plain', 'utf-8'))

        # Multiple connection strategies with different timeouts
        connection_strategies = [
            (120, "Extended timeout (2min)"),
            (60, "Standard timeout (1min)"),
            (30, "Quick timeout (30s)")
        ]

        smtp_methods = []
        if smtp_port == 465:
            smtp_methods.append(('SMTP_SSL', lambda timeout: smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=timeout)))
        elif smtp_port == 587:
            smtp_methods.append(('SMTP+STARTTLS', lambda timeout: smtplib.SMTP(smtp_server, smtp_port, timeout=timeout)))
        else:
            smtp_methods.extend([
                ('SMTP+STARTTLS', lambda timeout: smtplib.SMTP(smtp_server, smtp_port, timeout=timeout)),
                ('SMTP_SSL', lambda timeout: smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=timeout))
            ])

        last_error = None
        
        for timeout, timeout_desc in connection_strategies:
            print(f"\n🕐 Trying {timeout_desc}...")
            
            for method_name, server_factory in smtp_methods:
                try:
                    print(f"🔗 {method_name} connection to {smtp_server}:{smtp_port} (timeout: {timeout}s)")
                    
                    with server_factory(timeout) as server:
                        server.set_debuglevel(1)  # Show all SMTP conversation
                        
                        if method_name == 'SMTP+STARTTLS':
                            print("🔐 Starting TLS encryption...")
                            server.starttls()
                            print("✅ TLS encryption started")
                        
                        print("🔑 Attempting login...")
                        server.login(smtp_user, smtp_password)
                        print("✅ SMTP authentication successful!")
                        
                        print("📨 Sending message...")
                        server.send_message(msg)
                        print("✅ EMAIL SENT SUCCESSFULLY!")
                        
                        return True  # Success!

                except smtplib.SMTPAuthenticationError as e:
                    last_error = f"Authentication failed: {e}"
                    print(f"❌ {method_name}: {last_error}")
                    print("💡 Check: Email/password correct? App-specific password needed?")
                    break  # Don't retry other methods for auth errors
                    
                except smtplib.SMTPConnectError as e:
                    last_error = f"Connection refused: {e}"
                    print(f"❌ {method_name}: {last_error}")
                    continue
                    
                except smtplib.SMTPServerDisconnected as e:
                    last_error = f"Server disconnected: {e}"
                    print(f"❌ {method_name}: {last_error}")
                    continue
                    
                except (ConnectionRefusedError, OSError, socket.timeout) as e:
                    last_error = f"Network error: {e}"
                    print(f"❌ {method_name}: {last_error}")
                    continue
                    
                except Exception as e:
                    last_error = f"Unexpected error: {e}"
                    print(f"❌ {method_name}: {last_error}")
                    continue
        
        # If we get here, all methods failed
        print(f"\n❌ ALL CONNECTION METHODS FAILED")
        print(f"🔍 Last error: {last_error}")
        
        # Provide troubleshooting suggestions
        print(f"\n🔧 TROUBLESHOOTING SUGGESTIONS:")
        print(f"1. If using Outlook/Office365:")
        print(f"   - Enable 'SMTP AUTH' in your account settings")
        print(f"   - Use app-specific password if MFA is enabled")
        print(f"2. If using Gmail:")
        print(f"   - Enable 'Less secure app access' OR use app password")
        print(f"3. If in GitHub Actions:")
        print(f"   - Some email providers block cloud server IPs")
        print(f"   - Consider using SendGrid, Mailgun, or SES instead")
        print(f"4. Check firewall/network restrictions")
        
        return False

    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        print(f"🔍 Full traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Advanced SMTP Connection Test")
    print("=" * 50)
    
    if send_email_test():
        print("\n✅ EMAIL TEST PASSED - SMTP configuration is working!")
        sys.exit(0)
    else:
        print("\n❌ EMAIL TEST FAILED - Check configuration and troubleshooting suggestions")
        sys.exit(1)