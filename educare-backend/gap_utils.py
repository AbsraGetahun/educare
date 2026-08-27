"""
Learning gap detection from quiz_attempt data (source of truth for scores).
Handles both students.student_id and legacy rows where quiz_attempt.student_id = user_id.
"""

# Fixed JOIN: Use students table to map quiz_attempt.student_id to users.user_id
# If quiz_attempt.student_id is actually the user_id, we need to handle both cases
QUIZ_STUDENT_JOIN = """
    JOIN students s_qa ON s_qa.student_id = qa.student_id
"""

def weakness_level_from_avg(avg_pct):
    if avg_pct is None:
        return 'Low'
    if avg_pct < 40:
        return 'High'
    if avg_pct < 70:
        return 'Moderate'
    return 'Low'

def fetch_student_gaps(cursor, user_id):
    """
    Topics where the student averages below 70% across quiz attempts.
    user_id: users.user_id (what the API routes pass).
    """
    cursor.execute(
        f"""
        SELECT t.topic_id, t.topic_name,
               AVG(qa.score * 100.0 / NULLIF(q.total_marks, 0)) AS avg_pct
        FROM quiz_attempt qa
        JOIN quizzes q ON qa.quiz_id = q.quiz_id
        JOIN topics t ON q.topic_id = t.topic_id
        JOIN students s_qa ON s_qa.student_id = qa.student_id
        WHERE s_qa.user_id = %s
        GROUP BY t.topic_id, t.topic_name
        HAVING avg_pct IS NOT NULL AND avg_pct < 70
        ORDER BY avg_pct ASC
        """,
        (user_id,),
    )
    gaps = []
    for row in cursor.fetchall() or []:
        avg_pct = float(row[2])
        gaps.append({
            'topic_id': row[0],
            'topic_name': row[1],
            'avg_score': round(avg_pct, 2),
            'weakness_level': weakness_level_from_avg(avg_pct),
        })
    return gaps

def _grade_filter_clause(grade_level, alias='s_qa'):
    if grade_level is None:
        return '', []
    return (
        f" AND {alias}.user_id IN (SELECT user_id FROM students WHERE grade_level = %s)",
        [grade_level],
    )

def fetch_struggling_students_for_topic(cursor, topic_id, grade_level=None):
    """Students below 70% mastery on a topic; returns user_id as student_id."""
    grade_clause, grade_params = _grade_filter_clause(grade_level)
    cursor.execute(
        f"""
        SELECT u.user_id, u.full_name,
               AVG(qa.score * 100.0 / NULLIF(q.total_marks, 0)) AS avg_pct
        FROM quiz_attempt qa
        JOIN quizzes q ON qa.quiz_id = q.quiz_id
        JOIN students s_qa ON s_qa.student_id = qa.student_id
        JOIN users u ON s_qa.user_id = u.user_id
        WHERE q.topic_id = %s{grade_clause}
        GROUP BY u.user_id, u.full_name
        HAVING avg_pct IS NOT NULL AND avg_pct < 70
        ORDER BY avg_pct ASC
        """,
        (topic_id, *grade_params),
    )
    return [
        {
            'student_id': row[0],
            'full_name': row[1],
            'avg_score': round(float(row[2]), 1),
        }
        for row in cursor.fetchall() or []
    ]

def count_students_mastered_topic(cursor, topic_id, grade_level=None):
    grade_clause, grade_params = _grade_filter_clause(grade_level)
    cursor.execute(
        f"""
        SELECT COUNT(*) FROM (
            SELECT s_qa.user_id
            FROM quiz_attempt qa
            JOIN quizzes q ON qa.quiz_id = q.quiz_id
            JOIN students s_qa ON s_qa.student_id = qa.student_id
            WHERE q.topic_id = %s{grade_clause}
            GROUP BY s_qa.user_id
            HAVING AVG(qa.score * 100.0 / NULLIF(q.total_marks, 0)) >= 70
        ) mastered
        """,
        (topic_id, *grade_params),
    )
    row = cursor.fetchone()
    return row[0] if row else 0

def count_students_struggling_topic(cursor, topic_id, grade_level=None):
    grade_clause, grade_params = _grade_filter_clause(grade_level)
    cursor.execute(
        f"""
        SELECT COUNT(*) FROM (
            SELECT s_qa.user_id
            FROM quiz_attempt qa
            JOIN quizzes q ON qa.quiz_id = q.quiz_id
            JOIN students s_qa ON s_qa.student_id = qa.student_id
            WHERE q.topic_id = %s{grade_clause}
            GROUP BY s_qa.user_id
            HAVING AVG(qa.score * 100.0 / NULLIF(q.total_marks, 0)) < 70
        ) struggling
        """,
        (topic_id, *grade_params),
    )
    row = cursor.fetchone()
    return row[0] if row else 0

def count_students_untouched_topic(cursor, topic_id, grade_level=None):
    if grade_level is not None:
        cursor.execute(
            f"""
            SELECT COUNT(*) FROM users u
            JOIN students s ON u.user_id = s.user_id
            WHERE u.role = 'student' AND s.grade_level = %s
            AND u.user_id NOT IN (
                SELECT DISTINCT s_qa.user_id
                FROM quiz_attempt qa
                JOIN quizzes q ON qa.quiz_id = q.quiz_id
                JOIN students s_qa ON s_qa.student_id = qa.student_id
                WHERE q.topic_id = %s
            )
            """,
            (grade_level, topic_id),
        )
    else:
        cursor.execute(
            f"""
            SELECT COUNT(*) FROM users u
            WHERE u.role = 'student'
            AND u.user_id NOT IN (
                SELECT DISTINCT s_qa.user_id
                FROM quiz_attempt qa
                JOIN quizzes q ON qa.quiz_id = q.quiz_id
                JOIN students s_qa ON s_qa.student_id = qa.student_id
                WHERE q.topic_id = %s
            )
            """,
            (topic_id,),
        )
    row = cursor.fetchone()
    return row[0] if row else 0