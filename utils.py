"""
Utility Functions
"""
import re
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logger = logging.getLogger(__name__)

def hash_password(password):
    """Hash a password using werkzeug security"""
    return generate_password_hash(password, method='pbkdf2:sha256')

def verify_password(password_hash, password):
    """Verify a password against its hash"""
    return check_password_hash(password_hash, password)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_username(username):
    """Validate username (3-20 chars, alphanumeric + underscore)"""
    if not username or len(username) < 3 or len(username) > 20:
        return False
    return re.match(r'^[a-zA-Z0-9_]+$', username) is not None

def validate_password(password):
    """Validate password strength (min 6 chars)"""
    return password and len(password) >= 6

def validate_phone(phone):
    """Validate phone number"""
    pattern = r'^[0-9]{10}$'
    return re.match(pattern, phone) is not None

def format_currency(amount):
    """Format amount as currency"""
    return f"₹{amount:,.2f}"

def truncate_text(text, length=100):
    """Truncate text to specified length"""
    if len(text) > length:
        return text[:length] + "..."
    return text

def get_safe_filename(filename):
    """Get a safe filename by removing special characters"""
    filename = re.sub(r'[^\w\s-]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename.lower()
