import smtplib
from email.mime.text import MIMEText

def send_breach_alert(target_ip, threshold_limit):
    """Securely dispatches an email notification via SMTP."""
    
    # --- CONFIGURATION ---
    sender_email = "sadikouhak@gmail.com" 
    app_password = "PASSWORD_TO_SEND_EMAIL"
    receiver_email = "sadikouhak@gmail.com"
    
    # --- ASSEMBLE THE PAYLOAD ---
    body = (
        f"🚨 SMART ROUTER IPS ALERT 🚨\n\n"
        f"Target IP: {target_ip}\n"
        f"Violation: Exceeded rate limit of {threshold_limit} packets per 10 seconds.\n"
        f"Action Taken: 50% Packet Destruction (Bandwidth Throttling).\n"
        f"Duration: 5 minutes.\n\n"
        f"Review your dashboard for more details."
    )
    
    msg = MIMEText(body)
    msg['Subject'] = f"Threat Neutralized: {target_ip} Throttled"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    # --- TRANSMIT ---
    try:
        # Port 465 uses an implicit SSL/TLS encrypted tunnel
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.send_message(msg)
        print(f"[+] Secure alert dispatched to {receiver_email} regarding {target_ip}")
    except Exception as e:
        print(f"[-] Alert dispatch failed: {e}")

if __name__ == "__main__":
    print("[*] Testing SMTP connection...")
    # send_breach_alert("192.168.137.99", 500) # Test alert for a hypothetical breach scenario