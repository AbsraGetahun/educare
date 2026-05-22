"""
Learning gap detection from quiz_attempt data (source of truth for scores).
Handles both students.student_id and legacy rows where quiz_attempt.student_id = user_id.
"""

# Join quiz_attempt rows to the canonical user_id on students
QUIZ_STUDENT_JOIN = """
    JOIN students s_qa ON (qa.student_id = s_qa.student_id OR qa.student_id = s_qa.user_id)
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
        {QUIZ_STUDENT_JOIN}
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


def fetch_struggling_students_for_topic(cursor, topic_id):
    """Students below 70% mastery on a topic; returns user_id as student_id."""
    cursor.execute(
        f"""
        SELECT u.user_id, u.full_name,
               AVG(qa.score * 100.0 / NULLIF(q.total_marks, 0)) AS avg_pct
        FROM quiz_attempt qa
        JOIN quizzes q ON qa.quiz_id = q.quiz_id
        {QUIZ_STUDENT_JOIN}
        JOIN users u ON s_qa.user_id = u.user_id
        WHERE q.topic_id = %s
        GROUP BY u.user_id, u.full_name
        HAVING avg_pct IS NOT NULL AND avg_pct < 70
        ORDER BY avg_pct ASC
        """,
        (topic_id,),
    )
    return [
        {
            'student_id': row[0],
            'full_name': row[1],
            'avg_score': round(float(row[2]), 1),
        }
        for row in cursor.fetchall() or []
    ]


def count_students_mastered_topic(cursor, topic_id):
    cursor.execute(
        f"""
        SELECT COUNT(*) FROM (
            SELECT s_qa.user_id
            FROM quiz_attempt qa
            JOIN quizzes q ON qa.quiz_id = q.quiz_id
            {QUIZ_STUDENT_JOIN}
            WHERE q.topic_id = %s
            GROUP BY s_qa.user_id
            HAVING AVG(qa.score * 100.0 / NULLIF(q.total_marks, 0)) >= 70
        ) mastered
        """,
        (topic_id,),
    )
    row = cursor.fetchone()
    return row[0] if row else 0


def count_students_struggling_topic(cursor, topic_id):
    cursor.execute(
        f"""
        SELECT COUNT(*) FROM (
            SELECT s_qa.user_id
            FROM quiz_attempt qa
            JOIN quizzes q ON qa.quiz_id = q.quiz_id
            {QUIZ_STUDENT_JOIN}
            WHERE q.topic_id = %s
            GROUP BY s_qa.user_id
            HAVING AVG(qa.score * 100.0 / NULLIF(q.total_marks, 0)) < 70
        ) struggling
        """,
        (topic_id,),
    )
    row = cursor.fetchone()
    return row[0] if row else 0


def count_students_untouched_topic(cursor, topic_id):
    cursor.execute(
        f"""
        SELECT COUNT(*) FROM users u
        WHERE u.role = 'student'
        AND u.user_id NOT IN (
            SELECT DISTINCT s_qa.user_id
            FROM quiz_attempt qa
            JOIN quizzes q ON qa.quiz_id = q.quiz_id
            {QUIZ_STUDENT_JOIN}
            WHERE q.topic_id = %s
        )
        """,
        (topic_id,),
    )
    row = cursor.fetchone()
    return row[0] if row else 0
