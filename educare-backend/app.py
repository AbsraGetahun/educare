from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
import MySQLdb
import random
import json
import os
import faiss
import pickle
import numpy as np

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

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
        cursor.execute("""
            SELECT qa.attempt_id, qa.quiz_id, qa.score, qa.completed_at,
                   q.title, t.topic_name
            FROM quiz_attempt qa
            JOIN quizzes q ON qa.quiz_id = q.quiz_id
            JOIN topics t ON q.topic_id = t.topic_id
            WHERE qa.student_id = %s
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
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.topic_id, t.topic_name, 
                   AVG(r.score) as avg_score,
                   CASE 
                       WHEN AVG(r.score) < 40 THEN 'High'
                       WHEN AVG(r.score) < 70 THEN 'Moderate'
                       ELSE 'Low'
                   END as weakness_level
            FROM results r
            JOIN topics t ON r.topic_id = t.topic_id
            WHERE r.student_id = %s
            GROUP BY t.topic_id, t.topic_name
            HAVING AVG(r.score) < 70
        """, (student_id,))
        gaps = cursor.fetchall()
        cursor.close()
        conn.close()
        
        gaps_list = []
        for gap in gaps:
            gaps_list.append({
                'topic_id': gap[0],
                'topic_name': gap[1],
                'avg_score': round(gap[2], 2),
                'weakness_level': gap[3]
            })
        
        return jsonify({"gaps": gaps_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        
        if password != user[4]:
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

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Email already registered"}), 400

        cursor.execute(
            "INSERT INTO users (full_name, email, password, role) VALUES (%s, %s, %s, 'student')",
            (full_name, email, password)
        )
        user_id = int(cursor.lastrowid)

        cursor.execute(
            "INSERT INTO students (user_id, grade_level, section, enrollment_date) VALUES (%s, %s, %s, CURDATE())",
            (user_id, grade_level, section)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({"message": "Registration successful! Please login."}), 201
        
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
@jwt_required(optional=True)
def submit_quiz(quiz_id):
    try:
        identity = get_jwt_identity()
        if identity and identity.get('role') not in ('student', 'admin'):
            return jsonify({"error": "Access denied"}), 403
        data = request.get_json()
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

        # Look up student_id from students table using user_id
        cursor.execute("SELECT student_id FROM students WHERE user_id = %s", (student_id,))
        student_record = cursor.fetchone()
        if not student_record:
            cursor.close()
            conn.close()
            return jsonify({"error": "Student record not found"}), 404
        student_id = student_record[0]

        # Grade answers
        correct_answers = {1: 'B', 2: 'C', 3: 'C'}
        try:
            cursor.execute("""
                SELECT question_id, correct_answer
                FROM questions
                WHERE quiz_id = %s
                ORDER BY question_id
            """, (quiz_id,))
            question_rows = cursor.fetchall()
            if question_rows:
                correct_answers = {row[0]: row[1] for row in question_rows}
        except Exception:
            pass

        score = 0
        points_per_question = 5

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
            avg_score = get_student_mastery_for_topic(cursor, student_id, topic_id)
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
        return jsonify({"error": str(e)}), 500

# ==================== TEACHER ENDPOINTS ====================

@app.route('/api/quiz/<int:quiz_id>/results', methods=['GET'])
def get_quiz_results(quiz_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT qa.student_id, u.full_name, qa.score, qa.completed_at,
                   q.total_marks, q.title
            FROM quiz_attempt qa
            JOIN users u ON qa.student_id = u.user_id
            JOIN quizzes q ON qa.quiz_id = q.quiz_id
            WHERE qa.quiz_id = %s
            ORDER BY qa.score DESC
        """, (quiz_id,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        results_list = []
        for result in results:
            results_list.append({
                'student_id': result[0],
                'student_name': result[1],
                'score': result[2],
                'completed_at': str(result[3]),
                'total_marks': result[4],
                'quiz_title': result[5]
            })
        
        return jsonify({"results": results_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
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
        
        # Insert user with family role
        cursor.execute(
            "INSERT INTO users (full_name, email, password, role) VALUES (%s, %s, %s, 'family')",
            (full_name, email, password)
        )
        user_id = cursor.lastrowid
        
        # Link to student
        cursor.execute(
            "INSERT INTO family (user_id, student_id, relationship) VALUES (%s, %s, %s)",
            (user_id, student_id, relationship)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            "message": "Family account created successfully",
            "user_id": user_id,
            "linked_students": 1
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
        
        if password != user[4]:
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
        cursor.execute("""
            SELECT qa.attempt_id, qa.quiz_id, qa.score, qa.completed_at,
                   q.title, t.topic_name, q.total_marks
            FROM quiz_attempt qa
            JOIN quizzes q ON qa.quiz_id = q.quiz_id
            JOIN topics t ON q.topic_id = t.topic_id
            WHERE qa.student_id = %s
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
        cursor.execute("""
            SELECT t.topic_id, t.topic_name, 
                   AVG(r.score) as avg_score,
                   CASE 
                       WHEN AVG(r.score) < 40 THEN 'High'
                       WHEN AVG(r.score) < 70 THEN 'Moderate'
                       ELSE 'Low'
                   END as weakness_level
            FROM results r
            JOIN topics t ON r.topic_id = t.topic_id
            WHERE r.student_id = %s
            GROUP BY t.topic_id, t.topic_name
            HAVING AVG(r.score) < 70
        """, (student_id,))
        gaps = cursor.fetchall()
        
        gaps_list = []
        for gap in gaps:
            gaps_list.append({
                'topic_id': gap[0],
                'topic_name': gap[1],
                'avg_score': round(gap[2], 2),
                'weakness_level': gap[3]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({"gaps": gaps_list})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/family/student/<int:student_id>/recommendations', methods=['GET'])
def get_family_student_recommendations(student_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get topics where student has gaps
        cursor.execute("""
            SELECT t.topic_id, t.topic_name, AVG(r.score) as avg_score
            FROM results r
            JOIN topics t ON r.topic_id = t.topic_id
            WHERE r.student_id = %s
            GROUP BY t.topic_id, t.topic_name
            HAVING AVG(r.score) < 70
            ORDER BY avg_score ASC
            LIMIT 5
        """, (student_id,))
        gap_topics = cursor.fetchall()
        
        recommendations = []
        for topic in gap_topics:
            # Get quizzes for this topic that student hasn't taken yet
            cursor.execute("""
                SELECT q.quiz_id, q.title, q.total_marks
                FROM quizzes q
                WHERE q.topic_id = %s
                AND q.quiz_id NOT IN (
                    SELECT qa.quiz_id
                    FROM quiz_attempt qa
                    WHERE qa.student_id = %s
                )
                LIMIT 3
            """, (topic[0], student_id))
            quizzes = cursor.fetchall()
            
            for quiz in quizzes:
                recommendations.append({
                    'quiz_id': quiz[0],
                    'title': quiz[1],
                    'total_marks': quiz[2],
                    'topic_name': topic[1],
                    'avg_score': round(topic[2], 2)
                })
        
        cursor.close()
        conn.close()
        
        return jsonify({"recommendations": recommendations})
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
            # Get approved materials for topics where student has gaps
            cursor.execute("""
                SELECT m.material_id, m.title, m.content, m.source_citation,
                       m.generated_date, t.topic_name
                FROM material m
                JOIN topics t ON m.topic_id = t.topic_id
                WHERE m.approval_status = 'Approved'
                AND m.topic_id IN (
                    SELECT r.topic_id
                    FROM results r
                    WHERE r.student_id = %s
                    GROUP BY r.topic_id
                    HAVING AVG(r.score) < 70
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
        
        if password != user[4]:
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
@jwt_required(optional=True)
def admin_get_users():
    try:
        identity = get_jwt_identity()
        if identity and identity.get('role') != 'admin':
            return jsonify({"error": "Access denied"}), 403
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, full_name, email, role, created_at
            FROM users
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
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
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/users/<role>', methods=['GET'])
@jwt_required(optional=True)
def admin_get_users_by_role(role):
    try:
        identity = get_jwt_identity()
        if identity and identity.get('role') != 'admin':
            return jsonify({"error": "Access denied"}), 403
        if role not in ['student', 'teacher', 'family', 'admin']:
            return jsonify({"error": "Invalid role"}), 400
        
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
            users = cursor.fetchall()
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
            users = cursor.fetchall()
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
            users = cursor.fetchall()
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
            users = cursor.fetchall()
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
        return jsonify({"error": str(e)}), 500

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
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Email already registered"}), 400
        
        # Insert user
        cursor.execute(
            "INSERT INTO users (full_name, email, password, role, created_at) VALUES (%s, %s, %s, %s, NOW())",
            (full_name, email, password, role)
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
            cursor.execute(
                "UPDATE users SET full_name = %s, email = %s, password = %s, role = %s WHERE user_id = %s",
                (full_name, email, password, role, user_id)
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
@jwt_required(optional=True)
def admin_get_stats():
    try:
        identity = get_jwt_identity()
        if identity and identity.get('role') != 'admin':
            return jsonify({"error": "Access denied"}), 403
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get total users by role
        cursor.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
        role_counts = cursor.fetchall()
        users_by_role = {role: count for role, count in role_counts}
        
        # Get total quizzes
        cursor.execute("SELECT COUNT(*) FROM quizzes")
        total_quizzes = cursor.fetchone()[0]
        
        # Get total quiz attempts
        cursor.execute("SELECT COUNT(*) FROM quiz_attempt")
        total_attempts = cursor.fetchone()[0]
        
        # Get average score
        cursor.execute("SELECT AVG(score) FROM quiz_attempt")
        avg_score = cursor.fetchone()[0]
        avg_score = round(avg_score, 2) if avg_score else 0
        
        cursor.close()
        conn.close()
        
        return jsonify({
            "users_by_role": users_by_role,
            "total_quizzes": total_quizzes,
            "total_attempts": total_attempts,
            "average_score": avg_score
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    """Calculate average score for a student on a specific topic.
    Returns average score or None if no attempts."""
    cursor.execute("""
        SELECT AVG(qa.score * 100.0 / q.total_marks) as avg_pct
        FROM quiz_attempt qa
        JOIN quizzes q ON qa.quiz_id = q.quiz_id
        WHERE qa.student_id = %s AND q.topic_id = %s
    """, (student_id, topic_id))
    row = cursor.fetchone()
    if row and row[0] is not None:
        return round(row[0], 2)
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
        
        overview = []
        for topic in topics:
            topic_id = topic[0]
            
            # Get mastered count - students with >= 70% score
            mastered_count = 0
            attempted_count = 0
            try:
                cursor.execute("""
                    SELECT COUNT(DISTINCT qa.student_id)
                    FROM quiz_attempt qa
                    JOIN quizzes q ON qa.quiz_id = q.quiz_id
                    WHERE q.topic_id = %s
                    AND (qa.score * 100.0 / q.total_marks) >= 70
                """, (topic_id,))
                result = cursor.fetchone()
                mastered_count = result[0] if result else 0
            except Exception:
                pass
            
            try:
                cursor.execute("""
                    SELECT COUNT(DISTINCT qa.student_id)
                    FROM quiz_attempt qa
                    JOIN quizzes q ON qa.quiz_id = q.quiz_id
                    WHERE q.topic_id = %s
                """, (topic_id,))
                result = cursor.fetchone()
                attempted_count = result[0] if result else 0
            except Exception:
                pass
            
            mastery_pct = round((mastered_count / total_students) * 100, 1) if total_students > 0 else 0
            
            # Get struggling students
            struggling_students = []
            try:
                cursor.execute("""
                    SELECT u.user_id, u.full_name, AVG(qa.score * 100.0 / q.total_marks) as avg_pct
                    FROM quiz_attempt qa
                    JOIN quizzes q ON qa.quiz_id = q.quiz_id
                    JOIN users u ON qa.student_id = u.user_id
                    WHERE q.topic_id = %s
                    GROUP BY u.user_id, u.full_name
                    HAVING avg_pct < 70
                    ORDER BY avg_pct ASC
                """, (topic_id,))
                for s in cursor.fetchall() or []:
                    struggling_students.append({
                        'student_id': s[0],
                        'full_name': s[1],
                        'avg_score': round(s[2], 2)
                    })
            except Exception:
                pass
            
            # Get not started students
            not_started_students = []
            try:
                cursor.execute("""
                    SELECT u.user_id, u.full_name
                    FROM users u
                    WHERE u.role = 'student'
                    AND u.user_id NOT IN (
                        SELECT DISTINCT qa.student_id
                        FROM quiz_attempt qa
                        JOIN quizzes q ON qa.quiz_id = q.quiz_id
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

        heatmap = []
        for topic in topics:
            topic_id = topic[0]

            # Count students who mastered this topic (avg score >= 70%)
            mastered_count = 0
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT qa.student_id
                        FROM quiz_attempt qa
                        JOIN quizzes q ON qa.quiz_id = q.quiz_id
                        WHERE q.topic_id = %s
                        GROUP BY qa.student_id
                        HAVING AVG(qa.score * 100.0 / q.total_marks) >= 70
                    ) mastered
                """, (topic_id,))
                result = cursor.fetchone()
                mastered_count = result[0] if result else 0
            except Exception:
                pass

            # Count students who attempted but haven't mastered (avg < 70%)
            struggling_count = 0
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM (
                        SELECT qa.student_id
                        FROM quiz_attempt qa
                        JOIN quizzes q ON qa.quiz_id = q.quiz_id
                        WHERE q.topic_id = %s
                        GROUP BY qa.student_id
                        HAVING AVG(qa.score * 100.0 / q.total_marks) < 70
                    ) struggling
                """, (topic_id,))
                result = cursor.fetchone()
                struggling_count = result[0] if result else 0
            except Exception:
                pass

            # Count students who haven't attempted at all
            untouched_count = 0
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM users u
                    WHERE u.role = 'student'
                    AND u.user_id NOT IN (
                        SELECT DISTINCT qa.student_id
                        FROM quiz_attempt qa
                        JOIN quizzes q ON qa.quiz_id = q.quiz_id
                        WHERE q.topic_id = %s
                    )
                """, (topic_id,))
                result = cursor.fetchone()
                untouched_count = result[0] if result else 0
            except Exception:
                pass

            mastery_pct = round((mastered_count / total_students) * 100) if total_students > 0 else 0

            if mastery_pct >= 70:
                status = 'good'
            elif mastery_pct >= 40:
                status = 'needs_attention'
            else:
                status = 'critical'

            # Get struggling students with their scores
            struggling_students = []
            try:
                cursor.execute("""
                    SELECT u.user_id, u.full_name, AVG(qa.score * 100.0 / q.total_marks) as avg_pct
                    FROM quiz_attempt qa
                    JOIN quizzes q ON qa.quiz_id = q.quiz_id
                    JOIN users u ON qa.student_id = u.user_id
                    WHERE q.topic_id = %s
                    GROUP BY u.user_id, u.full_name
                    HAVING avg_pct < 70
                    ORDER BY avg_pct ASC
                """, (topic_id,))
                for s in cursor.fetchall() or []:
                    struggling_students.append({
                        'student_id': s[0],
                        'full_name': s[1],
                        'avg_score': round(s[2], 1)
                    })
            except Exception:
                pass

            heatmap.append({
                'topic_id': topic_id,
                'topic_name': topic[1],
                'grade_level': topic[2],
                'total_students': total_students,
                'mastered_count': mastered_count,
                'struggling_count': struggling_count,
                'untouched_count': untouched_count,
                'mastery_percentage': mastery_pct,
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

        # Get topics where student has gaps (avg score < 70%), ordered by weakness
        cursor.execute("""
            SELECT t.topic_id, t.topic_name, AVG(qa.score * 100.0 / q.total_marks) as avg_pct
            FROM quiz_attempt qa
            JOIN quizzes q ON qa.quiz_id = q.quiz_id
            JOIN topics t ON q.topic_id = t.topic_id
            WHERE qa.student_id = %s
            GROUP BY t.topic_id, t.topic_name
            HAVING avg_pct < 70
            ORDER BY avg_pct ASC
        """, (student_id,))
        gap_topics = cursor.fetchall()

        recommendations = []
        for topic in gap_topics:
            topic_id = topic[0]
            topic_name = topic[1]
            avg_score = round(topic[2], 1)

            if avg_score < 40:
                reason = f"You need to improve {topic_name}"
            else:
                reason = f"Practice more {topic_name} to reach mastery"

            # Find quizzes for this topic the student hasn't taken
            cursor.execute("""
                SELECT q.quiz_id, q.title, q.total_marks
                FROM quizzes q
                WHERE q.topic_id = %s
                AND q.quiz_id NOT IN (
                    SELECT qa.quiz_id
                    FROM quiz_attempt qa
                    WHERE qa.student_id = %s
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

        # If fewer than 5 gap-based recommendations, add quizzes for unstarted topics
        if len(recommendations) < 5:
            cursor.execute("""
                SELECT t.topic_id, t.topic_name
                FROM topics t
                WHERE t.topic_id NOT IN (
                    SELECT DISTINCT q.topic_id
                    FROM quiz_attempt qa
                    JOIN quizzes q ON qa.quiz_id = q.quiz_id
                    WHERE qa.student_id = %s
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
        
        cursor.execute("""
            SELECT m.material_id, m.title, m.content, m.source_citation,
                   m.generated_date, t.topic_name, m.topic_id
            FROM material m
            LEFT JOIN topics t ON m.topic_id = t.topic_id
            WHERE m.approval_status = 'Approved'
            ORDER BY m.generated_date DESC
        """)
        
        materials = cursor.fetchall() or []
        print(f"[DEBUG] Materials fetched: {len(materials)}")
        
        materials_list = []
        for material in materials:
            materials_list.append({
                'material_id': material[0],
                'title': material[1],
                'content': material[2],
                'source_citation': material[3],
                'generated_date': str(material[4]) if material[4] else '',
                'topic_name': material[5] if material[5] else '',
                'topic_id': material[6]
            })
        
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
        if request.method == 'POST':
            data = request.get_json() or {}
            query = data.get('query', '').strip()
        else:
            query = request.args.get('q', '').strip()

        if not query:
            return jsonify({"error": "Search query required"}), 400

        index_path = os.path.join('faiss_index', 'index.faiss')
        vectorizer_path = os.path.join('faiss_index', 'vectorizer.pkl')
        metadata_path = os.path.join('faiss_index', 'metadata.json')

        try:
            index = faiss.read_index(index_path)
            with open(vectorizer_path, 'rb') as f:
                vectorizer = pickle.load(f)
        except Exception:
            return jsonify({"error": "FAISS index or vectorizer could not be loaded"}), 500

        if not os.path.exists(metadata_path):
            return jsonify({"error": "Metadata file not found at faiss_index/metadata.json"}), 404

        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        query_vector = vectorizer.transform([query]).toarray().astype('float32')
        distances, indices = index.search(query_vector, 5)

        results = []
        for i, dist in zip(indices[0], distances[0]):
            if i < 0 or i >= len(metadata):
                continue
            chunk = metadata[i]
            similarity = max(0, (1 - float(dist)) * 100)
            results.append({
                'text': chunk['text'][:500],
                'source': chunk['source'],
                'page': chunk['page'],
                'similarity': int(similarity)
            })

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
    Part 3: Local RAG generation endpoint.
    Accepts topic_name, student_id, difficulty.
    Uses FAISS search + question_generator to create practice material,
    saves it to the material table with approval_status='pending'.
    """
    try:
        from question_generator import generate_questions
        from curriculum_extractor import extract_content

        data = request.get_json() or {}
        topic_name = data.get('topic_name', '').strip()
        student_id = data.get('student_id')
        difficulty = data.get('difficulty', 'medium')

        if not topic_name:
            return jsonify({"error": "topic_name is required"}), 400

        # ── Step 1: FAISS search for curriculum context ──────────────────────
        index_path = os.path.join('faiss_index', 'index.faiss')
        vectorizer_path = os.path.join('faiss_index', 'vectorizer.pkl')
        metadata_path = os.path.join('faiss_index', 'metadata.json')

        curriculum_chunks = []
        source_citation = f"Grade 12 Mathematics Curriculum - {topic_name}"

        try:
            index = faiss.read_index(index_path)
            with open(vectorizer_path, 'rb') as f:
                vectorizer = pickle.load(f)
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            query_vector = vectorizer.transform([topic_name]).toarray().astype('float32')
            distances, indices = index.search(query_vector, 3)

            for i in indices[0]:
                if 0 <= i < len(metadata):
                    chunk = metadata[i]
                    curriculum_chunks.append({
                        'text': chunk.get('text', ''),
                        'source': chunk.get('source', 'curriculum'),
                        'page': chunk.get('page', '')
                    })
        except Exception:
            pass  # FAISS unavailable – continue with questions only

        # ── Step 2: Extract curriculum content ──────────────────────────────
        extracted = extract_content(curriculum_chunks)
        if extracted['source_citation']:
            source_citation = extracted['source_citation']

        # ── Step 3: Generate questions ───────────────────────────────────────
        questions = generate_questions(topic_name, count=4, difficulty=difficulty)

        # ── Step 4: Build HTML content ───────────────────────────────────────
        html_parts = []

        # Curriculum explanation section
        if extracted['explanation']:
            html_parts.append(
                f'<div class="rag-explanation">'
                f'<h3>Curriculum Overview</h3>'
                f'<p>{extracted["explanation"]}</p>'
                f'</div>'
            )

        # Key formulas
        if extracted['formulas']:
            formulas_html = ''.join(f'<li><code>{f}</code></li>' for f in extracted['formulas'])
            html_parts.append(
                f'<div class="rag-formulas">'
                f'<h3>Key Formulas</h3>'
                f'<ul>{formulas_html}</ul>'
                f'</div>'
            )

        # Curriculum examples
        if extracted['examples']:
            examples_html = ''.join(f'<li>{e}</li>' for e in extracted['examples'])
            html_parts.append(
                f'<div class="rag-examples">'
                f'<h3>Curriculum Examples</h3>'
                f'<ul>{examples_html}</ul>'
                f'</div>'
            )

        # Practice questions
        questions_html = []
        for idx, q in enumerate(questions, 1):
            opts_html = ''.join(
                f'<li data-idx="{i}" class="rag-option">{chr(65+i)}. {opt}</li>'
                for i, opt in enumerate(q['options'])
            )
            questions_html.append(
                f'<div class="rag-question" data-correct="{q["correct_index"]}">'
                f'<p><strong>Q{idx}.</strong> {q["question"]}</p>'
                f'<ul class="rag-options">{opts_html}</ul>'
                f'<div class="rag-answer" style="display:none">'
                f'<strong>Answer: {q["correct_letter"]}</strong> — {q["explanation"]}'
                f'</div>'
                f'</div>'
            )

        html_parts.append(
            f'<div class="rag-questions">'
            f'<h3>Practice Questions</h3>'
            + ''.join(questions_html) +
            f'</div>'
        )

        content_html = '\n'.join(html_parts)

        # ── Step 5: Look up topic_id ─────────────────────────────────────────
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT topic_id FROM topics WHERE LOWER(topic_name) LIKE %s LIMIT 1",
            (f'%{topic_name.lower()}%',)
        )
        topic_row = cursor.fetchone()
        if not topic_row:
            # Fallback: use first topic
            cursor.execute("SELECT topic_id FROM topics LIMIT 1")
            topic_row = cursor.fetchone()

        if not topic_row:
            cursor.close()
            conn.close()
            return jsonify({"error": "No topics found in database"}), 500

        topic_id = topic_row[0]

        # ── Step 6: Save to material table ───────────────────────────────────
        cursor.execute("""
            INSERT INTO material (topic_id, title, content, source_citation,
                                  approval_status, generated_date)
            VALUES (%s, %s, %s, %s, 'Pending', NOW())
        """, (topic_id, f"Practice: {topic_name}", content_html, source_citation))

        material_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "material_id": material_id,
            "title": f"Practice: {topic_name}",
            "source_citation": source_citation,
            "questions_count": len(questions),
            "preview": content_html[:500],
            "message": "Material generated and sent for teacher approval"
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

if __name__ == '__main__':
    app.run(debug=True)