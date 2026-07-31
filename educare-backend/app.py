from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
import pymysql

import random
import json
import os
from datetime import datetime, timedelta
import re
import secrets
import traceback

# Simple .env loader (no extra deps)
def load_dotenv_file(path='.env'):
    if not os.path.exists(path):
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k, v = k.strip(), v.strip().strip('"\'')
                if k and v and k not in os.environ:
                    os.environ[k] = v
    except Exception:
        pass

load_dotenv_file()
load_dotenv_file(os.path.join(os.path.dirname(__file__), '.env'))

# Debug: print email config (without password)
print(f"[DEBUG] EMAIL_MODE: {os.getenv('EMAIL_MODE')}")
print(f"[DEBUG] SMTP_HOST: {os.getenv('SMTP_HOST')}")
print(f"[DEBUG] SMTP_USER: {os.getenv('SMTP_USER')}")
print(f"[DEBUG] SMTP_FROM: {os.getenv('SMTP_FROM')}")
print(f"[DEBUG] BASE_URL: {os.getenv('BASE_URL')}")

# ==================== FAISS IMPORT ====================
FAISS_AVAILABLE = True
try:
    import faiss
    print(f"[DEBUG] FAISS imported successfully, version: {faiss.__version__}")
except ImportError as e:
    FAISS_AVAILABLE = False
    print(f"[DEBUG] FAISS import failed: {e}")

try:
    import pickle
    print("[DEBUG] Pickle imported successfully")
except ImportError as e:
    import pickle as pickle
    print(f"[DEBUG] Pickle import failed: {e}")

try:
    import numpy as np
    print("[DEBUG] NumPy imported successfully")
except ImportError as e:
    np = None
    print(f"[DEBUG] NumPy import failed: {e}")

# bcrypt for password hashing - define placeholder first, then import
bcrypt = None
BCRYPT_AVAILABLE = False
try:
    import bcrypt
    if bcrypt:
        BCRYPT_AVAILABLE = True
        print("[DEBUG] bcrypt imported successfully")
except ImportError as e:
    print(f"[DEBUG] bcrypt import failed: {e}")

# Email service (real SMTP verification + OTP)
try:
    from email_service import (
        send_verification_email,
        send_welcome_email,
        send_password_reset_otp,
        generate_verification_token,
        get_token_expiry,
    )
    EMAIL_AVAILABLE = True
    print("[DEBUG] Email service imported successfully")
except Exception as e:
    print(f"Warning: email_service not available: {e}")
    EMAIL_AVAILABLE = False
    def send_verification_email(*a, **k): return False
    def send_welcome_email(*a, **k): return False
    def send_password_reset_otp(*a, **k): return False
    def generate_verification_token(): return os.urandom(32).hex()
    def get_token_expiry(): return datetime.now() + timedelta(hours=24)

app = Flask(__name__)

# ==================== HEALTH CHECK ====================
@app.route('/health')
def health():
    return jsonify({"status": "healthy", "message": "EDUCARE API is running!"})

# ==================== CORS CONFIGURATION ====================
CORS(app, resources={r"/*": {"origins": "*"}})

# ==================== JWT CONFIGURATION ====================
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'educare-secret-key')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # tokens don't expire in dev
jwt = JWTManager(app)

# Database configuration (overrideable via .env)
db_config = {
    'host': os.getenv('DB_HOST', os.getenv('MYSQL_HOST', 'localhost')),
    'user': os.getenv('DB_USER', os.getenv('MYSQL_USER', 'root')),
    'password': os.getenv('DB_PASSWORD', os.getenv('MYSQL_PASSWORD', '')),
    'database': os.getenv('DB_NAME', os.getenv('MYSQL_DB', 'railway')),
    'port': int(os.getenv('DB_PORT', os.getenv('MYSQL_PORT', 3306))),
    'charset': 'utf8mb4',
}
def get_db_connection():
    return pymysql.connect(**db_config)

# ==================== STRONG PASSWORD RULES ====================
PASSWORD_RULES = {
    'min_length': 8,
    'max_length': 20,
    'require_upper': True,
    'require_lower': True,
    'require_digit': True,
    'require_special': True,
    'special_chars': '!@#$%^&*'
}

def validate_strong_password(password):
    """Return (is_valid: bool, errors: list, strength: str)"""
    errors = []
    if not password:
        return False, ['Password is required'], 'Weak'
    length = len(password)
    if length < PASSWORD_RULES['min_length']:
        errors.append(f'At least {PASSWORD_RULES["min_length"]} characters')
    if length > PASSWORD_RULES['max_length']:
        errors.append(f'At most {PASSWORD_RULES["max_length"]} characters')
    if PASSWORD_RULES['require_upper'] and not re.search(r'[A-Z]', password):
        errors.append('At least 1 uppercase letter (A-Z)')
    if PASSWORD_RULES['require_lower'] and not re.search(r'[a-z]', password):
        errors.append('At least 1 lowercase letter (a-z)')
    if PASSWORD_RULES['require_digit'] and not re.search(r'[0-9]', password):
        errors.append('At least 1 number (0-9)')
    if PASSWORD_RULES['require_special'] and not re.search(r'[!@#$%^&*]', password):
        errors.append('At least 1 special character (!@#$%^&*)')
    
    # Strength meter
    score = 0
    if length >= 8: score += 1
    if length >= 12: score += 1
    if re.search(r'[A-Z]', password): score += 1
    if re.search(r'[a-z]', password): score += 1
    if re.search(r'[0-9]', password): score += 1
    if re.search(r'[!@#$%^&*]', password): score += 1
    if length >= 16: score += 1
    
    if score <= 2:
        strength = 'Weak'
    elif score <= 4:
        strength = 'Medium'
    else:
        strength = 'Strong'
    
    return len(errors) == 0, errors, strength


def require_role(*allowed_roles):
    """Return (identity, error_response) tuple. error_response is None if OK."""
    identity = get_jwt_identity()
    if not identity:
        return None, (jsonify({"error": "Authentication required"}), 401)
    if identity.get('role') not in allowed_roles:
        return None, (jsonify({"error": "Access denied: insufficient permissions"}), 403)
    return identity, None


ALLOWED_TEACHER_GRADES = (9, 10, 11, 12)


def parse_teacher_grade(value):
    """Validate teacher assigned grade (9–12). Returns int or None."""
    if value is None or str(value).strip() == '':
        return None
    try:
        grade = int(value)
    except (TypeError, ValueError):
        return None
    return grade if grade in ALLOWED_TEACHER_GRADES else None


def get_teacher_grade(cursor, user_id):
    """Return assigned grade for a teacher user, or None."""
    cursor.execute("SELECT grade_level FROM teachers WHERE user_id = %s", (user_id,))
    row = cursor.fetchone()
    if not row or row[0] is None:
        return None
    return int(row[0])


def student_in_grade(cursor, student_user_id, grade_level):
    cursor.execute(
        "SELECT 1 FROM students WHERE user_id = %s AND grade_level = %s",
        (student_user_id, grade_level),
    )
    return cursor.fetchone() is not None

# ==================== DATABASE SETUP ====================

# Create teachers table if it doesn't exist
def init_teachers_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                qualification VARCHAR(255),
                subject VARCHAR(255),
                grade_level INT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE KEY unique_teacher (user_id)
            )
        """)
        try:
            cursor.execute("SHOW COLUMNS FROM teachers LIKE 'grade_level'")
            if not cursor.fetchone():
                cursor.execute(
                    "ALTER TABLE teachers ADD COLUMN grade_level INT NULL AFTER subject"
                )
        except Exception as col_err:
            print(f"Note: teachers.grade_level column: {col_err}")
        conn.commit()
        cursor.close()
        conn.close()
        print("Teachers table initialized successfully")
    except Exception as e:
        print(f"Error initializing teachers table: {e}")

# Create family table if it doesn't exist
def init_family_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS family (
                family_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                student_id INT NOT NULL,
                relationship VARCHAR(50) DEFAULT 'parent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                -- student_id references students.student_id (canonical PK)
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                UNIQUE KEY unique_family_student (user_id, student_id)
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("Family table initialized successfully")
    except Exception as e:
        print(f"Error initializing family table: {e}")

# Initialize tables on startup
init_teachers_table()
init_family_table()

# ── Assistant conversations table ─────────────────────────────────────
def init_assistant_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assistant_conversations (
                conversation_id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                user_message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                source_citation VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
            )
        """)
        try:
            cursor.execute(
                "CREATE INDEX idx_assistant_conversations_student_id "
                "ON assistant_conversations(student_id)"
            )
        except Exception:
            pass
        conn.commit()
        cursor.close()
        conn.close()
        print("Assistant conversations table initialized successfully")
    except Exception as e:
        print(f"Error initializing assistant table: {e}")

init_assistant_table()


def init_student_materials_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        import material_delivery as delivery
        delivery.ensure_student_materials_table(cursor)
        delivery.ensure_generation_history_material_id(cursor)
        fk_fixed = delivery.repair_student_materials_fk_values(cursor)
        repaired = delivery.repair_overassigned_materials(cursor)
        unassigned = delivery.repair_unassigned_pending_materials(cursor)
        conn.commit()
        cursor.close()
        conn.close()
        print("student_materials table initialized successfully")
        if fk_fixed:
            print(f"Repaired {fk_fixed} student_materials FK value(s)")
        if repaired:
            print(f"Repaired {repaired} over-assigned material(s)")
        if unassigned:
            print(f"Repaired {unassigned} unassigned pending material(s)")
    except Exception as e:
        print(f"Error initializing student_materials table: {e}")


init_student_materials_table()

# ── Auth enhancements: profile_picture + password_resets OTP table ─────
def init_auth_enhancements():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # profile_picture
        cursor.execute("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'users' AND COLUMN_NAME = 'profile_picture'
        """, (db_config['database'],))
        if cursor.fetchone()[0] == 0:
            cursor.execute("ALTER TABLE users ADD COLUMN profile_picture VARCHAR(512) NULL AFTER email")
            print("Added profile_picture column to users")
        
        # password_resets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_resets (
                reset_id   INT AUTO_INCREMENT PRIMARY KEY,
                email      VARCHAR(255) NOT NULL,
                otp        VARCHAR(6) NOT NULL,
                expires_at DATETIME NOT NULL,
                attempts   INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_pr_email (email),
                INDEX idx_pr_expiry (expires_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("Auth enhancements (profile + OTP resets) initialized")
    except Exception as e:
        print(f"Warning: could not init auth enhancements: {e}")

init_auth_enhancements()

# ==================== BASIC ENDPOINTS ====================

@app.route('/')
def home():
    return jsonify({"message": "EDUCARE API is running!"})

@app.route('/test-db')
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return jsonify({"status": "Connected to MySQL!", "users_count": count})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/users')
def get_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, full_name, email, role FROM users")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        users_list = []
        for user in users:
            users_list.append({
                'user_id': user[0],
                'full_name': user[1],
                'email': user[2],
                'role': user[3]
            })
        
        return jsonify({"users": users_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== STUDENT ENDPOINTS ====================

@app.route('/api/students', methods=['GET'])
def get_students():
    try:
        grade_level = parse_teacher_grade(request.args.get('grade_level'))
        conn = get_db_connection()
        cursor = conn.cursor()
        if grade_level is not None:
            cursor.execute("""
                SELECT u.user_id, u.full_name, u.email, s.grade_level, s.section
                FROM users u
                JOIN students s ON u.user_id = s.user_id
                WHERE u.role = 'student' AND s.grade_level = %s
                ORDER BY u.full_name
            """, (grade_level,))
        else:
            cursor.execute("""
                SELECT u.user_id, u.full_name, u.email, s.grade_level, s.section
                FROM users u
                JOIN students s ON u.user_id = s.user_id
                WHERE u.role = 'student'
                ORDER BY u.full_name
            """)
        students = cursor.fetchall()
        students_list = [
            {
                'user_id': student[0],
                'full_name': student[1],
                'email': student[2],
                'grade_level': student[3],
                'section': student[4],
            }
            for student in students
        ]
        cursor.close()
        conn.close()
        return jsonify({"students": students_list})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/students/<int:student_id>/attempts', methods=['GET'])
def get_student_attempts(student_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        from gap_utils import QUIZ_STUDENT_JOIN
        cursor.execute(f"""
            SELECT qa.attempt_id, qa.quiz_id, qa.score, qa.completed_at,
                   q.title, t.topic_name
            FROM quiz_attempt qa
            JOIN quizzes q ON qa.quiz_id = q.quiz_id
            JOIN topics t ON q.topic_id = t.topic_id
            {QUIZ_STUDENT_JOIN}
            WHERE s_qa.user_id = %s
            ORDER BY qa.completed_at DESC
        """, (student_id,))
        attempts = cursor.fetchall()
        cursor.close()
        conn.close()
        
        attempts_list = []
        for attempt in attempts:
            attempts_list.append({
                'attempt_id': attempt[0],
                'quiz_id': attempt[1],
                'score': attempt[2],
                'completed_at': str(attempt[3]),
                'quiz_title': attempt[4],
                'topic': attempt[5]
            })
        
        return jsonify({"attempts": attempts_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/students/<int:student_id>/gaps', methods=['GET'])
def get_student_gaps(student_id):
    """Learning gaps from quiz attempts. student_id path param is users.user_id."""
    try:
        from gap_utils import fetch_student_gaps
        conn = get_db_connection()
        cursor = conn.cursor()
        gaps_list = fetch_student_gaps(cursor, student_id)
        cursor.close()
        conn.close()
        return jsonify({"gaps": gaps_list})
    except Exception as e:
        print(f"Error in /api/students/{student_id}/gaps: {e}")
        return jsonify({"gaps": []}), 200

# ==================== AUTHENTICATION ====================

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, full_name, email, role, password, is_verified FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        stored_password = user[4]
        is_verified = bool(user[5]) if len(user) > 5 else True
        
        # Check password
        password_valid = False
        if stored_password:
            if BCRYPT_AVAILABLE and stored_password.startswith('$2'):
                try:
                    password_valid = bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
                except Exception:
                    password_valid = False
            else:
                # Plain text comparison (fallback)
                password_valid = (password == stored_password)
                # Migrate to bcrypt if available
                if password_valid and BCRYPT_AVAILABLE and bcrypt:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        cursor.execute("UPDATE users SET password = %s WHERE user_id = %s", (new_hash, user[0]))
                        conn.commit()
                        cursor.close()
                        conn.close()
                    except Exception:
                        pass
        
        if not password_valid:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Enforce email verification for login (real email flow)
        if not is_verified:
            return jsonify({
                "error": "Please verify your email before logging in. Check your inbox for the verification link.",
                "requires_verification": True,
                "email": user[2]
            }), 403
        
        access_token = create_access_token(identity={
            'user_id': user[0],
            'role': user[3]
        })

        payload = {
            "user_id": user[0],
            "full_name": user[1],
            "email": user[2],
            "role": user[3],
            "token": access_token,
        }

        if user[3] == 'teacher':
            conn = get_db_connection()
            cursor = conn.cursor()
            assigned_grade = get_teacher_grade(cursor, user[0])
            cursor.execute(
                "SELECT qualification, subject FROM teachers WHERE user_id = %s",
                (user[0],),
            )
            trow = cursor.fetchone()
            cursor.close()
            conn.close()
            if assigned_grade is not None:
                payload["assigned_grade"] = assigned_grade
                payload["grade_level"] = assigned_grade
            if trow:
                payload["qualification"] = trow[0]
                payload["subject"] = trow[1]

        return jsonify(payload), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== REGISTER ENDPOINT ====================
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        print(f"[DEBUG] Registration data received: {data}")
        
        # Get all fields with proper default values
        full_name = data.get('full_name', '').strip() or ''
        email = data.get('email', '').strip()
        username = email
        password = data.get('password', '')
        grade_level = data.get('grade_level')
        section = data.get('section', '').strip()
        
        # Validate required fields
        if not email:
            return jsonify({"error": "Email is required"}), 400
        if not password:
            return jsonify({"error": "Password is required"}), 400
        if not grade_level:
            return jsonify({"error": "Grade level is required"}), 400
        if not section:
            return jsonify({"error": "Section is required"}), 400

        try:
            grade_level = int(grade_level)
        except (ValueError, TypeError):
            return jsonify({"error": "Grade level must be a number"}), 400

        section = str(section).strip()

        # Hash the password using bcrypt
        if BCRYPT_AVAILABLE and bcrypt:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            hashed_password = password

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Email already registered"}), 400

        # Enforce strong password
        is_strong, pw_errors, strength = validate_strong_password(password)
        if not is_strong:
            cursor.close()
            conn.close()
            return jsonify({"error": "Weak password", "errors": pw_errors, "strength": strength}), 400

        # Generate verification token (24h expiry)
        verification_token = generate_verification_token()
        token_expiry = get_token_expiry()

        # DEBUG: Print what we're about to insert
        print(f"[DEBUG] Inserting: username={username}, full_name={full_name}, email={email}")
        print(f"[DEBUG] Values: hashed_password={hashed_password[:10]}..., role=student, is_verified=1")

        # ✅ FIXED: Auto-verified (is_verified = 1)
        cursor.execute(
            """INSERT INTO users 
               (username, full_name, email, password, role, is_verified, verification_token, token_expiry) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (username, full_name, email, hashed_password, 'student', 1, verification_token, token_expiry)
        )
        user_id = int(cursor.lastrowid)

        cursor.execute(
            "INSERT INTO students (user_id, grade_level, section, enrollment_date) VALUES (%s, %s, %s, CURDATE())",
            (user_id, grade_level, section)
        )
        
        conn.commit()
        cursor.close()
        conn.close()

        # No email verification needed
        email_sent = False

        return jsonify({
            "message": "Account created successfully! You can now login.",
            "user_id": user_id,
            "full_name": full_name,
            "email": email,
            "role": "student",
            "email_sent": email_sent,
            "strength": strength
        }), 201
        
    except Exception as e:
        print(f"[ERROR] Registration failed: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ==================== EMAIL VERIFICATION ====================
@app.route('/api/verify-email', methods=['GET', 'POST'])
def verify_email():
    """Verify email using token from link. 24h expiry enforced in DB."""
    try:
        token = request.args.get('token') or (request.get_json() or {}).get('token')
        if not token:
            return jsonify({"error": "Verification token required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT user_id, full_name, email, role, is_verified, token_expiry 
               FROM users WHERE verification_token = %s""",
            (token,)
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid or expired verification link"}), 400
        
        user_id, full_name, email, role, is_verified, token_expiry = row
        
        if is_verified:
            cursor.close()
            conn.close()
            return jsonify({"message": "Email already verified. You can login now.", "already_verified": True}), 200
        
        # Check expiry
        if token_expiry and datetime.now() > token_expiry:
            cursor.close()
            conn.close()
            return jsonify({"error": "Verification link has expired. Please register again or request a new link."}), 400
        
        # Mark verified, clear token
        cursor.execute(
            """UPDATE users SET is_verified = TRUE, verification_token = NULL, token_expiry = NULL 
               WHERE user_id = %s""",
            (user_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Send welcome
        if EMAIL_AVAILABLE:
            try:
                send_welcome_email(email, full_name, role)
            except Exception:
                pass
        
        return jsonify({
            "message": "Email verified successfully! You can now log in.",
            "user_id": user_id,
            "email": email
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== FORGOT PASSWORD + OTP (6-digit, 10min, max 3 attempts) ====================

def _generate_otp():
    return f"{secrets.randbelow(900000) + 100000}"  # 6 digits, no leading zero issue

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip().lower()
        if not email:
            return jsonify({"error": "Email required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, full_name FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            # Don't leak existence
            cursor.close()
            conn.close()
            return jsonify({"message": "If the email exists, an OTP has been sent."}), 200
        
        user_id, full_name = user
        
        # Cleanup expired
        cursor.execute("DELETE FROM password_resets WHERE expires_at < NOW()")
        
        # Check existing active reset attempts (rate-ish)
        cursor.execute(
            "SELECT attempts FROM password_resets WHERE email = %s AND expires_at > NOW() ORDER BY created_at DESC LIMIT 1",
            (email,)
        )
        row = cursor.fetchone()
        if row and row[0] >= 3:
            cursor.close()
            conn.close()
            return jsonify({"error": "Too many attempts. Please wait or request after expiry."}), 429
        
        otp = _generate_otp()
        expires_at = datetime.now() + timedelta(minutes=10)
        
        # Insert new OTP request (old ones expire naturally)
        cursor.execute(
            "INSERT INTO password_resets (email, otp, expires_at, attempts) VALUES (%s, %s, %s, 0)",
            (email, otp, expires_at)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Send email (real)
        sent = False
        if EMAIL_AVAILABLE:
            try:
                sent = send_password_reset_otp(email, full_name, otp)
            except Exception as e:
                print(f"OTP email error: {e}")
        
        return jsonify({
            "message": "If the email exists, an OTP has been sent.",
            "otp_sent": sent,
            "expires_in_minutes": 10
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """Verify 6-digit OTP (max 3 attempts) + set new strong password."""
    try:
        data = request.get_json() or {}
        email = (data.get('email') or '').strip().lower()
        otp = (data.get('otp') or '').strip()
        new_password = data.get('new_password') or ''
        
        if not email or not otp or not new_password:
            return jsonify({"error": "Email, OTP and new password required"}), 400
        
        # Validate new pw strength
        is_strong, pw_errors, strength = validate_strong_password(new_password)
        if not is_strong:
            return jsonify({"error": "Weak password", "errors": pw_errors, "strength": strength}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT reset_id, otp, expires_at, attempts FROM password_resets 
               WHERE email = %s AND expires_at > NOW() 
               ORDER BY created_at DESC LIMIT 1""",
            (email,)
        )
        reset_row = cursor.fetchone()
        if not reset_row:
            cursor.close()
            conn.close()
            return jsonify({"error": "No valid OTP request or it expired. Request a new one."}), 400
        
        reset_id, stored_otp, expires_at, attempts = reset_row
        
        if attempts >= 3:
            cursor.close()
            conn.close()
            return jsonify({"error": "Maximum attempts exceeded for this OTP."}), 429
        
        # Increment attempt
        cursor.execute("UPDATE password_resets SET attempts = attempts + 1 WHERE reset_id = %s", (reset_id,))
        
        if stored_otp != otp:
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid OTP", "attempts_remaining": max(0, 2 - attempts)}), 400
        
        # OTP correct -> hash and update user pw
        if BCRYPT_AVAILABLE and bcrypt:
            hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            hashed = new_password
        
        cursor.execute("UPDATE users SET password = %s WHERE email = %s", (hashed, email))
        
        # Invalidate this reset + old ones
        cursor.execute("DELETE FROM password_resets WHERE email = %s", (email,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Password reset successful. You can now log in with your new password."}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== PROFILE ENDPOINTS ====================
@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        identity = get_jwt_identity()
        user_id = identity.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, full_name, email, role, profile_picture, is_verified FROM users WHERE user_id = %s",
            (user_id,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "user_id": row[0],
            "full_name": row[1],
            "email": row[2],
            "role": row[3],
            "profile_picture": row[4],
            "is_verified": bool(row[5])
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Edit name and/or email. If email changes, optionally force re-verify (here we keep verified if was)."""
    try:
        identity = get_jwt_identity()
        user_id = identity.get('user_id')
        data = request.get_json() or {}
        
        new_name = (data.get('full_name') or '').strip()
        new_email = (data.get('email') or '').strip().lower()
        
        if not new_name and not new_email:
            return jsonify({"error": "Nothing to update"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current
        cursor.execute("SELECT full_name, email FROM users WHERE user_id = %s", (user_id,))
        cur = cursor.fetchone()
        if not cur:
            cursor.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404
        cur_name, cur_email = cur
        
        final_name = new_name or cur_name
        final_email = new_email or cur_email
        
        if new_email and new_email != cur_email:
            cursor.execute("SELECT user_id FROM users WHERE email = %s AND user_id != %s", (new_email, user_id))
            if cursor.fetchone():
                cursor.close()
                conn.close()
                return jsonify({"error": "Email already in use by another account"}), 400
        
        cursor.execute(
            "UPDATE users SET full_name = %s, email = %s WHERE user_id = %s",
            (final_name, final_email, user_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Profile updated successfully", "full_name": final_name, "email": final_email}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/profile/password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change password: requires old + new + confirm, strong rules."""
    try:
        identity = get_jwt_identity()
        user_id = identity.get('user_id')
        data = request.get_json() or {}
        
        old_pw = data.get('old_password') or ''
        new_pw = data.get('new_password') or ''
        confirm = data.get('confirm_password') or ''
        
        if not old_pw or not new_pw or not confirm:
            return jsonify({"error": "old_password, new_password and confirm_password required"}), 400
        if new_pw != confirm:
            return jsonify({"error": "New passwords do not match"}), 400
        
        is_strong, pw_errors, strength = validate_strong_password(new_pw)
        if not is_strong:
            return jsonify({"error": "Weak password", "errors": pw_errors, "strength": strength}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        stored = row[0]
        valid_old = False
        if stored:
            if BCRYPT_AVAILABLE and stored.startswith('$2'):
                try:
                    valid_old = bcrypt.checkpw(old_pw.encode('utf-8'), stored.encode('utf-8'))
                except:
                    valid_old = False
            else:
                valid_old = (old_pw == stored)
        
        if not valid_old:
            cursor.close()
            conn.close()
            return jsonify({"error": "Current password is incorrect"}), 401
        
        # Update to new hash
        if BCRYPT_AVAILABLE and bcrypt:
            new_hash = bcrypt.hashpw(new_pw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            new_hash = new_pw
        
        cursor.execute("UPDATE users SET password = %s WHERE user_id = %s", (new_hash, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Password changed successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Simple profile picture upload (reuses upload logic, stores under uploads/profile/)
@app.route('/api/profile/picture', methods=['POST'])
@jwt_required()
def upload_profile_picture():
    try:
        identity = get_jwt_identity()
        user_id = identity.get('user_id')
        
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files['file']
        if not file.filename:
            return jsonify({"error": "Empty filename"}), 400
        
        # Validate image type for profile
        allowed_ext = {'.jpg', '.jpeg', '.png', '.gif'}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_ext:
            return jsonify({"error": "Only JPG, PNG, GIF allowed for profile pictures"}), 400
        
        # Size limit 5MB
        file.stream.seek(0, 2)
        size = file.stream.tell()
        file.stream.seek(0)
        if size > 5 * 1024 * 1024:
            return jsonify({"error": "Profile picture too large (max 5MB)"}), 400
        
        # Save to uploads/profile/
        profile_dir = os.path.join(os.path.dirname(__file__), 'uploads', 'profile')
        os.makedirs(profile_dir, exist_ok=True)
        unique = f"{datetime.utcnow().strftime('%Y%m%d')}_{os.urandom(6).hex()}_{file.filename[:60]}"
        safe_name = re.sub(r'[^\w.\-]+', '_', unique)
        save_path = os.path.join(profile_dir, safe_name)
        file.save(save_path)
        
        url = f'/uploads/profile/{safe_name}'
        
        # Update DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET profile_picture = %s WHERE user_id = %s", (url, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"profile_picture": url, "message": "Profile picture updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==================== QUIZ ENDPOINTS ====================

@app.route('/api/quizzes', methods=['GET'])
def get_quizzes():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT q.quiz_id, q.title, q.total_marks, q.time_limit, 
                   t.topic_name, t.grade_level
            FROM quizzes q
            JOIN topics t ON q.topic_id = t.topic_id
        """)
        quizzes = cursor.fetchall() or []
        cursor.close()
        conn.close()
        
        quizzes_list = []
        for quiz in quizzes:
            quizzes_list.append({
                'quiz_id': quiz[0],
                'title': quiz[1],
                'total_marks': quiz[2],
                'time_limit': quiz[3],
                'topic': quiz[4],
                'grade_level': quiz[5]
            })
        
        return jsonify({"quizzes": quizzes_list})
    except Exception as e:
        print(f"Error in /api/quizzes: {e}")
        return jsonify({"quizzes": []}), 200

@app.route('/api/quizzes/<int:quiz_id>', methods=['GET'])
def get_quiz(quiz_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT q.quiz_id, q.title, q.total_marks, q.time_limit, t.topic_name
            FROM quizzes q
            JOIN topics t ON q.topic_id = t.topic_id
            WHERE q.quiz_id = %s
        """, (quiz_id,))
        quiz = cursor.fetchone()

        if not quiz:
            cursor.close()
            conn.close()
            return jsonify({"error": "Quiz not found"}), 404

        questions = None
        try:
            has_image_col = False
            try:
                cursor.execute("SHOW COLUMNS FROM quiz_questions LIKE 'question_image'")
                has_image_col = cursor.fetchone() is not None
            except Exception:
                pass

            if has_image_col:
                cursor.execute("""
                    SELECT question_id, question_text, question_image,
                           option_a, option_b, option_c, option_d, correct_answer
                    FROM quiz_questions
                    WHERE quiz_id = %s
                    ORDER BY question_id
                """, (quiz_id,))
            else:
                cursor.execute("""
                    SELECT question_id, question_text, option_a, option_b, option_c, option_d, correct_answer
                    FROM quiz_questions
                    WHERE quiz_id = %s
                    ORDER BY question_id
                """, (quiz_id,))
            question_rows = cursor.fetchall()
            if question_rows:
                questions = []
                for row in question_rows:
                    if has_image_col:
                        questions.append({
                            'question_id': row[0],
                            'question_text': row[1],
                            'question_image': row[2] or '',
                            'options': [row[3], row[4], row[5] or '', row[6] or ''],
                            'correct_answer': row[7]
                        })
                    else:
                        questions.append({
                            'question_id': row[0],
                            'question_text': row[1],
                            'question_image': '',
                            'options': [row[2], row[3], row[4] or '', row[5] or ''],
                            'correct_answer': row[6]
                        })
        except Exception:
            pass

        cursor.close()
        conn.close()

        if not questions:
            questions = [
                {'question_id': 1, 'question_text': 'What is 2 + 2?', 'options': ['3', '4', '5', '6']},
                {'question_id': 2, 'question_text': 'What is the square root of 16?', 'options': ['2', '3', '4', '5']},
                {'question_id': 3, 'question_text': 'Solve: x + 5 = 10. What is x?', 'options': ['3', '4', '5', '6']}
            ]

        return jsonify({
            'quiz_id': quiz[0],
            'title': quiz[1],
            'total_marks': quiz[2],
            'time_limit': quiz[3],
            'topic': quiz[4],
            'questions': questions
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/quizzes/<int:quiz_id>/submit', methods=['POST'])
def submit_quiz(quiz_id):
    try:
        data = request.get_json() or {}
        student_id = data.get('student_id')
        answers = data.get('answers')

        if not student_id or not answers:
            return jsonify({"error": "student_id and answers required"}), 400

        try:
            student_id = int(student_id)
        except (ValueError, TypeError):
            return jsonify({"error": "student_id must be a number"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Path/body student_id is users.user_id; quiz_attempt stores students.student_id
        user_id = student_id
        cursor.execute("SELECT student_id FROM students WHERE user_id = %s", (user_id,))
        student_record = cursor.fetchone()
        if not student_record:
            cursor.close()
            conn.close()
            return jsonify({"error": "Student record not found"}), 404
        student_id = student_record[0]

        # Grade answers - try quiz_questions table first
        correct_answers = {}
        try:
            cursor.execute("""
                SELECT question_id, correct_answer
                FROM quiz_questions
                WHERE quiz_id = %s
                ORDER BY question_id
            """, (quiz_id,))
            question_rows = cursor.fetchall()
            if question_rows:
                correct_answers = {row[0]: row[1] for row in question_rows}
        except Exception:
            pass

        # If no questions in quiz_questions, use default grading
        if not correct_answers:
            correct_answers = {1: 'B', 2: 'C', 3: 'C'}

        cursor.execute("SELECT total_marks FROM quizzes WHERE quiz_id = %s", (quiz_id,))
        quiz_row = cursor.fetchone()
        num_questions = max(len(correct_answers), len(answers), 1)
        total_marks = int(quiz_row[0]) if quiz_row and quiz_row[0] else num_questions
        if total_marks <= 0:
            total_marks = num_questions

        correct_count = 0
        for answer in answers:
            question_id = answer.get('question_id')
            user_answer = answer.get('answer')
            if correct_answers.get(question_id) == user_answer:
                correct_count += 1

        # Distribute quiz total_marks evenly across questions (e.g. 4 Q × 5 marks = 20 total)
        score = int(round((correct_count / num_questions) * total_marks))

        cursor.execute("""
            INSERT INTO quiz_attempt (student_id, quiz_id, score, completed_at)
            VALUES (%s, %s, %s, NOW())
        """, (student_id, quiz_id, score))

        conn.commit()

        # Check mastery for the quiz's topic after submission
        cursor.execute("SELECT topic_id FROM quizzes WHERE quiz_id = %s", (quiz_id,))
        topic_row = cursor.fetchone()
        mastery_update = None
        if topic_row:
            topic_id = topic_row[0]
            avg_score = get_student_mastery_for_topic(cursor, user_id, topic_id)
            mastered = avg_score is not None and avg_score >= 70
            cursor.execute("SELECT topic_name FROM topics WHERE topic_id = %s", (topic_id,))
            tname_row = cursor.fetchone()
            mastery_update = {
                'topic_id': topic_id,
                'topic_name': tname_row[0] if tname_row else 'Unknown',
                'avg_score': avg_score,
                'mastered': mastered,
                'threshold': 70
            }

        cursor.close()
        conn.close()

        percentage = min(100.0, round((score / total_marks) * 100, 1)) if total_marks > 0 else 0.0
        response_data = {
            "message": "Quiz submitted successfully",
            "score": score,
            "total_marks": total_marks,
            "total_possible": total_marks,
            "percentage": percentage,
        }
        if mastery_update:
            response_data["mastery_update"] = mastery_update

        return jsonify(response_data)

    except Exception as e:
        print(f"[DEBUG] Error submitting quiz: {e}")
        return jsonify({"error": str(e), "score": 0}), 200

# ==================== TEACHER ENDPOINTS ====================

@app.route('/api/quiz/<int:quiz_id>/results', methods=['GET'])
def get_quiz_results(quiz_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get quiz title and total marks
        cursor.execute("SELECT title, total_marks FROM quizzes WHERE quiz_id = %s", (quiz_id,))
        quiz_info = cursor.fetchone()
        if not quiz_info:
            cursor.close()
            conn.close()
            return jsonify({"results": [], "error": "Quiz not found"}), 200
        
        quiz_title = quiz_info[0]
        total_marks = quiz_info[1]
        
        # Get attempts - join with students table to get user_id, then users table for name
        cursor.execute("""
            SELECT 
                u.user_id,
                u.full_name, 
                qa.score, 
                qa.completed_at
            FROM quiz_attempt qa
            JOIN students s ON qa.student_id = s.student_id
            JOIN users u ON s.user_id = u.user_id
            WHERE qa.quiz_id = %s
            ORDER BY qa.score DESC
        """, (quiz_id,))
        results = cursor.fetchall() or []
        
        results_list = []
        for result in results:
            results_list.append({
                'student_id': result[0],
                'student_name': result[1],
                'score': result[2],
                'completed_at': str(result[3]) if result[3] else '',
                'total_marks': total_marks,
                'quiz_title': quiz_title
            })
        
        cursor.close()
        conn.close()
        return jsonify({"results": results_list})
    except Exception as e:
        print(f"[DEBUG] Error getting quiz results: {e}")
        return jsonify({"results": [], "error": str(e)}), 200

@app.route('/api/quiz/create', methods=['POST'])
def create_quiz():
    """
    Create a quiz with custom questions.
    """
    try:
        data = request.get_json() or {}
        title = data.get('title')
        topic_id = data.get('topic_id')
        total_marks = data.get('total_marks')
        time_limit = data.get('time_limit', 30)
        questions = data.get('questions', [])
        
        if not title or not topic_id:
            return jsonify({"error": "Title and topic_id are required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"[DEBUG] Creating quiz: {title}, topic_id: {topic_id}, questions: {len(questions)}")
        
        cursor.execute("""
            INSERT INTO quizzes (topic_id, title, total_marks, time_limit, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (topic_id, title, total_marks or len(questions), time_limit))
        quiz_id = cursor.lastrowid
        print(f"[DEBUG] Quiz created with ID: {quiz_id}")
        
        has_image_col = False
        try:
            cursor.execute("SHOW COLUMNS FROM quiz_questions LIKE 'question_image'")
            has_image_col = cursor.fetchone() is not None
        except Exception:
            pass

        questions_saved = 0
        for q in questions:
            try:
                img = (q.get('question_image') or '').strip()
                if img and not img.startswith('/uploads/quiz/'):
                    img = ''
                if has_image_col:
                    cursor.execute("""
                        INSERT INTO quiz_questions
                        (quiz_id, question_text, question_image, option_a, option_b, option_c, option_d, correct_answer)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        quiz_id,
                        q.get('question_text', ''),
                        img or None,
                        q.get('option_a', ''),
                        q.get('option_b', ''),
                        q.get('option_c') or '',
                        q.get('option_d') or '',
                        q.get('correct_answer', 'A')
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO quiz_questions
                        (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_answer)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        quiz_id,
                        q.get('question_text', ''),
                        q.get('option_a', ''),
                        q.get('option_b', ''),
                        q.get('option_c') or '',
                        q.get('option_d') or '',
                        q.get('correct_answer', 'A')
                    ))
                questions_saved += 1
            except Exception as qe:
                print(f"[DEBUG] Error saving question: {qe}")
        
        print(f"[DEBUG] Saved {questions_saved} questions")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "Quiz created successfully",
            "quiz_id": quiz_id,
            "questions_count": questions_saved
        }), 201
        
    except Exception as e:
        print(f"[DEBUG] Error creating quiz: {e}")
        return jsonify({"error": str(e), "quiz_id": None}), 200


@app.route('/api/quiz/<int:quiz_id>', methods=['PUT'])
def update_quiz(quiz_id):
    try:
        data = request.get_json() or {}
        title = data.get('title')
        topic_id = data.get('topic_id')
        total_marks = data.get('total_marks')
        time_limit = data.get('time_limit')
        questions = data.get('questions', [])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update quiz
        cursor.execute("""
            UPDATE quizzes 
            SET title = %s, topic_id = %s, total_marks = %s, time_limit = %s
            WHERE quiz_id = %s
        """, (title, topic_id, total_marks or len(questions), time_limit, quiz_id))
        
        # Delete old questions and insert new ones
        cursor.execute("DELETE FROM quiz_questions WHERE quiz_id = %s", (quiz_id,))

        has_image_col = False
        try:
            cursor.execute("SHOW COLUMNS FROM quiz_questions LIKE 'question_image'")
            has_image_col = cursor.fetchone() is not None
        except Exception:
            pass
        
        questions_saved = 0
        for q in questions:
            img = (q.get('question_image') or '').strip()
            if img and not img.startswith('/uploads/quiz/'):
                img = ''
            if has_image_col:
                cursor.execute("""
                    INSERT INTO quiz_questions
                    (quiz_id, question_text, question_image, option_a, option_b, option_c, option_d, correct_answer)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    quiz_id,
                    q.get('question_text', ''),
                    img or None,
                    q.get('option_a', ''),
                    q.get('option_b', ''),
                    q.get('option_c') or '',
                    q.get('option_d') or '',
                    q.get('correct_answer', 'A')
                ))
            else:
                cursor.execute("""
                    INSERT INTO quiz_questions
                    (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_answer)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    quiz_id,
                    q.get('question_text', ''),
                    q.get('option_a', ''),
                    q.get('option_b', ''),
                    q.get('option_c') or '',
                    q.get('option_d') or '',
                    q.get('correct_answer', 'A')
                ))
            questions_saved += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Quiz updated", "questions_count": questions_saved}), 200
        
    except Exception as e:
        print(f"[DEBUG] Error updating quiz: {e}")
        return jsonify({"error": str(e)}), 200


@app.route('/api/quiz/<int:quiz_id>', methods=['DELETE'])
def delete_quiz(quiz_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM quiz_questions WHERE quiz_id = %s", (quiz_id,))
        cursor.execute("DELETE FROM quizzes WHERE quiz_id = %s", (quiz_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Quiz deleted"}), 200
    except Exception as e:
        print(f"[DEBUG] Error deleting quiz: {e}")
        return jsonify({"error": str(e)}), 200

# ==================== FAMILY ENDPOINTS ====================
@app.route('/api/family/register', methods=['POST'])
def family_register():
    conn = None
    cursor = None
    try:
        data = request.get_json(silent=True) or {}
        print(f"[DEBUG FAMILY] Received data: {data}")
        
        full_name = (data.get('full_name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        student_id = data.get('student_id')
        student_email = (data.get('student_email') or '').strip().lower()
        relationship = (data.get('relationship') or 'parent').strip() or 'parent'
        
        print(f"[DEBUG FAMILY] full_name={full_name}, email={email}, student_id={student_id}, relationship={relationship}")
        
        if not full_name or not email or not password or (not student_id and not student_email):
            return jsonify({"error": "All fields required"}), 400
        
        # Hash the password using bcrypt
        if BCRYPT_AVAILABLE and bcrypt:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            hashed_password = password
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Email already registered"}), 400
        
        # Enforce strong password for family too
        is_strong, pw_errors, strength = validate_strong_password(password)
        if not is_strong:
            cursor.close()
            conn.close()
            return jsonify({"error": "Weak password", "errors": pw_errors}), 400
        
        # Resolve canonical students.student_id (FK target) + students.user_id (API ID)
        # Incoming "student_id" from frontend is users.user_id (selected from list).
        if student_id is not None and str(student_id).strip() != '':
            try:
                student_id = int(student_id)
            except (TypeError, ValueError):
                cursor.close()
                conn.close()
                return jsonify({"error": "student_id must be a number"}), 400
            cursor.execute("SELECT id FROM students WHERE user_id = %s", (student_id,))
            row = cursor.fetchone()
            if not row:
                cursor.close()
                conn.close()
                return jsonify({"error": "Student with this ID not found"}), 400
            student_user_id = int(student_id)
            student_pk_id = int(row[0])
        else:
            cursor.execute("SELECT user_id FROM users WHERE email = %s AND role = 'student'", (student_email,))
            student = cursor.fetchone()
            if not student:
                cursor.close()
                conn.close()
                return jsonify({"error": "Student with this email not found"}), 400
            student_user_id = int(student[0])
            cursor.execute("SELECT id FROM students WHERE user_id = %s", (student_user_id,))
            row = cursor.fetchone()
            if not row:
                cursor.close()
                conn.close()
                return jsonify({"error": "Student record not found"}), 400
            student_pk_id = int(row[0])
        
        # Generate verification for family (real email)
        verification_token = generate_verification_token()
        token_expiry = get_token_expiry()

        # ✅ FIXED: Auto-verified (is_verified = TRUE)
        cursor.execute(
            """INSERT INTO users 
               (full_name, email, password, role, is_verified, verification_token, token_expiry) 
               VALUES (%s, %s, %s, 'family', TRUE, %s, %s)""",
            (full_name, email, hashed_password, verification_token, token_expiry)
        )
        user_id = int(cursor.lastrowid)
        
        # Link to student
        cursor.execute(
            "INSERT INTO family (user_id, student_id, relationship) VALUES (%s, %s, %s)",
            (user_id, student_pk_id, relationship)
        )
        
        # ✅ FIXED: Changed s.student_id to s.id
        cursor.execute("""
            SELECT s.user_id, u.full_name, s.grade_level, s.section
            FROM family f
            JOIN students s ON f.student_id = s.id
            JOIN users u ON s.user_id = u.user_id
            WHERE f.user_id = %s
        """, (user_id,))
        linked = cursor.fetchall() or []
        students_list = [{
            'student_id': row[0],
            'full_name': row[1],
            'grade_level': row[2],
            'section': row[3],
        } for row in linked]

        conn.commit()

        return jsonify({
            "message": "Family account created successfully! You can now login.",
            "user_id": user_id,
            "full_name": full_name,
            "email": email,
            "role": "family",
            "email_sent": False,
            "students": students_list,
            "linked_students": len(students_list)
        }), 201
        
    except Exception as e:
        print(f"[ERROR FAMILY] Registration failed: {e}")
        traceback.print_exc()
        if conn:
            try:
                conn.rollback()
            except Exception:
                pass
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass

@app.route('/api/family/students/list', methods=['GET'])
def list_students_for_family():
    """Get list of all students available to link to family accounts"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.full_name, s.grade_level, s.section
            FROM users u
            JOIN students s ON u.user_id = s.user_id
            WHERE u.role = 'student'
            ORDER BY u.full_name
        """)
        students = cursor.fetchall()
        
        students_list = []
        for student in students:
            students_list.append({
                'user_id': student[0],
                'full_name': student[1],
                'grade_level': student[2],
                'section': student[3]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({"students": students_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== FAMILY ENDPOINTS ====================

@app.route('/api/family/login', methods=['POST'])
def family_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        # ✅ FIXED: Added role check for family
        cursor.execute(
            "SELECT user_id, full_name, email, role, password, is_verified FROM users WHERE email = %s AND role = 'family'",
            (email,)
        )
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid credentials"}), 401
        
        stored_password = user[4]
        is_verified = bool(user[5]) if len(user) > 5 else True
        
        # Check bcrypt hash first, then fall back to plain text for migration
        password_valid = False
        if stored_password:
            if BCRYPT_AVAILABLE and stored_password.startswith('$2'):
                try:
                    password_valid = bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
                except Exception:
                    password_valid = False
            else:
                password_valid = (password == stored_password)
                if password_valid and BCRYPT_AVAILABLE and bcrypt:
                    new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    cursor.execute("UPDATE users SET password = %s WHERE user_id = %s", (new_hash, user[0]))
                    conn.commit()
        
        if not password_valid:
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid credentials"}), 401
        
        # ✅ FIXED: Skip verification check for family
        # if not is_verified:
        #     cursor.close()
        #     conn.close()
        #     return jsonify({
        #         "error": "Please verify your email before logging in.",
        #         "requires_verification": True,
        #         "email": user[2]
        #     }), 403
        
        # Get linked students
        cursor.execute("""
            SELECT s.user_id, u.full_name, s.grade_level, s.section
            FROM family f
            JOIN students s ON f.student_id = s.id
            JOIN users u ON s.user_id = u.user_id
            WHERE f.user_id = %s
        """, (user[0],))
        students = cursor.fetchall()
        
        students_list = []
        for student in students:
            students_list.append({
                'student_id': student[0],
                'full_name': student[1],
                'grade_level': student[2],
                'section': student[3]
            })
        
        cursor.close()
        conn.close()
        
        access_token = create_access_token(identity={
            'user_id': user[0],
            'role': user[3]
        })
        
        return jsonify({
            "user_id": user[0],
            "full_name": user[1],
            "email": user[2],
            "role": user[3],
            "token": access_token,
            "students": students_list
        }), 200
        
    except Exception as e:
        print(f"[ERROR FAMILY LOGIN] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/family/students', methods=['GET'])
def get_family_students():
    try:
        # Get user_id from JWT token
        from flask_jwt_extended import jwt_required, get_jwt_identity
        
        # For simplicity, we'll get user_id from query param
        # In production, you'd use JWT
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.user_id, u.full_name, s.grade_level, s.section
            FROM family f
            JOIN students s ON f.student_id = s.id
            JOIN users u ON s.user_id = u.user_id
            WHERE f.user_id = %s
        """, (user_id,))
        students = cursor.fetchall()
        
        students_list = []
        for student in students:
            students_list.append({
                'student_id': student[0],
                'full_name': student[1],
                'grade_level': student[2],
                'section': student[3]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({"students": students_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/family/student/<int:student_id>/progress', methods=['GET'])
def get_family_student_progress(student_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        from gap_utils import QUIZ_STUDENT_JOIN
        cursor.execute(f"""
            SELECT qa.attempt_id, qa.quiz_id, qa.score, qa.completed_at,
                   q.title, t.topic_name, q.total_marks
            FROM quiz_attempt qa
            JOIN quizzes q ON qa.quiz_id = q.quiz_id
            JOIN topics t ON q.topic_id = t.topic_id
            {QUIZ_STUDENT_JOIN}
            WHERE s_qa.user_id = %s
            ORDER BY qa.completed_at ASC
        """, (student_id,))
        attempts = cursor.fetchall()
        
        attempts_list = []
        for attempt in attempts:
            attempts_list.append({
                'attempt_id': attempt[0],
                'quiz_id': attempt[1],
                'score': attempt[2],
                'completed_at': str(attempt[3]),
                'quiz_title': attempt[4],
                'topic': attempt[5],
                'total_marks': attempt[6]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({"attempts": attempts_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/family/student/<int:student_id>/gaps', methods=['GET'])
def get_family_student_gaps(student_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        from gap_utils import fetch_student_gaps
        gaps_list = fetch_student_gaps(cursor, student_id)
        cursor.close()
        conn.close()
        return jsonify({"gaps": gaps_list})
    except Exception as e:
        print(f"Error in family gaps: {e}")
        return jsonify({"gaps": []}), 200

@app.route('/api/family/student/<int:student_id>/recommendations', methods=['GET'])
def get_family_student_recommendations(student_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        from gap_utils import QUIZ_STUDENT_JOIN, fetch_student_gaps
        gap_topics = fetch_student_gaps(cursor, student_id)[:5]
        
        recommendations = []
        for topic in gap_topics:
            topic_id = topic['topic_id']
            avg_score = topic['avg_score']
            cursor.execute(f"""
                SELECT q.quiz_id, q.title, q.total_marks                FROM quizzes q
                WHERE q.topic_id = %s
                AND q.quiz_id NOT IN (
                    SELECT qa.quiz_id
                    FROM quiz_attempt qa
                    {QUIZ_STUDENT_JOIN}
                    WHERE s_qa.user_id = %s
                )
                LIMIT 3
            """, (topic_id, student_id))
            quizzes = cursor.fetchall()
            
            for quiz in quizzes:
                recommendations.append({
                    'quiz_id': quiz[0],
                    'title': quiz[1],
                    'total_marks': quiz[2],
                    'topic_name': topic['topic_name'],
                    'avg_score': avg_score
                })
        
        cursor.close()
        conn.close()
        
        return jsonify({"recommendations": recommendations})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/family/student/<int:student_id>/report', methods=['GET'])
def get_family_student_report(student_id):
    """Download a printable HTML student progress report."""
    try:
        import family_report as freport
        conn = get_db_connection()
        cursor = conn.cursor()

        report_data = freport.fetch_report_data(cursor, student_id)
        cursor.close()
        conn.close()

        if not report_data:
            return jsonify({"error": "Student not found"}), 404

        html_content = freport.build_report_html(report_data)
        safe_name = (report_data['student'].get('name') or 'Student').replace(' ', '_')
        filename = f"{safe_name}_Progress_Report.html"

        return Response(
            html_content,
            mimetype='text/html',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'text/html; charset=utf-8',
            },
        )
    except Exception as e:
        print(f"Error generating family report: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ==================== MATERIAL APPROVAL ENDPOINTS ====================

@app.route('/api/materials/pending', methods=['GET'])
def get_pending_materials():
    try:
        import material_delivery as delivery
        conn = get_db_connection()
        cursor = conn.cursor()

        extra_cols = delivery.existing_material_columns(cursor)
        select_cols = delivery.build_material_select('m', 't')
        select_cols += [f'm.{c}' for c in extra_cols]
        select_sql = ', '.join(select_cols)

        cursor.execute(f"""
            SELECT {select_sql}
            FROM material m
            LEFT JOIN topics t ON m.topic_id = t.topic_id
            WHERE m.approval_status = 'Pending'
            ORDER BY m.generated_date DESC
        """)
        materials = cursor.fetchall() or []

        delivery.repair_unassigned_pending_materials(cursor)
        conn.commit()

        materials_list = []
        for material in materials:
            delivery.ensure_material_assigned(cursor, material[0])
            assigned = delivery.get_assigned_students(cursor, material[0])
            materials_list.append(
                delivery.material_row_to_dict(material, extra_cols, assigned_students=assigned)
            )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"materials": materials_list})
    except Exception as e:
        print(f"Error in /api/materials/pending: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "materials": []}), 500

@app.route('/api/materials/<int:material_id>/assign', methods=['POST'])
def assign_material_to_student(material_id):
    """Assign a pending material to a student (users.user_id) before approval."""
    try:
        import material_delivery as delivery
        data = request.get_json() or {}
        student_id = data.get('student_id')
        if not student_id:
            return jsonify({"error": "student_id is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT material_id FROM material WHERE material_id = %s", (material_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Material not found"}), 404

        cursor.execute(
            """
            SELECT t.grade_level FROM material m
            LEFT JOIN topics t ON m.topic_id = t.topic_id
            WHERE m.material_id = %s
            """,
            (material_id,),
        )
        grade_row = cursor.fetchone()
        mat_grade = int(grade_row[0]) if grade_row and grade_row[0] else None
        count = delivery.ensure_material_assigned(
            cursor, material_id, student_id=student_id, grade_level=mat_grade
        )
        if not count:
            cursor.close()
            conn.close()
            return jsonify({
                "error": "Could not assign material — student not found in class roster",
            }), 400

        assigned = delivery.get_assigned_students(cursor, material_id)
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({
            "message": "Material assigned to student",
            "assigned_students": assigned,
        }), 200
    except Exception as e:
        print(f"Error in /api/materials/{material_id}/assign: {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# ✅ FIXED: approve_material - Direct SQL query for assigned students
# ============================================================
@app.route('/api/materials/approve/<int:material_id>', methods=['POST'])
def approve_material(material_id):
    try:
        import material_delivery as delivery
        data = request.get_json() or {}
        student_id = data.get('student_id')
        
        # 🔍 DEBUG LOGS
        print(f"[DEBUG] ========================================")
        print(f"[DEBUG] Approve material {material_id} with student_id: {student_id}")
        print(f"[DEBUG] Request data: {data}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if material exists
        cursor.execute("SELECT material_id, approval_status FROM material WHERE material_id = %s", (material_id,))
        material = cursor.fetchone()
        if not material:
            cursor.close()
            conn.close()
            return jsonify({"error": "Material not found"}), 404
        
        print(f"[DEBUG] Material found: ID={material[0]}, Status={material[1]}")
        
        # Check if already approved
        if material[1] == 'Approved':
            cursor.close()
            conn.close()
            return jsonify({"error": "Material already approved"}), 400
        
        delivery.ensure_generation_history_material_id(cursor)

        # Get grade level
        cursor.execute(
            """
            SELECT t.grade_level FROM material m
            LEFT JOIN topics t ON m.topic_id = t.topic_id
            WHERE m.material_id = %s
            """,
            (material_id,),
        )
        grade_row = cursor.fetchone()
        mat_grade = int(grade_row[0]) if grade_row and grade_row[0] else None
        print(f"[DEBUG] Material grade: {mat_grade}")
        
        # ✅ DIRECT ASSIGNMENT: Link material to student
        if student_id:
            print(f"[DEBUG] Attempting to assign to student_id: {student_id}")
            # student_id from frontend is users.user_id, need to get students.id (PK)
            cursor.execute("SELECT id FROM students WHERE user_id = %s", (student_id,))
            student_row = cursor.fetchone()
            if student_row:
                actual_student_id = student_row[0]
                print(f"[DEBUG] Found student: user_id={student_id}, student_pk={actual_student_id}")
                
                # Check if already assigned
                cursor.execute(
                    "SELECT 1 FROM student_materials WHERE student_id = %s AND material_id = %s",
                    (actual_student_id, material_id)
                )
                if not cursor.fetchone():
                    # Assign the material to the student
                    cursor.execute(
                        "INSERT INTO student_materials (student_id, material_id, status, assigned_date) VALUES (%s, %s, 'Pending', NOW())",
                        (actual_student_id, material_id)
                    )
                    conn.commit()
                    print(f"[DEBUG] ✅ Assigned material {material_id} to student {actual_student_id}")
                else:
                    print(f"[DEBUG] Material already assigned to student {actual_student_id}")
            else:
                print(f"[DEBUG] ❌ Student with user_id {student_id} not found in students table!")
        else:
            print(f"[DEBUG] ❌ No student_id provided in request")
            cursor.close()
            conn.close()
            return jsonify({
                "error": "No student selected. Please select a student before approving."
            }), 400
        
        # ✅ FIXED: Use direct SQL query instead of delivery.get_assigned_students()
        cursor.execute("""
            SELECT u.user_id, u.full_name
            FROM student_materials sm
            JOIN students s ON sm.student_id = s.id
            JOIN users u ON s.user_id = u.user_id
            WHERE sm.material_id = %s
        """, (material_id,))
        assigned_rows = cursor.fetchall()
        assigned = [{'user_id': row[0], 'full_name': row[1]} for row in assigned_rows]
        print(f"[DEBUG] Assigned students after: {assigned}")

        if not assigned:
            print(f"[DEBUG] ❌ No assigned students found!")
            cursor.close()
            conn.close()
            return jsonify({
                "error": "Failed to assign material to student. Please try again.",
                "debug": {
                    "student_id_provided": student_id,
                    "material_id": material_id
                }
            }), 400

        # Update material status to Approved
        cursor.execute(
            "UPDATE material SET approval_status = 'Approved' WHERE material_id = %s",
            (material_id,)
        )
        conn.commit()
        
        # Get final assigned students using direct SQL
        cursor.execute("""
            SELECT u.user_id, u.full_name
            FROM student_materials sm
            JOIN students s ON sm.student_id = s.id
            JOIN users u ON s.user_id = u.user_id
            WHERE sm.material_id = %s
        """, (material_id,))
        final_rows = cursor.fetchall()
        assigned = [{'user_id': row[0], 'full_name': row[1]} for row in final_rows]
        print(f"[DEBUG] ✅ Final assigned students: {assigned}")
        print(f"[DEBUG] ========================================")
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "Material approved successfully",
            "assigned_students": assigned,
        }), 200
    except Exception as e:
        print(f"[ERROR] Error in /api/materials/approve/{material_id}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/materials/reject/<int:material_id>', methods=['POST'])
def reject_material(material_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if material exists
        cursor.execute("SELECT material_id FROM material WHERE material_id = %s", (material_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Material not found"}), 404
        
        # Update status to Rejected
        cursor.execute(
            "UPDATE material SET approval_status = 'Rejected' WHERE material_id = %s",
            (material_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Material rejected successfully"}), 200
    except Exception as e:
        print(f"Error in /api/materials/reject/{material_id}: {e}")
        return jsonify({"error": str(e)}), 200

@app.route('/api/materials/approved', methods=['GET'])
def get_approved_materials():
    try:
        student_id = request.args.get('student_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        import material_delivery as delivery

        extra_cols = delivery.existing_material_columns(cursor)
        select_cols = delivery.build_material_select('m', 't', include_topic_id=True)
        select_cols += [f'm.{c}' for c in extra_cols]
        select_sql = ', '.join(select_cols)

        delivery.ensure_student_materials_table(cursor)

        if student_id:
            user_id = delivery.resolve_student_user_id(cursor, student_id)
            sm_join = delivery.student_materials_filter_by_user_sql('%s')
            cursor.execute(f"""
                SELECT {select_sql}
                FROM material m
                JOIN topics t ON m.topic_id = t.topic_id
                {sm_join}
                WHERE m.approval_status = 'Approved'
                ORDER BY m.generated_date DESC
            """, (user_id or student_id,))
        else:
            cursor.execute(f"""
                SELECT {select_sql}
                FROM material m
                JOIN topics t ON m.topic_id = t.topic_id
                WHERE m.approval_status = 'Approved'
                ORDER BY m.generated_date DESC
            """)
        
        materials = cursor.fetchall() or []
        materials_list = [
            delivery.material_row_to_dict(m, extra_cols, has_topic_id=True)
            for m in materials
        ]
        
        cursor.close()
        conn.close()
        
        return jsonify({"materials": materials_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== ADMIN ENDPOINTS ====================

@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({"error": "Email and password required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        # ✅ FIXED: Added role check for admin
        cursor.execute(
            "SELECT user_id, full_name, email, role, password, is_verified FROM users WHERE email = %s AND role = 'admin'",
            (email,)
        )
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid credentials"}), 401
        
        stored_password = user[4]
        is_verified = bool(user[5]) if len(user) > 5 else True
        
        # Check bcrypt hash first, then fall back to plain text for migration
        password_valid = False
        if stored_password:
            if stored_password.startswith('$2'):
                try:
                    password_valid = bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
                except Exception:
                    password_valid = False
            else:
                password_valid = (password == stored_password)
                if password_valid:
                    new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    cursor.execute("UPDATE users SET password = %s WHERE user_id = %s", (new_hash, user[0]))
                    conn.commit()
        
        if not password_valid:
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid credentials"}), 401
        
        # ✅ FIXED: Skip verification check for admin
        # if not is_verified:
        #     cursor.close()
        #     conn.close()
        #     return jsonify({"error": "Admin email not verified.", "requires_verification": True}), 403
        
        cursor.close()
        conn.close()
        
        access_token = create_access_token(identity={
            'user_id': user[0],
            'role': user[3]
        })
        
        return jsonify({
            "user_id": user[0],
            "full_name": user[1],
            "email": user[2],
            "role": user[3],
            "token": access_token
        }), 200
        
    except Exception as e:
        print(f"[ERROR ADMIN LOGIN] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, full_name, email, role, created_at
            FROM users
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall() or []
        cursor.close()
        conn.close()

        users_list = []
        for user in users:
            users_list.append({
                'user_id': user[0],
                'full_name': user[1],
                'email': user[2],
                'role': user[3],
                'created_at': str(user[4]) if user[4] else None
            })

        return jsonify({"users": users_list})
    except Exception as e:
        print(f"Error in /api/admin/users: {e}")
        return jsonify({"users": [], "error": str(e)}), 200

@app.route('/api/admin/users/<role>', methods=['GET'])
def admin_get_users_by_role(role):
    try:
        if role not in ['student', 'teacher', 'family', 'admin']:
            return jsonify({"users": [], "error": "Invalid role"}), 200
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if role == 'student':
            cursor.execute("""
                SELECT u.user_id, u.full_name, u.email, u.role, u.created_at,
                       s.grade_level, s.section
                FROM users u
                LEFT JOIN students s ON u.user_id = s.user_id
                WHERE u.role = 'student'
                ORDER BY u.created_at DESC
            """)
            users = cursor.fetchall() or []
            users_list = []
            for user in users:
                users_list.append({
                    'user_id': user[0],
                    'full_name': user[1],
                    'email': user[2],
                    'role': user[3],
                    'created_at': str(user[4]) if user[4] else None,
                    'grade_level': user[5],
                    'section': user[6]
                })
        elif role == 'teacher':
            cursor.execute("""
                SELECT u.user_id, u.full_name, u.email, u.role, u.created_at,
                       t.qualification, t.subject, t.grade_level
                FROM users u
                LEFT JOIN teachers t ON u.user_id = t.user_id
                WHERE u.role = 'teacher'
                ORDER BY u.created_at DESC
            """)
            users = cursor.fetchall() or []
            users_list = []
            for user in users:
                users_list.append({
                    'user_id': user[0],
                    'full_name': user[1],
                    'email': user[2],
                    'role': user[3],
                    'created_at': str(user[4]) if user[4] else None,
                    'qualification': user[5],
                    'subject': user[6],
                    'grade_level': user[7],
                    'assigned_grade': user[7],
                })
        elif role == 'family':
            cursor.execute("""
                SELECT u.user_id, u.full_name, u.email, u.role, u.created_at,
                       f.relationship
                FROM users u
                LEFT JOIN family f ON u.user_id = f.user_id
                WHERE u.role = 'family'
                ORDER BY u.created_at DESC
            """)
            users = cursor.fetchall() or []
            users_list = []
            for user in users:
                users_list.append({
                    'user_id': user[0],
                    'full_name': user[1],
                    'email': user[2],
                    'role': user[3],
                    'created_at': str(user[4]) if user[4] else None,
                    'relationship': user[5]
                })
        else:  # admin
            cursor.execute("""
                SELECT u.user_id, u.full_name, u.email, u.role, u.created_at
                FROM users u
                WHERE u.role = 'admin'
                ORDER BY u.created_at DESC
            """)
            users = cursor.fetchall() or []
            users_list = []
            for user in users:
                users_list.append({
                    'user_id': user[0],
                    'full_name': user[1],
                    'email': user[2],
                    'role': user[3],
                    'created_at': str(user[4]) if user[4] else None
                })
        
        cursor.close()
        conn.close()
        
        return jsonify({"users": users_list})
    except Exception as e:
        print(f"Error in /api/admin/users/{role}: {e}")
        return jsonify({"users": [], "error": str(e)}), 200

@app.route('/api/admin/user', methods=['POST'])
def admin_create_user():
    try:
        data = request.get_json()
        full_name = data.get('full_name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        grade_level = data.get('grade_level')
        section = data.get('section')
        qualification = data.get('qualification')
        subject = data.get('subject')
        relationship = data.get('relationship', 'parent')
        student_ids = data.get('student_ids', [])
        
        if not full_name or not email or not password or not role:
            return jsonify({"error": "Full name, email, password, and role are required"}), 400
        
        if role not in ['student', 'teacher', 'family', 'admin']:
            return jsonify({"error": "Invalid role"}), 400
        
        # Hash the password using bcrypt when available
        if BCRYPT_AVAILABLE and bcrypt:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        else:
            hashed_password = password
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Email already registered"}), 400
        
        # Admin-created accounts must still use strong passwords
        is_strong, pw_errors, _ = validate_strong_password(password)
        if not is_strong:
            cursor.close()
            conn.close()
            return jsonify({"error": "Weak password", "errors": pw_errors}), 400
        
        # Insert user (admin created = auto verified)
        cursor.execute(
            "INSERT INTO users (full_name, email, password, role, is_verified, created_at) VALUES (%s, %s, %s, %s, TRUE, NOW())",
            (full_name, email, hashed_password, role)
        )
        user_id = cursor.lastrowid
        
        # Insert role-specific data
        if role == 'student':
            if not grade_level or not section:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({"error": "Grade level and section are required for students"}), 400
            try:
                grade_level = int(grade_level)
            except (ValueError, TypeError):
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({"error": "Grade level must be a number"}), 400
            section = str(section).strip()
            cursor.execute(
                "INSERT INTO students (user_id, grade_level, section, enrollment_date) VALUES (%s, %s, %s, CURDATE())",
                (user_id, grade_level, section)
            )
        elif role == 'teacher':
            # ============================================================
            # ✅ FIXED: Use grade_level directly from frontend
            # ============================================================
            if not qualification or not subject:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({"error": "Qualification and subject are required for teachers"}), 400
            
            # Use grade_level directly (sent from frontend)
            teacher_grade = grade_level
            
            if teacher_grade is None or str(teacher_grade).strip() == '':
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({"error": "Assigned grade (9, 10, 11, or 12) is required for teachers"}), 400
            
            try:
                teacher_grade = int(teacher_grade)
            except (ValueError, TypeError):
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({"error": "Grade must be a number (9, 10, 11, or 12)"}), 400
            
            # Validate it's between 9 and 12
            if teacher_grade not in [9, 10, 11, 12]:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({"error": "Assigned grade must be 9, 10, 11, or 12"}), 400
            
            cursor.execute(
                "INSERT INTO teachers (user_id, qualification, subject, grade_level) VALUES (%s, %s, %s, %s)",
                (user_id, qualification, subject, teacher_grade)
            )
        elif role == 'family':
            if not student_ids:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({"error": "At least one student ID is required for family accounts"}), 400
            
            for student_id in student_ids:
                # incoming student_id is users.user_id; family.student_id stores students.student_id
                cursor.execute("SELECT student_id FROM students WHERE user_id = %s", (student_id,))
                row = cursor.fetchone()
                if not row:
                    conn.rollback()
                    cursor.close()
                    conn.close()
                    return jsonify({"error": f"Student with ID {student_id} not found"}), 400
                student_pk_id = int(row[0])
                
                cursor.execute(
                    "INSERT INTO family (user_id, student_id, relationship) VALUES (%s, %s, %s)",
                    (user_id, student_pk_id, relationship)
                )
        elif role == 'admin':
            cursor.execute(
                "INSERT INTO administrator (user_id) VALUES (%s)",
                (user_id,)
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "User created successfully",
            "user_id": user_id
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/user/<int:user_id>', methods=['PUT'])
def admin_update_user(user_id):
    try:
        data = request.get_json()
        full_name = data.get('full_name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        grade_level = data.get('grade_level')
        section = data.get('section')
        qualification = data.get('qualification')
        subject = data.get('subject')
        
        if not full_name or not email or not role:
            return jsonify({"error": "Full name, email, and role are required"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT user_id, role FROM users WHERE user_id = %s", (user_id,))
        existing_user = cursor.fetchone()
        if not existing_user:
            cursor.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        # Check if email is already used by another user
        cursor.execute("SELECT user_id FROM users WHERE email = %s AND user_id != %s", (email, user_id))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Email already registered by another user"}), 400
        
        # Update user
        if password:
            if BCRYPT_AVAILABLE and bcrypt:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            else:
                hashed_password = password
            cursor.execute(
                "UPDATE users SET full_name = %s, email = %s, password = %s, role = %s WHERE user_id = %s",
                (full_name, email, hashed_password, role, user_id)
            )
        else:
            cursor.execute(
                "UPDATE users SET full_name = %s, email = %s, role = %s WHERE user_id = %s",
                (full_name, email, role, user_id)
            )
        
        # Update role-specific data
        old_role = existing_user[1]
        
        if old_role == 'student' and role != 'student':
            cursor.execute("DELETE FROM students WHERE user_id = %s", (user_id,))
        elif old_role == 'teacher' and role != 'teacher':
            cursor.execute("DELETE FROM teachers WHERE user_id = %s", (user_id,))
        elif old_role == 'family' and role != 'family':
            cursor.execute("DELETE FROM family WHERE user_id = %s", (user_id,))
        elif old_role == 'admin' and role != 'admin':
            cursor.execute("DELETE FROM administrator WHERE user_id = %s", (user_id,))
        
        if role == 'student':
            if grade_level and section:
                try:
                    grade_level = int(grade_level)
                except (ValueError, TypeError):
                    conn.rollback()
                    cursor.close()
                    conn.close()
                    return jsonify({"error": "Grade level must be a number"}), 400
                section = str(section).strip()
                cursor.execute("SELECT user_id FROM students WHERE user_id = %s", (user_id,))
                if cursor.fetchone():
                    cursor.execute(
                        "UPDATE students SET grade_level = %s, section = %s WHERE user_id = %s",
                        (grade_level, section, user_id)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO students (user_id, grade_level, section, enrollment_date) VALUES (%s, %s, %s, CURDATE())",
                        (user_id, grade_level, section)
                    )
        elif role == 'teacher':
            teacher_grade = parse_teacher_grade(
                data.get('teacher_grade_level') or data.get('assigned_grade') or grade_level
            )
            if qualification and subject:
                cursor.execute("SELECT user_id FROM teachers WHERE user_id = %s", (user_id,))
                if cursor.fetchone():
                    if teacher_grade is not None:
                        cursor.execute(
                            "UPDATE teachers SET qualification = %s, subject = %s, grade_level = %s WHERE user_id = %s",
                            (qualification, subject, teacher_grade, user_id)
                        )
                    else:
                        cursor.execute(
                            "UPDATE teachers SET qualification = %s, subject = %s WHERE user_id = %s",
                            (qualification, subject, user_id)
                        )
                else:
                    if teacher_grade is None:
                        conn.rollback()
                        cursor.close()
                        conn.close()
                        return jsonify({"error": "Assigned grade (9, 10, 11, or 12) is required for teachers"}), 400
                    cursor.execute(
                        "INSERT INTO teachers (user_id, qualification, subject, grade_level) VALUES (%s, %s, %s, %s)",
                        (user_id, qualification, subject, teacher_grade)
                    )
        elif role == 'admin':
            cursor.execute("SELECT user_id FROM administrator WHERE user_id = %s", (user_id,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO administrator (user_id) VALUES (%s)",
                    (user_id,)
                )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "User updated successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/user/<int:user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        # Delete user (cascade will handle related records)
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "User deleted successfully"}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/stats', methods=['GET'])
def admin_get_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total users by role
        users_by_role = {}
        try:
            cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
            role_counts = cursor.fetchall() or []
            users_by_role = {str(role): count for role, count in role_counts}
        except Exception:
            pass
        
        # Get total quizzes
        total_quizzes = 0
        try:
            cursor.execute("SELECT COUNT(*) FROM quizzes")
            result = cursor.fetchone()
            total_quizzes = result[0] if result else 0
        except Exception:
            pass
        
        # Get total quiz attempts
        total_attempts = 0
        try:
            cursor.execute("SELECT COUNT(*) FROM quiz_attempt")
            result = cursor.fetchone()
            total_attempts = result[0] if result else 0
        except Exception:
            pass
        
        # Get average score
        avg_score = 0
        try:
            cursor.execute("SELECT AVG(score) FROM quiz_attempt")
            result = cursor.fetchone()
            avg_score = round(result[0], 2) if result and result[0] else 0
        except Exception:
            pass
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "users_by_role": users_by_role,
            "total_quizzes": total_quizzes,
            "total_attempts": total_attempts,
            "average_score": avg_score
        })
    except Exception as e:
        print(f"Error in /api/admin/stats: {e}")
        return jsonify({
            "users_by_role": {},
            "total_quizzes": 0,
            "total_attempts": 0,
            "average_score": 0,
            "error": str(e)
        }, 200)

# ==================== MASTERY-BASED PROGRESSION ENDPOINTS ====================

def parse_prerequisites(prereq_str):
    """Parse prerequisites string into list of topic IDs.
    Supports JSON format '[1,2]' or comma-separated '1,2'."""
    if not prereq_str:
        return []
    prereq_str = prereq_str.strip()
    try:
        parsed = json.loads(prereq_str)
        if isinstance(parsed, list):
            return [int(x) for x in parsed]
    except (json.JSONDecodeError, ValueError):
        pass
    return [int(x.strip()) for x in prereq_str.split(',') if x.strip().isdigit()]

def get_student_mastery_for_topic(cursor, student_id, topic_id):
    """Calculate average score % for a student on a topic. student_id is users.user_id."""
    from gap_utils import QUIZ_STUDENT_JOIN
    cursor.execute(f"""
        SELECT AVG(qa.score * 100.0 / NULLIF(q.total_marks, 0)) as avg_pct
        FROM quiz_attempt qa
        JOIN quizzes q ON qa.quiz_id = q.quiz_id
        {QUIZ_STUDENT_JOIN}
        WHERE s_qa.user_id = %s AND q.topic_id = %s
    """, (student_id, topic_id))
    row = cursor.fetchone()
    if row and row[0] is not None:
        return round(float(row[0]), 2)
    return None

def get_topic_mastery_map(cursor, student_id):
    """Get mastery status for all topics for a student.
    Returns dict {topic_id: {'avg_score': float|None, 'status': str}}"""
    cursor.execute("SELECT topic_id, prerequisites, topic_name, grade_level FROM topics")
    topics = cursor.fetchall()
    mastery_map = {}
    for topic in topics:
        topic_id = topic[0]
        avg_score = get_student_mastery_for_topic(cursor, student_id, topic_id)
        if avg_score is None:
            status = 'not_started'
        elif avg_score >= 70:
            status = 'mastered'
        else:
            status = 'in_progress'
        mastery_map[topic_id] = {
            'avg_score': avg_score,
            'status': status,
            'topic_name': topic[2],
            'grade_level': topic[3],
            'prerequisites': topic[1] or ''
        }
    return mastery_map

def check_prerequisites_met(cursor, student_id, topic_id):
    """Check if all prerequisites for a topic are mastered (>=70%)."""
    cursor.execute("SELECT prerequisites FROM topics WHERE topic_id = %s", (topic_id,))
    row = cursor.fetchone()
    if not row or not row[0]:
        return True
    prereq_ids = parse_prerequisites(row[0])
    if not prereq_ids:
        return True
    for prereq_id in prereq_ids:
        avg_score = get_student_mastery_for_topic(cursor, student_id, prereq_id)
        if avg_score is None or avg_score < 70:
            return False
    return True

@app.route('/api/student/<int:student_id>/available-topics', methods=['GET'])
def get_available_topics(student_id):
    """Returns topics the student can access based on mastered prerequisites."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT topic_id, topic_name, grade_level, prerequisites FROM topics")
        topics = cursor.fetchall()
        
        mastery_map = get_topic_mastery_map(cursor, student_id)
        
        available = []
        for topic in topics:
            topic_id = topic[0]
            prereqs_met = check_prerequisites_met(cursor, student_id, topic_id)
            mastery = mastery_map.get(topic_id, {})
            
            available.append({
                'topic_id': topic_id,
                'topic_name': topic[1],
                'grade_level': topic[2],
                'prerequisites': topic[3] or '',
                'prerequisites_met': prereqs_met,
                'status': mastery.get('status', 'not_started'),
                'avg_score': mastery.get('avg_score')
            })
        
        cursor.close()
        conn.close()
        return jsonify({"topics": available})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/student/<int:student_id>/mastery-status', methods=['GET'])
def get_mastery_status(student_id):
    """Returns mastery status for all topics for a given student."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        mastery_map = get_topic_mastery_map(cursor, student_id)
        
        statuses = []
        for topic_id, data in mastery_map.items():
            prereq_ids = parse_prerequisites(data['prerequisites'])
            prereq_names = []
            for pid in prereq_ids:
                cursor.execute("SELECT topic_name FROM topics WHERE topic_id = %s", (pid,))
                prow = cursor.fetchone()
                prereq_names.append(prow[0] if prow else f"Topic {pid}")
            
            statuses.append({
                'topic_id': topic_id,
                'topic_name': data['topic_name'],
                'grade_level': data['grade_level'],
                'avg_score': data['avg_score'],
                'status': data['status'],
                'prerequisites': prereq_ids,
                'prerequisite_names': prereq_names
            })
        
        cursor.close()
        conn.close()
        return jsonify({"mastery_status": statuses})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/student/<int:student_id>/check-mastery/<int:topic_id>', methods=['POST'])
def check_mastery(student_id, topic_id):
    """Check if a student has mastered a topic (score >= 70%)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        avg_score = get_student_mastery_for_topic(cursor, student_id, topic_id)
        
        cursor.execute("SELECT topic_name FROM topics WHERE topic_id = %s", (topic_id,))
        row = cursor.fetchone()
        topic_name = row[0] if row else "Unknown"
        
        mastered = avg_score is not None and avg_score >= 70
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "topic_id": topic_id,
            "topic_name": topic_name,
            "avg_score": avg_score,
            "mastered": mastered,
            "threshold": 70
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/student/<int:student_id>/progress-map', methods=['GET'])
def get_progress_map(student_id):
    """Visual map of mastered vs locked topics grouped by grade level."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT grade_level FROM topics ORDER BY grade_level")
        grades = [row[0] for row in cursor.fetchall()] or []
        
        mastery_map = get_topic_mastery_map(cursor, student_id)
        
        progress = {}
        for grade in grades:
            try:
                cursor.execute(
                    "SELECT topic_id, topic_name, prerequisites FROM topics WHERE grade_level = %s ORDER BY topic_id",
                    (grade,)
                )
                grade_topics = cursor.fetchall() or []
            except Exception:
                grade_topics = []
            
            grade_list = []
            for gt in grade_topics:
                tid = gt[0]
                mastery = mastery_map.get(tid, {})
                prereqs_met = check_prerequisites_met(cursor, student_id, tid)
                
                if mastery.get('status') == 'mastered':
                    color = 'green'
                elif mastery.get('status') == 'in_progress':
                    color = 'yellow'
                elif prereqs_met:
                    color = 'blue'
                else:
                    color = 'gray'
                
                prereq_ids = parse_prerequisites(gt[2]) if gt[2] else []
                prereq_names = []
                for pid in prereq_ids:
                    try:
                        cursor.execute("SELECT topic_name FROM topics WHERE topic_id = %s", (pid,))
                        prow = cursor.fetchone()
                        prereq_names.append(prow[0] if prow else f"Topic {pid}")
                    except Exception:
                        prereq_names.append(f"Topic {pid}")
                
                grade_list.append({
                    'topic_id': tid,
                    'topic_name': gt[1],
                    'status': mastery.get('status', 'not_started'),
                    'avg_score': mastery.get('avg_score'),
                    'color': color,
                    'prerequisites_met': prereqs_met,
                    'prerequisite_names': prereq_names
                })
            progress[grade] = grade_list
        
        cursor.close()
        conn.close()
        return jsonify({"progress_map": progress, "grades": grades})
    except Exception as e:
        print(f"Error in /api/student/{student_id}/progress-map: {e}")
        return jsonify({"progress_map": {}, "grades": []}), 200

@app.route('/api/teacher/mastery-overview', methods=['GET'])
def get_teacher_mastery_overview():
    """Class-wide mastery summary showing % of students who mastered each topic."""
    try:
        grade_filter = parse_teacher_grade(request.args.get('grade_level'))
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get topics (optionally scoped to teacher grade)
        if grade_filter is not None:
            cursor.execute(
                "SELECT topic_id, topic_name, grade_level FROM topics WHERE grade_level = %s ORDER BY topic_id",
                (grade_filter,),
            )
        else:
            cursor.execute("SELECT topic_id, topic_name, grade_level FROM topics ORDER BY grade_level, topic_id")
        topics = cursor.fetchall() or []
        
        # Total students in scope
        if grade_filter is not None:
            cursor.execute(
                """
                SELECT COUNT(*) FROM users u
                JOIN students s ON u.user_id = s.user_id
                WHERE u.role = 'student' AND s.grade_level = %s
                """,
                (grade_filter,),
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
        result = cursor.fetchone()
        total_students = result[0] if result else 0
        
        from gap_utils import (
            count_students_mastered_topic,
            fetch_struggling_students_for_topic,
            QUIZ_STUDENT_JOIN,
        )

        overview = []
        for topic in topics:
            topic_id = topic[0]
            
            mastered_count = count_students_mastered_topic(cursor, topic_id, grade_filter)
            attempted_count = 0
            try:
                grade_clause = ""
                params = [topic_id]
                if grade_filter is not None:
                    grade_clause = " AND s_qa.user_id IN (SELECT user_id FROM students WHERE grade_level = %s)"
                    params.append(grade_filter)
                cursor.execute(f"""
                    SELECT COUNT(DISTINCT s_qa.user_id)
                    FROM quiz_attempt qa
                    JOIN quizzes q ON qa.quiz_id = q.quiz_id
                    {QUIZ_STUDENT_JOIN}
                    WHERE q.topic_id = %s{grade_clause}
                """, tuple(params))
                result = cursor.fetchone()
                attempted_count = result[0] if result else 0
            except Exception:
                pass
            
            mastery_pct = round((mastered_count / total_students) * 100, 1) if total_students > 0 else 0
            
            struggling_students = fetch_struggling_students_for_topic(cursor, topic_id, grade_filter)
            
            not_started_students = []
            try:
                grade_join = ""
                params = [topic_id]
                if grade_filter is not None:
                    grade_join = (
                        " JOIN students s_ns ON u.user_id = s_ns.user_id AND s_ns.grade_level = %s"
                    )
                    params = [grade_filter, topic_id]
                cursor.execute(f"""
                    SELECT u.user_id, u.full_name
                    FROM users u{grade_join}
                    WHERE u.role = 'student'
                    AND u.user_id NOT IN (
                        SELECT DISTINCT s_qa.user_id
                        FROM quiz_attempt qa
                        JOIN quizzes q ON qa.quiz_id = q.quiz_id
                        {QUIZ_STUDENT_JOIN}
                        WHERE q.topic_id = %s
                    )
                """, tuple(params))
                for s in cursor.fetchall() or []:
                    prereqs_met = check_prerequisites_met(cursor, s[0], topic_id)
                    if not prereqs_met:
                        not_started_students.append({
                            'student_id': s[0],
                            'full_name': s[1]
                        })
            except Exception:
                pass
            
            overview.append({
                'topic_id': topic_id,
                'topic_name': topic[1],
                'grade_level': topic[2],
                'total_students': total_students,
                'mastered_count': mastered_count,
                'attempted_count': attempted_count,
                'mastery_pct': mastery_pct,
                'struggling_students': struggling_students,
                'blocked_students': not_started_students
            })
        
        cursor.close()
        conn.close()
        return jsonify({
            "overview": overview,
            "total_students": total_students,
            "grade_level": grade_filter,
        })
    except Exception as e:
        print(f"Error in /api/teacher/mastery-overview: {e}")
        return jsonify({"error": str(e), "overview": [], "total_students": 0}), 200

@app.route('/api/teacher/heatmap', methods=['GET'])
def get_teacher_heatmap():
    """Class-wide gap heatmap showing mastery percentage and student breakdown per topic."""
    try:
        grade_filter = parse_teacher_grade(request.args.get('grade_level'))
        conn = get_db_connection()
        cursor = conn.cursor()

        if grade_filter is not None:
            cursor.execute(
                """
                SELECT COUNT(*) FROM users u
                JOIN students s ON u.user_id = s.user_id
                WHERE u.role = 'student' AND s.grade_level = %s
                """,
                (grade_filter,),
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
        result = cursor.fetchone()
        total_students = result[0] if result else 0 or 0

        if grade_filter is not None:
            cursor.execute(
                "SELECT topic_id, topic_name, grade_level FROM topics WHERE grade_level = %s ORDER BY topic_id",
                (grade_filter,),
            )
        else:
            cursor.execute("SELECT topic_id, topic_name, grade_level FROM topics ORDER BY grade_level, topic_id")
        topics = cursor.fetchall() or []

        from gap_utils import (
            count_students_mastered_topic,
            count_students_struggling_topic,
            count_students_untouched_topic,
            fetch_struggling_students_for_topic,
        )

        heatmap = []
        for topic in topics:
            topic_id = topic[0]

            mastered_count = count_students_mastered_topic(cursor, topic_id, grade_filter)
            struggling_count = count_students_struggling_topic(cursor, topic_id, grade_filter)
            untouched_count = count_students_untouched_topic(cursor, topic_id, grade_filter)
            struggling_students = fetch_struggling_students_for_topic(cursor, topic_id, grade_filter)

            mastery_pct = round((mastered_count / total_students) * 100) if total_students > 0 else 0

            if mastery_pct >= 70:
                status = 'good'
            elif mastery_pct >= 40:
                status = 'needs_attention'
            else:
                status = 'critical'

            heatmap.append({
                'topic_id': topic_id,
                'topic_name': topic[1],
                'grade_level': topic[2],
                'total_students': total_students,
                'mastered_count': mastered_count,
                'struggling_count': struggling_count,
                'untouched_count': untouched_count,
                'mastery_percentage': mastery_pct,
                'mastery_pct': mastery_pct,
                'status': status,
                'struggling_students': struggling_students
            })

        cursor.close()
        conn.close()
        return jsonify({
            "heatmap": heatmap,
            "total_students": total_students,
            "grade_level": grade_filter,
        })
    except Exception as e:
        print(f"Error in /api/teacher/heatmap: {e}")
        return jsonify({"error": str(e), "heatmap": [], "total_students": 0}), 200

@app.route('/api/student/<int:student_id>/recommendations', methods=['GET'])
def get_student_recommendations(student_id):
    """Personalized quiz recommendations based on skill gaps.
    Returns quizzes for weak topics that the student hasn't taken yet."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        from gap_utils import QUIZ_STUDENT_JOIN, fetch_student_gaps
        gap_topics = fetch_student_gaps(cursor, student_id)

        recommendations = []
        for topic in gap_topics:
            topic_id = topic['topic_id']
            topic_name = topic['topic_name']
            avg_score = topic['avg_score']

            if avg_score < 40:
                reason = f"You need to improve {topic_name}"
            else:
                reason = f"Practice more {topic_name} to reach mastery"

            # Find quizzes for this topic the student hasn't taken
            cursor.execute(f"""
                SELECT q.quiz_id, q.title, q.total_marks
                FROM quizzes q
                WHERE q.topic_id = %s
                AND q.quiz_id NOT IN (
                    SELECT qa.quiz_id
                    FROM quiz_attempt qa
                    {QUIZ_STUDENT_JOIN}
                    WHERE s_qa.user_id = %s
                )
                LIMIT 2
            """, (topic_id, student_id))
            for quiz in cursor.fetchall():
                recommendations.append({
                    'quiz_id': quiz[0],
                    'title': quiz[1],
                    'topic_name': topic_name,
                    'total_marks': quiz[2],
                    'avg_score': avg_score,
                    'reason': reason
                })

            if len(recommendations) >= 5:
                break

        if len(recommendations) < 5:
            cursor.execute(f"""
                SELECT t.topic_id, t.topic_name
                FROM topics t
                WHERE t.topic_id NOT IN (
                    SELECT DISTINCT q.topic_id
                    FROM quiz_attempt qa
                    JOIN quizzes q ON qa.quiz_id = q.quiz_id
                    {QUIZ_STUDENT_JOIN}
                    WHERE s_qa.user_id = %s
                )
                ORDER BY t.grade_level, t.topic_id
            """, (student_id,))
            unstarted_topics = cursor.fetchall()

            for topic in unstarted_topics:
                if len(recommendations) >= 5:
                    break
                topic_id = topic[0]
                topic_name = topic[1]

                # Check if prerequisites are met
                prereqs_met = check_prerequisites_met(cursor, student_id, topic_id)
                if not prereqs_met:
                    continue

                cursor.execute("""
                    SELECT q.quiz_id, q.title, q.total_marks
                    FROM quizzes q
                    WHERE q.topic_id = %s
                    LIMIT 2
                """, (topic_id,))
                for quiz in cursor.fetchall():
                    if len(recommendations) >= 5:
                        break
                    recommendations.append({
                        'quiz_id': quiz[0],
                        'title': quiz[1],
                        'topic_name': topic_name,
                        'total_marks': quiz[2],
                        'avg_score': None,
                        'reason': f"Try {topic_name} - a new topic for you"
                    })

        cursor.close()
        conn.close()
        return jsonify({"recommendations": recommendations[:5]})
    except Exception as e:
        print(f"Error in /api/student/{student_id}/recommendations: {e}")
        return jsonify({"recommendations": []}), 200

@app.route('/api/student/<int:student_id>/completed-quizzes', methods=['GET'])
def get_completed_quizzes(student_id):
    """Return quiz_ids the student has completed with their best scores."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Look up actual student_id from students table (URL param is user_id)
        cursor.execute("SELECT student_id FROM students WHERE user_id = %s", (student_id,))
        student_record = cursor.fetchone()
        if not student_record:
            cursor.close()
            conn.close()
            return jsonify({"completed_quizzes": {}})
        actual_student_id = student_record[0]

        cursor.execute("""
            SELECT quiz_id, MAX(score) as best_score
            FROM quiz_attempt
            WHERE student_id = %s
            GROUP BY quiz_id
        """, (actual_student_id,))
        rows = cursor.fetchall() or []
        cursor.close()
        conn.close()

        completed = {}
        for row in rows:
            completed[str(row[0])] = row[1]
        return jsonify({"completed_quizzes": completed})
    except Exception as e:
        print(f"Error in /api/student/{student_id}/completed-quizzes: {e}")
        return jsonify({"completed_quizzes": {}}), 200

@app.route('/api/student/materials', methods=['GET'])
def get_student_materials():
    """Get approved materials assigned to a specific student."""
    try:
        student_id = request.args.get('student_id')
        if not student_id:
            return jsonify({"error": "student_id is required", "materials": []}), 400
        try:
            student_id = int(student_id)
        except (TypeError, ValueError):
            return jsonify({"error": "student_id must be a valid integer", "materials": []}), 400

        import material_delivery as delivery
        conn = get_db_connection()
        cursor = conn.cursor()
        delivery.ensure_student_materials_table(cursor)

        extra_cols = delivery.existing_material_columns(cursor)
        select_cols = delivery.build_material_select('m', 't', include_topic_id=True)
        select_cols += [f'm.{c}' for c in extra_cols]
        select_sql = ', '.join(select_cols)

        user_id = delivery.resolve_student_user_id(cursor, student_id)
        if not user_id:
            cursor.close()
            conn.close()
            return jsonify({"materials": []})

        sm_join = delivery.student_materials_filter_by_user_sql('%s')
        cursor.execute(f"""
            SELECT {select_sql}
            FROM material m
            LEFT JOIN topics t ON m.topic_id = t.topic_id
            {sm_join}
            WHERE m.approval_status = 'Approved'
            ORDER BY m.generated_date DESC
        """, (user_id,))
        
        materials = cursor.fetchall() or []
        materials_list = [
            delivery.material_row_to_dict(m, extra_cols, has_topic_id=True)
            for m in materials
        ]
        
        cursor.close()
        conn.close()
        return jsonify({"materials": materials_list})
    except Exception as e:
        print(f"Error in /api/student/materials: {e}")
        return jsonify({"materials": []}), 500

@app.route('/api/curriculum/index-status', methods=['GET'])
def curriculum_index_status():
    """Report which textbooks are indexed in FAISS (for debugging missing Grade 11/12)."""
    try:
        import rag_service as rag
        status = rag.get_indexed_textbooks()
        status['faiss_available'] = rag.faiss_available()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/curriculum/search', methods=['GET', 'POST'])
def search_curriculum():
    """Search curriculum using FAISS index and return full text results."""
    try:
        import rag_service as rag
        if request.method == 'POST':
            data = request.get_json() or {}
            query = data.get('query', '').strip()
            grade_level = data.get('grade_level')
        else:
            query = request.args.get('q', '').strip()
            grade_level = request.args.get('grade_level')

        if not query:
            return jsonify({"error": "Search query required"}), 400

        if grade_level is not None:
            grade_level = int(grade_level)

        results = rag.search_curriculum(query, grade_level, k=5)
        if not results and not rag.faiss_available():
            return jsonify({"error": "FAISS index or vectorizer could not be loaded"}), 500

        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== FAISS TEST WITH DETAILED DEBUG LOGGING ====================
@app.route('/api/faiss/test', methods=['GET'])
def faiss_test():
    """Test endpoint that loads FAISS index and vectorizer with detailed debug logging."""
    try:
        import os
        import pickle
        import sys
        import faiss
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        index_path = os.path.join(current_dir, 'faiss_index', 'index.faiss')
        vectorizer_path = os.path.join(current_dir, 'faiss_index', 'vectorizer.pkl')
        
        # Log everything
        print(f"[DEBUG FAISS] ========================================")
        print(f"[DEBUG FAISS] Python version: {sys.version}")
        print(f"[DEBUG FAISS] Current directory: {current_dir}")
        print(f"[DEBUG FAISS] Looking for index at: {index_path}")
        print(f"[DEBUG FAISS] Looking for vectorizer at: {vectorizer_path}")
        print(f"[DEBUG FAISS] Index exists: {os.path.exists(index_path)}")
        print(f"[DEBUG FAISS] Vectorizer exists: {os.path.exists(vectorizer_path)}")
        
        # List directory contents
        try:
            print(f"[DEBUG FAISS] Directory contents of {current_dir}:")
            for item in os.listdir(current_dir):
                print(f"  - {item}")
        except Exception as e:
            print(f"[DEBUG FAISS] Error listing directory: {e}")
        
        # Check if faiss_index folder exists
        faiss_dir = os.path.join(current_dir, 'faiss_index')
        if os.path.exists(faiss_dir):
            print(f"[DEBUG FAISS] faiss_index folder contents:")
            for item in os.listdir(faiss_dir):
                print(f"  - {item}")
        else:
            print(f"[DEBUG FAISS] faiss_index folder NOT found!")
        
        print(f"[DEBUG FAISS] FAISS imported successfully, version: {faiss.__version__}")

        if not os.path.exists(index_path):
            return jsonify({"error": f"FAISS index file not found at {index_path}"}), 404
        if not os.path.exists(vectorizer_path):
            return jsonify({"error": f"Vectorizer file not found at {vectorizer_path}"}), 404

        print(f"[DEBUG FAISS] Loading FAISS index...")
        index = faiss.read_index(index_path)
        print(f"[DEBUG FAISS] FAISS index loaded, size: {index.ntotal}")
        
        print(f"[DEBUG FAISS] Loading vectorizer...")
        with open(vectorizer_path, 'rb') as f:
            vectorizer = pickle.load(f)
        print(f"[DEBUG FAISS] Vectorizer loaded successfully")
        
        print(f"[DEBUG FAISS] ========================================")

        return jsonify({
            "status": "FAISS loaded successfully",
            "index_size": index.ntotal,
            "index_path": index_path,
            "vectorizer_path": vectorizer_path,
            "current_directory": current_dir
        })
    except Exception as e:
        import traceback
        print(f"[ERROR FAISS TEST] {e}")
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500

# ==================== MATERIAL GENERATION ENDPOINT ====================
@app.route('/api/materials/generate', methods=['POST'])
def generate_practice_material():
    try:
        data = request.get_json() or {}
        print(f"[DEBUG] Received data: {data}")
        
        topic_name = data.get('topic_name', '').strip()
        student_id = data.get('student_id')
        grade_level = data.get('grade_level')
        for_all_students = data.get('for_all_students', False)
        difficulty = data.get('difficulty', 'medium')
        teacher_id = data.get('teacher_id', 1)

        if not topic_name:
            return jsonify({"error": "topic_name is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Get topic_id from topics table (create if not exists)
        cursor.execute("SELECT topic_id FROM topics WHERE topic_name LIKE %s LIMIT 1", (f'%{topic_name}%',))
        topic_row = cursor.fetchone()
        if not topic_row:
            cursor.execute(
                "INSERT INTO topics (topic_name, grade_level) VALUES (%s, %s)",
                (topic_name, grade_level or 10)
            )
            topic_id = cursor.lastrowid
            conn.commit()
        else:
            topic_id = topic_row[0]

        # 2. Generate sample questions
        sample_questions = [
            f"What is the main concept of {topic_name}?",
            f"Explain how {topic_name} applies to real-world situations.",
            f"Solve a practice problem related to {topic_name}.",
            f"Describe the key principles of {topic_name}."
        ]

        html_content = f"""
        <h2>Practice Material: {topic_name}</h2>
        <p><strong>Difficulty:</strong> {difficulty}</p>
        <p><strong>Teacher ID:</strong> {teacher_id}</p>
        <hr>
        <h3>Questions:</h3>
        <ol>
            <li>{sample_questions[0]}</li>
            <li>{sample_questions[1]}</li>
            <li>{sample_questions[2]}</li>
            <li>{sample_questions[3]}</li>
        </ol>
        <p><strong>Source:</strong> Generated by EDUCARE AI</p>
        """

        # 3. Insert into material table with Pending status
        cursor.execute("""
            INSERT INTO material 
            (topic_id, title, content, source_citation, source_file, source_page, source_grade, 
             generated_date, approval_status, teacher_id, difficulty)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s)
        """, (
            topic_id,
            f"Practice: {topic_name}",
            html_content,
            "Generated by EDUCARE AI",
            "curriculum_data/sample.pdf",
            "1",
            str(grade_level or 10),
            'Pending',
            teacher_id,
            difficulty
        ))
        material_id = cursor.lastrowid
        conn.commit()
        print(f"[DEBUG] Material inserted with ID: {material_id}")

        # 4. If student_id is provided, link to that student
        if student_id:
            # FIXED: Use 'id' instead of 'student_id'
            cursor.execute("SELECT id FROM students WHERE user_id = %s", (student_id,))
            student_row = cursor.fetchone()
            if student_row:
                actual_student_id = student_row[0]
                cursor.execute("""
                    INSERT INTO student_materials (student_id, material_id, status, assigned_date)
                    VALUES (%s, %s, 'Pending', NOW())
                """, (actual_student_id, material_id))
                conn.commit()
                print(f"[DEBUG] Linked material to student: {actual_student_id}")

        # 5. If for_all_students is true, link to all students in the grade
        if for_all_students and grade_level:
            # FIXED: Use 'id' instead of 'student_id'
            cursor.execute("""
                SELECT id FROM students WHERE grade_level = %s
            """, (grade_level,))
            students = cursor.fetchall()
            for student in students:
                cursor.execute("""
                    INSERT INTO student_materials (student_id, material_id, status, assigned_date)
                    VALUES (%s, %s, 'Pending', NOW())
                """, (student[0], material_id))
            conn.commit()
            print(f"[DEBUG] Linked material to {len(students)} students")

        cursor.close()
        conn.close()

        return jsonify({
            "material_id": material_id,
            "title": f"Practice: {topic_name}",
            "topic_name": topic_name,
            "grade_level": grade_level or 10,
            "difficulty": difficulty,
            "questions_count": len(sample_questions),
            "message": "Material generated and sent for teacher approval",
            "status": "pending"
        }), 201

    except Exception as e:
        print(f"[ERROR] Material generation failed: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/curriculum/search/faiss', methods=['POST'])
def search_curriculum_faiss():
    """Search curriculum using FAISS index. Returns chunk indexes and distances."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip() if data else ''

        if not query:
            return jsonify({"error": "Query 'query' is required"}), 400

        index_path = os.path.join('faiss_index', 'index.faiss')
        vectorizer_path = os.path.join('faiss_index', 'vectorizer.pkl')

        try:
            index = faiss.read_index(index_path)
            with open(vectorizer_path, 'rb') as f:
                vectorizer = pickle.load(f)
        except Exception:
            return jsonify({"error": "FAISS index or vectorizer could not be loaded"}), 500

        query_vector = vectorizer.transform([query]).toarray().astype('float32')
        distances, indices = index.search(query_vector, 5)

        return jsonify({
            "indexes": [int(i) for i in indices[0]],
            "distances": [float(d) for d in distances[0]]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Advanced RAG routes (quiz AI, assistant, batch, analytics, etc.)
from material_routes import register_routes as _register_material_routes
_material_helpers = _register_material_routes(app, get_db_connection)

# Peer-to-peer student questions (broadcast questions, private answers)
from peer_routes import register_routes as _register_peer_routes
_register_peer_routes(app, get_db_connection)

# File uploads (peer attachments, quiz question images)
from upload_routes import register_routes as _register_upload_routes
_register_upload_routes(app, get_db_connection)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)