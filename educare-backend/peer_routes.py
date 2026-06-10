"""
Peer-to-peer math questions between students.
- Posted questions are visible to ALL students (broadcast feed).
- Answers are stored privately and returned ONLY to the student who asked.
"""
from flask import jsonify, request


def _init_peer_tables(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS peer_attachments (
            attachment_id   INT AUTO_INCREMENT PRIMARY KEY,
            parent_type     ENUM('question', 'answer') NOT NULL,
            parent_id       INT NOT NULL,
            file_url        VARCHAR(512) NOT NULL,
            file_name       VARCHAR(255) NOT NULL,
            content_type    VARCHAR(128) DEFAULT '',
            is_image        TINYINT(1) DEFAULT 0,
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_peer_att_parent (parent_type, parent_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS peer_questions (
            question_id   INT AUTO_INCREMENT PRIMARY KEY,
            asker_user_id INT NOT NULL,
            question_text TEXT NOT NULL,
            status        ENUM('open', 'closed') DEFAULT 'open',
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (asker_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            INDEX idx_peer_q_created (created_at DESC),
            INDEX idx_peer_q_asker (asker_user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS peer_answers (
            answer_id         INT AUTO_INCREMENT PRIMARY KEY,
            question_id       INT NOT NULL,
            responder_user_id INT NOT NULL,
            answer_text       TEXT NOT NULL,
            created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES peer_questions(question_id) ON DELETE CASCADE,
            FOREIGN KEY (responder_user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            UNIQUE KEY uniq_peer_answer (question_id, responder_user_id),
            INDEX idx_peer_a_question (question_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)


def _parse_student_id(data):
    raw = data.get('student_id') if data else None
    if raw is None:
        return None, 'student_id required'
    try:
        return int(raw), None
    except (TypeError, ValueError):
        return None, 'student_id must be a number'


def _ensure_student(cursor, user_id):
    cursor.execute(
        "SELECT user_id, full_name FROM users WHERE user_id = %s AND role = 'student'",
        (user_id,),
    )
    row = cursor.fetchone()
    return row


def _normalize_attachments(raw):
    """Validate attachment dicts from client [{url, file_name, content_type, is_image}]."""
    if not raw or not isinstance(raw, list):
        return []
    out = []
    for item in raw[:8]:
        if not isinstance(item, dict):
            continue
        url = (item.get('url') or '').strip()
        if not url.startswith('/uploads/peer/'):
            continue
        out.append({
            'url': url,
            'file_name': (item.get('file_name') or 'file')[:255],
            'content_type': (item.get('content_type') or '')[:128],
            'is_image': 1 if item.get('is_image') else 0,
        })
    return out


def _save_attachments(cursor, parent_type, parent_id, attachments):
    for att in attachments:
        cursor.execute(
            """
            INSERT INTO peer_attachments
                (parent_type, parent_id, file_url, file_name, content_type, is_image)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                parent_type, parent_id, att['url'], att['file_name'],
                att['content_type'], att['is_image'],
            ),
        )


def _fetch_attachments(cursor, parent_type, parent_id):
    cursor.execute(
        """
        SELECT file_url, file_name, content_type, is_image
        FROM peer_attachments
        WHERE parent_type = %s AND parent_id = %s
        ORDER BY attachment_id ASC
        """,
        (parent_type, parent_id),
    )
    return [
        {
            'url': r[0],
            'file_name': r[1],
            'content_type': r[2],
            'is_image': bool(r[3]),
        }
        for r in cursor.fetchall()
    ]


def register_routes(app, get_db_connection):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        _init_peer_tables(cur)
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass

    @app.route('/api/peer/questions', methods=['POST'])
    def peer_post_question():
        """Student posts a math question — broadcast to all students via the feed."""
        data = request.get_json() or {}
        student_id, err = _parse_student_id(data)
        if err:
            return jsonify({'error': err}), 400

        question_text = (data.get('question_text') or '').strip()
        attachments = _normalize_attachments(data.get('attachments'))
        if len(question_text) < 5 and not attachments:
            return jsonify({'error': 'Add a question (5+ characters) or attach a file/image'}), 400
        if len(question_text) > 2000:
            return jsonify({'error': 'Question is too long (max 2000 characters)'}), 400

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            student = _ensure_student(cursor, student_id)
            if not student:
                cursor.close()
                conn.close()
                return jsonify({'error': 'Student not found'}), 404

            cursor.execute(
                """
                INSERT INTO peer_questions (asker_user_id, question_text)
                VALUES (%s, %s)
                """,
                (student_id, question_text or '(see attached file)'),
            )
            question_id = cursor.lastrowid
            if attachments:
                _save_attachments(cursor, 'question', question_id, attachments)
            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({
                'question_id': question_id,
                'message': 'Your question has been posted for all students to see.',
            }), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/peer/questions', methods=['GET'])
    def peer_list_questions():
        """
        Public feed: all open questions for every student.
        Does NOT include any answer text or answer metadata (private to asker).
        """
        student_id = request.args.get('student_id')
        try:
            viewer_id = int(student_id) if student_id else None
        except (TypeError, ValueError):
            return jsonify({'error': 'student_id required'}), 400

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if not _ensure_student(cursor, viewer_id):
                cursor.close()
                conn.close()
                return jsonify({'error': 'Student not found'}), 404

            cursor.execute(
                """
                SELECT pq.question_id, pq.question_text, pq.created_at,
                       pq.asker_user_id, u.full_name AS asker_name,
                       (pq.asker_user_id = %s) AS is_mine,
                       EXISTS (
                           SELECT 1 FROM peer_answers pa
                           WHERE pa.question_id = pq.question_id
                             AND pa.responder_user_id = %s
                       ) AS i_answered
                FROM peer_questions pq
                JOIN users u ON u.user_id = pq.asker_user_id
                WHERE pq.status = 'open'
                ORDER BY pq.created_at DESC
                LIMIT 100
                """,
                (viewer_id, viewer_id),
            )
            rows = cursor.fetchall()
            questions = []
            for row in rows:
                qid = row[0]
                questions.append({
                    'question_id': qid,
                    'question_text': row[1],
                    'created_at': row[2].isoformat() if row[2] else None,
                    'asker_user_id': row[3],
                    'asker_name': row[4],
                    'is_mine': bool(row[5]),
                    'i_answered': bool(row[6]),
                    'attachments': _fetch_attachments(cursor, 'question', qid),
                })
            cursor.close()
            conn.close()
            return jsonify({'questions': questions})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/peer/my-questions', methods=['GET'])
    def peer_my_questions():
        """Questions asked by this student, including private answers (asker only)."""
        student_id = request.args.get('student_id')
        try:
            asker_id = int(student_id)
        except (TypeError, ValueError):
            return jsonify({'error': 'student_id required'}), 400

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if not _ensure_student(cursor, asker_id):
                cursor.close()
                conn.close()
                return jsonify({'error': 'Student not found'}), 404

            cursor.execute(
                """
                SELECT question_id, question_text, status, created_at
                FROM peer_questions
                WHERE asker_user_id = %s
                ORDER BY created_at DESC
                LIMIT 50
                """,
                (asker_id,),
            )
            q_rows = cursor.fetchall()
            result = []
            for qid, qtext, status, created in q_rows:
                cursor.execute(
                    """
                    SELECT pa.answer_id, pa.answer_text, pa.created_at, u.full_name
                    FROM peer_answers pa
                    JOIN users u ON u.user_id = pa.responder_user_id
                    WHERE pa.question_id = %s
                    ORDER BY pa.created_at ASC
                    """,
                    (qid,),
                )
                answers = []
                for a in cursor.fetchall():
                    answers.append({
                        'answer_text': a[1],
                        'created_at': a[2].isoformat() if a[2] else None,
                        'responder_name': a[3],
                        'attachments': _fetch_attachments(cursor, 'answer', a[0]),
                    })
                result.append({
                    'question_id': qid,
                    'question_text': qtext,
                    'status': status,
                    'created_at': created.isoformat() if created else None,
                    'answer_count': len(answers),
                    'answers': answers,
                    'attachments': _fetch_attachments(cursor, 'question', qid),
                })

            cursor.close()
            conn.close()
            return jsonify({'questions': result})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/peer/questions/<int:question_id>/answers', methods=['POST'])
    def peer_post_answer(question_id):
        """
        Any student (except the asker) may answer.
        Answer is NOT returned on the public feed — only stored for the asker.
        """
        data = request.get_json() or {}
        student_id, err = _parse_student_id(data)
        if err:
            return jsonify({'error': err}), 400

        answer_text = (data.get('answer_text') or '').strip()
        attachments = _normalize_attachments(data.get('attachments'))
        if len(answer_text) < 3 and not attachments:
            return jsonify({'error': 'Add an answer (3+ characters) or attach a file/image'}), 400
        if len(answer_text) > 3000:
            return jsonify({'error': 'Answer is too long (max 3000 characters)'}), 400

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            if not _ensure_student(cursor, student_id):
                cursor.close()
                conn.close()
                return jsonify({'error': 'Student not found'}), 404

            cursor.execute(
                """
                SELECT asker_user_id, question_text, status
                FROM peer_questions WHERE question_id = %s
                """,
                (question_id,),
            )
            q_row = cursor.fetchone()
            if not q_row:
                cursor.close()
                conn.close()
                return jsonify({'error': 'Question not found'}), 404

            asker_id, q_text, status = q_row
            if status != 'open':
                cursor.close()
                conn.close()
                return jsonify({'error': 'This question is closed'}), 400
            if asker_id == student_id:
                cursor.close()
                conn.close()
                return jsonify({'error': 'You cannot answer your own question'}), 400

            cursor.execute(
                """
                INSERT INTO peer_answers (question_id, responder_user_id, answer_text)
                VALUES (%s, %s, %s)
                """,
                (question_id, student_id, answer_text or '(see attached file)'),
            )
            answer_id = cursor.lastrowid
            if attachments:
                _save_attachments(cursor, 'answer', answer_id, attachments)
            conn.commit()
            cursor.close()
            conn.close()

            return jsonify({
                'message': (
                    'Your answer was sent privately to the student who asked. '
                    'Other students cannot see it.'
                ),
                'question_id': question_id,
            }), 201
        except Exception as e:
            err = str(e)
            if 'uniq_peer_answer' in err or 'Duplicate' in err:
                return jsonify({'error': 'You already answered this question'}), 409
            return jsonify({'error': err}), 500
