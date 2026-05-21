import os
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import uuid

VERIFICATION_TOKEN_EXPIRY_HOURS = int(os.getenv('VERIFICATION_TOKEN_EXPIRY_HOURS', '24'))
BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')

SMTP_HOST = os.getenv('SMTP_HOST', '')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_FROM = os.getenv('SMTP_FROM', 'noreply@educare.com')

EMAIL_MODE = os.getenv('EMAIL_MODE', 'smtp')

# ---- In-memory rate limiter: max 3 emails per hour per email address ----
_MAX_PER_HOUR = int(os.getenv('VERIFICATION_EMAILS_PER_HOUR', '3'))
_WINDOW = timedelta(hours=1)

_rate_lock = threading.Lock()
_send_log: dict[str, list[datetime]] = {}   # email -> list of send timestamps


class RateLimitError(Exception):
    """Raised when the per-email rate limit is exceeded."""
    pass


def _prune(history: list[datetime], now: datetime) -> list[datetime]:
    return [t for t in history if now - t <= _WINDOW]


def check_rate_limit(email: str) -> bool:
    """Return True if sending is allowed; False if rate limit exceeded."""
    now = datetime.now()
    with _rate_lock:
        hist = _send_log.get(email, [])
        hist = _prune(hist, now)
        _send_log[email] = hist
        return len(hist) < _MAX_PER_HOUR


def record_send(email: str) -> None:
    with _rate_lock:
        hist = _send_log.get(email, [])
        hist.append(datetime.now())
        _send_log[email] = hist


def get_rate_limit_remaining(email: str) -> int:
    """Return how many more emails can be sent in the current window."""
    now = datetime.now()
    with _rate_lock:
        hist = _send_log.get(email, [])
        hist = _prune(hist, now)
        _send_log[email] = hist
        return max(0, _MAX_PER_HOUR - len(hist))


def get_rate_limit_reset_in(email: str) -> int | None:
    """Return seconds until the rate-limit window resets (first old entry expires)."""
    now = datetime.now()
    with _rate_lock:
        hist = _send_log.get(email, [])
        hist = _prune(hist, now)
        _send_log[email] = hist
        if len(hist) < _MAX_PER_HOUR:
            return None
        oldest = min(hist)
        reset = (oldest + _WINDOW) - now
        return max(0, int(reset.total_seconds()))


def send_with_rate_limit(email: str, subject: str, html_body: str, text_body: str = "") -> bool:
    """Apply rate-limit check, record the send, then dispatch the real email."""
    if EMAIL_MODE == 'console':
        # Dev mode: only honour the rate limit so tests stay realistic
        if not check_rate_limit(email):
            raise RateLimitError(
                f"Rate limit exceeded for {email}- Max {_MAX_PER_HOUR} emails per hour."
            )
        record_send(email)
        print(f"\n{'='*60}")
        print(f"EMAIL ({EMAIL_MODE.upper()} MODE)")
        print(f"To: {email}")
        print(f"Subject: {subject}")
        print(f"{'='*60}")
        return True

    if not SMTP_HOST or not SMTP_USER:
        raise ValueError(
            "SMTP credentials not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, and SMTP_PASSWORD environment variables."
        )

    if not check_rate_limit(email):
        raise RateLimitError(
            f"Rate limit exceeded for {email}. Max {_MAX_PER_HOUR} emails per hour."
        )
    record_send(email)

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SMTP_FROM
        msg['To'] = email
        if text_body:
            msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM, email, msg.as_string())
        server.quit()
        return True
    except RateLimitError:
        raise
    except Exception as e:
        print(f"Error sending email to {email}: {e}")
        return False

def generate_verification_token():
    return uuid.uuid4().hex + uuid.uuid4().hex

def get_token_expiry():
    return datetime.now() + timedelta(hours=VERIFICATION_TOKEN_EXPIRY_HOURS)

def send_verification_email(email, full_name, token):
    """Send verification email to user."""
    verification_url = f"{BASE_URL}/verify-email?token={token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
        <div style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); padding: 20px; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0;">EDUCARE</h1>
        </div>
        
        <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e5e7eb; border-top: none;">
            <h2 style="color: #1f2937; margin-top: 0;">Verify Your Email Address</h2>
            
            <p>Hello <strong>{full_name}</strong>,</p>
            
            <p>Thank you for registering with EDUCARE! To complete your registration, please verify your email address by clicking the button below:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}" style="display: inline-block; background: #2563eb; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">Verify Email Address</a>
            </div>
            
            <p style="font-size: 14px; color: #6b7280;">
                Or copy and paste this link into your browser:<br>
                <a href="{verification_url}" style="color: #2563eb;">{verification_url}</a>
            </p>
            
            <div style="background: #fef3c7; border: 1px solid #f59e0b; border-radius: 6px; padding: 15px; margin: 20px 0;">
                <p style="margin: 0; font-size: 14px; color: #92400e;">
                    <strong>Important:</strong> This verification link will expire in {VERIFICATION_TOKEN_EXPIRY_HOURS} hours. If you didn't create an account with EDUCARE, you can safely ignore this email.
                </p>
            </div>
            
            <p style="font-size: 14px; color: #6b7280; margin-top: 30px;">
                Best regards,<br>
                The EDUCARE Team
            </p>
        </div>
        
        <div style="text-align: center; padding: 20px; color: #9ca3af; font-size: 12px;">
            <p>This is an automated message from EDUCARE. Please do not reply to this email.</p>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    Hello {full_name},
    
    Thank you for registering with EDUCARE! To complete your registration, please verify your email address by visiting this link:
    
    {verification_url}
    
    This verification link will expire in {VERIFICATION_TOKEN_EXPIRY_HOURS} hours. If you didn't create an account with EDUCARE, you can safely ignore this email.
    
    Best regards,
    The EDUCARE Team
    """
    
    ok = send_with_rate_limit(
        email,
        subject='Verify Your Email - EDUCARE',
        html_body=html_content,
        text_body=text_content
    )
    return ok

def send_welcome_email(email, full_name, role):
    """Send welcome email after verification."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
        <div style="background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%); padding: 20px; border-radius: 10px 10px 0 0;">
            <h1 style="color: white; margin: 0;">EDUCARE</h1>
        </div>
        <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e5e7eb; border-top: none;">
            <h2 style="color: #1f2937;">Welcome to EDUCARE, {full_name}!</h2>
            <p>Your email has been verified successfully. You can now log in as a <strong>{role}</strong>.</p>
            <p>Log in at: <a href="{BASE_URL}">{BASE_URL}</a></p>
        </div>
    </body>
    </html>
    """
    
    return send_with_rate_limit(
        email,
        subject=f'Welcome to EDUCARE!',
        html_body=html_content,
    )