from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
import MySQLdb
import random
import json
import os

# Optional imports - app will work without these
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

try:
    import pickle
except ImportError:
    import pickle as pickle

try:
    import numpy as np
except ImportError:
    np = None

# bcrypt for password hashing - define placeholder first, then import
bcrypt = None
BCRYPT_AVAILABLE = False
try:
    import bcrypt
    if bcrypt:
        BCRYPT_AVAILABLE = True
except ImportError:
    pass

app = Flask(__name__)
CORS(app, 
     origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
     supports_credentials=True,
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
     expose_headers=["Content-Type", "Authorization"],
     max_age=3600)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'educare-secret-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # tokens don't expire in dev
jwt = JWTManager(app)

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'absra123',
    'database': 'educare',
    'charset': 'utf8mb4'
}

# Function to get database connection
def get_db_connection():
    return MySQLdb.connect(**db_config)


def require_role(*allowed_roles):
    """Return (identity, error_response) tuple. error_response is None if OK."""
    identity = get_jwt_identity()
    if not identity:
        return None, (jsonify({"error": "Authentication required"}), 401)
    if identity.get('role') not in allowed_roles:
        return None, (jsonify({"error": "Access denied: insufficient permissions"}), 403)
    return identity, None

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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE KEY unique_teacher (user_id)
            )
        """)
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
                FOREIGN KEY (student_id) REFERENCES students(user_id) ON DELETE CASCADE,
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
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_assistant_conversations_student_id
            ON assistant_conversations(student_id)
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("Assistant conversations table initialized successfully")
    except Exception as e:
        print(f"Error initializing assistant table: {e}")

init_assistant_table()

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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.user_id, u.full_name, u.email, s.grade_level, s.section
            FROM users u
            JOIN students s ON u.user_id = s.user_id
            WHERE u.role = 'student'
        """)
        students = cursor.fetchall()
        cursor.close()
        conn.close()
        
        students_list = []
        for student in students:
            students_list.append({
                'user_id': student[0],
                'full_name': student[1],
                'email': student[2],
                'grade_level': student[3],
                'section': student[4]
            })
        
        return jsonify({"students": students_list})
    except Exception as e:
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
            "SELECT user_id, full_name, email, role, password FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        stored_password = user[4]
        
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        full_name = data.get('full_name')
        email = data.get('email')
        password = data.get('password')
        grade_level = data.get('grade_level')
        section = data.get('section')
        
        if not full_name or not email or not password:
            return jsonify({"error": "All fields required"}), 400
        if not grade_level or not section:
            return jsonify({"error": "Grade level and section are required"}), 400

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

        cursor.execute(
            "INSERT INTO users (full_name, email, password, role, is_verified) VALUES (%s, %s, %s, 'student', TRUE)",
            (full_name, email, hashed_password)
        )
        user_id = int(cursor.lastrowid)

        cursor.execute(
            "INSERT INTO students (user_id, grade_level, section, enrollment_date) VALUES (%s, %s, %s, CURDATE())",
            (user_id, grade_level, section)
        )
        
        conn.commit()
        cursor.close()
        conn.close()

        access_token = create_access_token(identity={
            'user_id': user_id,
            'role': 'student'
        })
        
        return jsonify({
            "message": "Account created successfully! You can now login.",
            "user_id": user_id,
            "full_name": full_name,
            "email": email,
            "role": "student",
            "token": access_token
        }), 201
        
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
                    questions.append({
                        'question_id': row[0],
                        'question_text': row[1],
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

        score = 0
        total_questions = len(correct_answers) if correct_answers else 1
        points_per_question = 10

        for answer in answers:
            question_id = answer.get('question_id')
            user_answer = answer.get('answer')
            if correct_answers.get(question_id) == user_answer:
                score += points_per_question

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

        total_possible = len(answers) * points_per_question
        response_data = {
            "message": "Quiz submitted successfully",
            "score": score,
            "total_possible": total_possible,
            "percentage": (score / total_possible) * 100 if total_possible > 0 else 0
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
        
        questions_saved = 0
        for q in questions:
            try:
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
        
        questions_saved = 0
        for q in questions:
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
    try:
        data = request.get_json()
        full_name = data.get('full_name')
        email = data.get('email')
        password = data.get('password')
        student_email = data.get('student_email')  # Student email to link
        relationship = data.get('relationship', 'parent')
        
        if not full_name or not email or not password or not student_email:
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
        
        # Look up student by email
        cursor.execute("SELECT user_id FROM users WHERE email = %s AND role = 'student'", (student_email,))
        student = cursor.fetchone()
        if not student:
            cursor.close()
            conn.close()
            return jsonify({"error": "Student with this email not found"}), 400
        
        student_id = student[0]
        
        cursor.execute(
            "INSERT INTO users (full_name, email, password, role, is_verified) VALUES (%s, %s, %s, 'family', TRUE)",
            (full_name, email, hashed_password)
        )
        user_id = cursor.lastrowid()
        
        # Link to student
        cursor.execute(
            "INSERT INTO family (user_id, student_id, relationship) VALUES (%s, %s, %s)",
            (user_id, student_id, relationship)
        )
        
        conn.commit()

        cursor.execute("""
            SELECT f.student_id, u.full_name, s.grade_level, s.section
            FROM family f
            JOIN students s ON f.student_id = s.user_id
            JOIN users u ON s.user_id = u.user_id
            WHERE f.user_id = %s
        """, (user_id,))
        linked = cursor.fetchall() or []
        students_list = [{
            'user_id': row[0],
            'full_name': row[1],
            'grade_level': row[2],
            'section': row[3],
        } for row in linked]

        cursor.close()
        conn.close()

        access_token = create_access_token(identity={
            'user_id': user_id,
            'role': 'family'
        })
        
        return jsonify({
            "message": "Account created successfully! You can now login.",
            "user_id": user_id,
            "full_name": full_name,
            "email": email,
            "role": "family",
            "token": access_token,
            "students": students_list,
            "linked_students": len(students_list)
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        cursor.execute(
            "SELECT user_id, full_name, email, role, password FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid credentials"}), 401
        
        stored_password = user[4]
        
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
        
        # Check if user has family role
        if user[3] != 'family':
            cursor.close()
            conn.close()
            return jsonify({"error": "Access denied. Family account required."}), 403
        
        # Get linked students
        cursor.execute("""
            SELECT f.student_id, u.full_name, s.grade_level, s.section
            FROM family f
            JOIN students s ON f.student_id = s.user_id
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
            SELECT f.student_id, u.full_name, s.grade_level, s.section
            FROM family f
            JOIN students s ON f.student_id = s.user_id
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
                SELECT q.quiz_id, q.title, q.total_marks
                FROM quizzes q
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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get student info
        cursor.execute("""
            SELECT u.full_name, s.grade_level, s.section
            FROM users u
            JOIN students s ON u.user_id = s.user_id
            WHERE u.user_id = %s
        """, (student_id,))
        student_info = cursor.fetchone()
        
        if not student_info:
            cursor.close()
            conn.close()
            return jsonify({"error": "Student not found"}), 404
        
        from gap_utils import QUIZ_STUDENT_JOIN, fetch_student_gaps
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
        gaps_list = fetch_student_gaps(cursor, student_id)
        
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
                'topic': attempt[5],
                'total_marks': attempt[6],
                'percentage': round((attempt[2] / attempt[6]) * 100, 1) if attempt[6] else 0
            })
        
        # Calculate overall stats
        total_attempts = len(attempts_list)
        avg_score = round(sum(a['percentage'] for a in attempts_list) / total_attempts, 1) if total_attempts > 0 else 0
        highest_score = max((a['percentage'] for a in attempts_list), default=0)
        lowest_score = min((a['percentage'] for a in attempts_list), default=0)
        
        return jsonify({
            "student": {
                "name": student_info[0],
                "grade_level": student_info[1],
                "section": student_info[2]
            },
            "stats": {
                "total_attempts": total_attempts,
                "average_score": avg_score,
                "highest_score": highest_score,
                "lowest_score": lowest_score,
                "topics_needing_work": len(gaps_list)
            },
            "attempts": attempts_list,
            "gaps": gaps_list
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== MATERIAL APPROVAL ENDPOINTS ====================

@app.route('/api/materials/pending', methods=['GET'])
def get_pending_materials():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.material_id, m.title, m.content, m.source_citation,
                   m.generated_date, t.topic_name
            FROM material m
            LEFT JOIN topics t ON m.topic_id = t.topic_id
            WHERE m.approval_status = 'Pending'
            ORDER BY m.generated_date DESC
        """)
        materials = cursor.fetchall() or []
        
        materials_list = []
        for material in materials:
            materials_list.append({
                'material_id': material[0],
                'title': material[1],
                'content': material[2],
                'source_citation': material[3],
                'generated_date': str(material[4]) if material[4] else '',
                'topic_name': material[5] if material[5] else ''
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({"materials": materials_list})
    except Exception as e:
        print(f"Error in /api/materials/pending: {e}")
        return jsonify({"error": str(e), "materials": []}), 200

@app.route('/api/materials/approve/<int:material_id>', methods=['POST'])
def approve_material(material_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if material exists
        cursor.execute("SELECT material_id FROM material WHERE material_id = %s", (material_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Material not found"}), 404
        
        # Update status to Approved
        cursor.execute(
            "UPDATE material SET approval_status = 'Approved' WHERE material_id = %s",
            (material_id,)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Material approved successfully"}), 200
    except Exception as e:
        print(f"Error in /api/materials/approve/{material_id}: {e}")
        return jsonify({"error": str(e)}), 200

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
        
        if student_id:
            from gap_utils import QUIZ_STUDENT_JOIN
            cursor.execute(f"""
                SELECT m.material_id, m.title, m.content, m.source_citation,
                       m.generated_date, t.topic_name
                FROM material m
                JOIN topics t ON m.topic_id = t.topic_id
                WHERE m.approval_status = 'Approved'
                AND m.topic_id IN (
                    SELECT t2.topic_id
                    FROM quiz_attempt qa
                    JOIN quizzes q ON qa.quiz_id = q.quiz_id
                    JOIN topics t2 ON q.topic_id = t2.topic_id
                    {QUIZ_STUDENT_JOIN}
                    WHERE s_qa.user_id = %s
                    GROUP BY t2.topic_id
                    HAVING AVG(qa.score * 100.0 / NULLIF(q.total_marks, 0)) < 70
                )
                ORDER BY m.generated_date DESC
            """, (student_id,))
        else:
            # Get all approved materials
            cursor.execute("""
                SELECT m.material_id, m.title, m.content, m.source_citation,
                       m.generated_date, t.topic_name
                FROM material m
                JOIN topics t ON m.topic_id = t.topic_id
                WHERE m.approval_status = 'Approved'
                ORDER BY m.generated_date DESC
            """)
        
        materials = cursor.fetchall()
        
        materials_list = []
        for material in materials:
            materials_list.append({
                'material_id': material[0],
                'title': material[1],
                'content': material[2],
                'source_citation': material[3],
                'generated_date': str(material[4]),
                'topic_name': material[5]
            })
        
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
        cursor.execute(
            "SELECT user_id, full_name, email, role, password FROM users WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid credentials"}), 401
        
        stored_password = user[4]
        
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
        
        # Check if user has admin role
        if user[3] != 'admin':
            cursor.close()
            conn.close()
            return jsonify({"error": "Access denied. Admin account required."}), 403
        
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
                       t.qualification, t.subject
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
                    'subject': user[6]
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
@jwt_required(optional=True)
def admin_create_user():
    try:
        identity = get_jwt_identity()
        if identity and identity.get('role') != 'admin':
            return jsonify({"error": "Access denied"}), 403
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
        
        # Hash the password using bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Email already registered"}), 400
        
        # Insert user with hashed password
        cursor.execute(
            "INSERT INTO users (full_name, email, password, role, created_at) VALUES (%s, %s, %s, %s, NOW())",
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
            if not qualification or not subject:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({"error": "Qualification and subject are required for teachers"}), 400
            cursor.execute(
                "INSERT INTO teachers (user_id, qualification, subject) VALUES (%s, %s, %s)",
                (user_id, qualification, subject)
            )
        elif role == 'family':
            if not student_ids:
                conn.rollback()
                cursor.close()
                conn.close()
                return jsonify({"error": "At least one student ID is required for family accounts"}), 400
            
            for student_id in student_ids:
                cursor.execute("SELECT user_id FROM students WHERE user_id = %s", (student_id,))
                if not cursor.fetchone():
                    conn.rollback()
                    cursor.close()
                    conn.close()
                    return jsonify({"error": f"Student with ID {student_id} not found"}), 400
                
                cursor.execute(
                    "INSERT INTO family (user_id, student_id, relationship) VALUES (%s, %s, %s)",
                    (user_id, student_id, relationship)
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
@jwt_required(optional=True)
def admin_update_user(user_id):
    try:
        identity = get_jwt_identity()
        if identity and identity.get('role') != 'admin':
            return jsonify({"error": "Access denied"}), 403
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
            # Hash the password using bcrypt
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
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
            if qualification and subject:
                cursor.execute("SELECT user_id FROM teachers WHERE user_id = %s", (user_id,))
                if cursor.fetchone():
                    cursor.execute(
                        "UPDATE teachers SET qualification = %s, subject = %s WHERE user_id = %s",
                        (qualification, subject, user_id)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO teachers (user_id, qualification, subject) VALUES (%s, %s, %s)",
                        (user_id, qualification, subject)
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
@jwt_required(optional=True)
def admin_delete_user(user_id):
    try:
        identity = get_jwt_identity()
        if identity and identity.get('role') != 'admin':
            return jsonify({"error": "Access denied"}), 403
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
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all topics
        cursor.execute("SELECT topic_id, topic_name, grade_level FROM topics ORDER BY grade_level, topic_id")
        topics = cursor.fetchall() or []
        
        # Get total students count
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
            
            mastered_count = count_students_mastered_topic(cursor, topic_id)
            attempted_count = 0
            try:
                cursor.execute(f"""
                    SELECT COUNT(DISTINCT s_qa.user_id)
                    FROM quiz_attempt qa
                    JOIN quizzes q ON qa.quiz_id = q.quiz_id
                    {QUIZ_STUDENT_JOIN}
                    WHERE q.topic_id = %s
                """, (topic_id,))
                result = cursor.fetchone()
                attempted_count = result[0] if result else 0
            except Exception:
                pass
            
            mastery_pct = round((mastered_count / total_students) * 100, 1) if total_students > 0 else 0
            
            struggling_students = fetch_struggling_students_for_topic(cursor, topic_id)
            
            not_started_students = []
            try:
                cursor.execute(f"""
                    SELECT u.user_id, u.full_name
                    FROM users u
                    WHERE u.role = 'student'
                    AND u.user_id NOT IN (
                        SELECT DISTINCT s_qa.user_id
                        FROM quiz_attempt qa
                        JOIN quizzes q ON qa.quiz_id = q.quiz_id
                        {QUIZ_STUDENT_JOIN}
                        WHERE q.topic_id = %s
                    )
                """, (topic_id,))
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
        return jsonify({"overview": overview, "total_students": total_students})
    except Exception as e:
        print(f"Error in /api/teacher/mastery-overview: {e}")
        return jsonify({"error": str(e), "overview": [], "total_students": 0}), 200

@app.route('/api/teacher/heatmap', methods=['GET'])
def get_teacher_heatmap():
    """Class-wide gap heatmap showing mastery percentage and student breakdown per topic."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
        result = cursor.fetchone()
        total_students = result[0] if result else 0 or 0

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

            mastered_count = count_students_mastered_topic(cursor, topic_id)
            struggling_count = count_students_struggling_topic(cursor, topic_id)
            untouched_count = count_students_untouched_topic(cursor, topic_id)
            struggling_students = fetch_struggling_students_for_topic(cursor, topic_id)

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
        return jsonify({"heatmap": heatmap, "total_students": total_students})
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
    """Get approved materials for students."""
    try:
        student_id = request.args.get('student_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f"[DEBUG] get_student_materials called with student_id={student_id}")
        
        cursor.execute("SELECT COUNT(*) FROM material WHERE approval_status = 'Approved'")
        approved_count = cursor.fetchone()[0]
        print(f"[DEBUG] Approved materials in DB: {approved_count}")
        
        select_cols = """
            m.material_id, m.title, m.content, m.source_citation,
            m.generated_date, t.topic_name, m.topic_id
        """
        try:
            cursor.execute("SHOW COLUMNS FROM material LIKE 'source_file'")
            if cursor.fetchone():
                select_cols = """
                    m.material_id, m.title, m.content, m.source_citation,
                    m.generated_date, t.topic_name, m.topic_id,
                    m.source_file, m.source_page, m.source_grade, m.section_title
                """
        except Exception:
            pass

        cursor.execute(f"""
            SELECT {select_cols}
            FROM material m
            LEFT JOIN topics t ON m.topic_id = t.topic_id
            WHERE m.approval_status = 'Approved'
            ORDER BY m.generated_date DESC
        """)
        
        materials = cursor.fetchall() or []
        print(f"[DEBUG] Materials fetched: {len(materials)}")
        
        materials_list = []
        for material in materials:
            item = {
                'material_id': material[0],
                'title': material[1],
                'content': material[2],
                'source_citation': material[3],
                'generated_date': str(material[4]) if material[4] else '',
                'topic_name': material[5] if material[5] else '',
                'topic_id': material[6],
            }
            if len(material) > 7:
                item['source_file'] = material[7]
                item['source_page'] = material[8]
                item['source_grade'] = material[9]
                item['section_title'] = material[10]
            materials_list.append(item)
        
        cursor.close()
        conn.close()
        return jsonify({"materials": materials_list})
    except Exception as e:
        print(f"Error in /api/student/materials: {e}")
        return jsonify({"materials": []}), 200

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

@app.route('/api/faiss/test', methods=['GET'])
def faiss_test():
    """Test endpoint that loads FAISS index and vectorizer."""
    try:
        index_path = os.path.join('faiss_index', 'index.faiss')
        vectorizer_path = os.path.join('faiss_index', 'vectorizer.pkl')

        if not os.path.exists(index_path):
            return jsonify({"error": "FAISS index file not found at faiss_index/index.faiss"}), 404
        if not os.path.exists(vectorizer_path):
            return jsonify({"error": "Vectorizer file not found at faiss_index/vectorizer.pkl"}), 404

        index = faiss.read_index(index_path)
        with open(vectorizer_path, 'rb') as f:
            vectorizer = pickle.load(f)

        return jsonify({
            "status": "FAISS loaded successfully",
            "index_size": index.ntotal
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==================== LOCAL RAG GENERATION ENDPOINT ====================

@app.route('/api/materials/generate', methods=['POST'])
def generate_practice_material():
    """
    Weakness-targeted RAG material generation for a specific student.
    Respects grade-level curriculum filter and 7-day deduplication.
    """
    try:
        data = request.get_json() or {}
        topic_name = data.get('topic_name', '').strip()
        student_id = data.get('student_id')
        difficulty = data.get('difficulty', 'medium')
        teacher_id = data.get('teacher_id', 1)
        skip_dedup = data.get('skip_dedup', False)

        if not topic_name:
            return jsonify({"error": "topic_name is required"}), 400
        if not student_id:
            return jsonify({"error": "student_id is required"}), 400

        helpers = _material_helpers
        conn = get_db_connection()
        cursor = conn.cursor()

        grade_level = helpers['student_grade'](cursor, student_id) or 10

        if not skip_dedup and helpers['dedup_recent'](cursor, student_id, topic_name):
            cursor.close()
            conn.close()
            return jsonify({
                "error": "Material for this topic was already generated within the last 7 days",
                "duplicate": True,
            }), 409

        html, cite, questions, _ = helpers['generate_material_core'](
            topic_name, grade_level, difficulty, num_questions=4
        )
        topic_id = helpers['resolve_topic_id'](cursor, topic_name)
        if not topic_id:
            cursor.close()
            conn.close()
            return jsonify({"error": "No topics found in database"}), 500

        material_id = helpers['insert_material'](
            cursor, topic_id, f"Practice: {topic_name}", html, cite, teacher_id
        )
        helpers['record_generation'](
            cursor, teacher_id, student_id, topic_name, grade_level, difficulty
        )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "material_id": material_id,
            "title": f"Practice: {topic_name}",
            "source_citation": cite['source_citation'],
            "source_file": cite.get('source_file'),
            "source_page": cite.get('source_page'),
            "source_grade": cite.get('source_grade'),
            "grade_level": grade_level,
            "questions_count": len(questions),
            "preview": html[:500],
            "message": "Material generated and sent for teacher approval",
        }), 201

    except Exception as e:
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

if __name__ == '__main__':
    app.run(debug=True)