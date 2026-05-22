"""
Material generation, assistant, quiz AI, analytics — register on Flask app via register_routes(app).
All RAG operations now use ALL 6 textbooks with Extreme Mathematics priority.
"""
from flask import jsonify, request
import rag_service as rag


def register_routes(app, get_db_connection):
    from question_generator import generate_questions
    from curriculum_extractor import extract_content

    def _resolve_topic_id(cursor, topic_name):
        cursor.execute(
            "SELECT topic_id FROM topics WHERE LOWER(topic_name) LIKE %s LIMIT 1",
            (f'%{topic_name.lower()}%',),
        )
        row = cursor.fetchone()
        if row:
            return row[0]
        cursor.execute("SELECT topic_id FROM topics LIMIT 1")
        row = cursor.fetchone()
        return row[0] if row else None

    def _student_grade(cursor, student_user_id):
        cursor.execute(
            "SELECT grade_level FROM students WHERE user_id = %s",
            (student_user_id,),
        )
        row = cursor.fetchone()
        return int(row[0]) if row and row[0] else None

    def _dedup_recent(cursor, student_id, topic_name, days=7):
        try:
            cursor.execute(
                """
                SELECT history_id FROM generation_history
                WHERE student_id = %s AND LOWER(topic_name) = LOWER(%s)
                  AND generated_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                LIMIT 1
                """,
                (student_id, topic_name, days),
            )
            return cursor.fetchone() is not None
        except Exception:
            return False

    def _insert_material(cursor, topic_id, title, content_html, cite, teacher_id=None):
        base_cols = ['topic_id', 'title', 'content', 'source_citation', 'approval_status']
        base_vals = [topic_id, title, content_html, cite['source_citation'], 'Pending']
        extra_cols = []
        extra_vals = []
        for col, key in [
            ('source_file', 'source_file'),
            ('source_page', 'source_page'),
            ('source_grade', 'source_grade'),
            ('section_title', 'section'),
        ]:
            try:
                cursor.execute("SHOW COLUMNS FROM material LIKE %s", (col,))
                if cursor.fetchone():
                    extra_cols.append(col)
                    extra_vals.append(cite.get(key))
            except Exception:
                pass
        if teacher_id is not None:
            try:
                cursor.execute("SHOW COLUMNS FROM material LIKE %s", ('teacher_id',))
                if cursor.fetchone():
                    extra_cols.append('teacher_id')
                    extra_vals.append(teacher_id)
            except Exception:
                pass
        all_cols = base_cols + extra_cols + ['generated_date']
        all_vals = base_vals + extra_vals
        sql = (
            f"INSERT INTO material ({', '.join(all_cols)}) "
            f"VALUES ({', '.join(['%s'] * len(all_vals))}, NOW())"
        )
        cursor.execute(sql, all_vals)
        return cursor.lastrowid

    def _record_generation(cursor, teacher_id, student_id, topic_name, grade_level, difficulty):
        try:
            cursor.execute(
                """
                INSERT INTO generation_history (teacher_id, student_id, topic_name, grade_level, difficulty)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (teacher_id or 1, student_id, topic_name, grade_level, difficulty),
            )
        except Exception:
            pass

    def _generate_material_core(topic_name, grade_level, difficulty, num_questions=4):
        """
        Core RAG material generation using ALL 6 textbooks with Extreme Mathematics priority.
        """
        multi_hits = rag.search_all_books(topic_name, grade_level, k_per_phase=5)
        standard_hits = rag.search_curriculum(topic_name, grade_level, k=5)
        all_hit_keys = set()
        merged_hits = []
        for h in multi_hits + standard_hits:
            key = ((h.get('source_file') or h.get('source') or '').lower(),
                   str(h.get('page') or ''))
            if key not in all_hit_keys:
                all_hit_keys.add(key)
                merged_hits.append(h)

        chunks = [
            {'text': h.get('text', ''), 'source': h.get('source', ''), 'page': h.get('page', '')}
            for h in merged_hits
        ]
        extracted = extract_content(chunks)

        cite = rag.build_citation_from_hits(merged_hits, topic_name)
        if extracted.get('source_citation'):
            cite['source_citation'] = extracted['source_citation']
        if extracted.get('book_name'):
            cite['source_file'] = extracted.get('source_file', cite.get('source_file', ''))
            cite['source_grade'] = extracted.get('source_grade', cite.get('source_grade'))
        if extracted.get('source_page'):
            cite['source_page'] = extracted.get('source_page')

        source_files = [h.get('source_file') or h.get('source', '') for h in merged_hits]
        source_pages = [h.get('source_page') or h.get('page', '') for h in merged_hits]

        questions = generate_questions(
            topic_name, count=num_questions, difficulty=difficulty,
            source_files=source_files, source_pages=source_pages,
        )

        html = rag.build_material_html(extracted, questions)
        return html, cite, questions, merged_hits

    @app.route('/api/curriculum/search-by-topic', methods=['POST'])
    def search_curriculum_by_topic():
        data = request.get_json() or {}
        topic_name = (data.get('topic_name') or '').strip()
        grade_level = data.get('grade_level')
        if grade_level is not None:
            grade_level = int(grade_level)
        if not topic_name:
            return jsonify({'error': 'topic_name is required'}), 400
        results = rag.search_curriculum(topic_name, grade_level, k=5)
        return jsonify({'results': results})

    @app.route('/api/curriculum/topics', methods=['GET'])
    def curriculum_topics():
        prefix = (request.args.get('prefix') or '').strip()
        topics = rag.list_curriculum_topics(prefix, limit=25)
        return jsonify({'topics': topics})

    @app.route('/api/materials/generate-by-topic', methods=['POST'])
    def generate_material_by_topic():
        data = request.get_json() or {}
        topic_name = (data.get('topic_name') or '').strip()
        grade_level = int(data.get('grade_level', 10))
        difficulty = data.get('difficulty', 'medium')
        teacher_id = data.get('teacher_id', 1)
        if not topic_name:
            return jsonify({'error': 'topic_name is required'}), 400
        try:
            html, cite, questions, _ = _generate_material_core(
                topic_name, grade_level, difficulty, num_questions=7
            )
            conn = get_db_connection()
            cursor = conn.cursor()
            topic_id = _resolve_topic_id(cursor, topic_name)
            if not topic_id:
                cursor.close(); conn.close()
                return jsonify({'error': 'No topics in database'}), 500
            material_id = _insert_material(
                cursor, topic_id, f'Practice: {topic_name}', html, cite, teacher_id
            )
            conn.commit(); cursor.close(); conn.close()
            return jsonify({
                'material_id': material_id,
                'title': f'Practice: {topic_name}',
                'topic_name': topic_name,
                'grade_level': grade_level, 'difficulty': difficulty,
                'source_citation': cite['source_citation'],
                'source_file': cite.get('source_file'),
                'source_page': cite.get('source_page'),
                'questions_count': len(questions),
                'message': 'Material generated and sent for teacher approval',
            }), 201
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/materials/generate-batch', methods=['POST'])
    def generate_batch_materials():
        data = request.get_json() or {}
        grade_level = int(data.get('grade_level', 10))
        difficulty = data.get('difficulty', 'medium')
        teacher_id = data.get('teacher_id', 1)
        generated = failed = 0
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT u.user_id FROM users u "
                "JOIN students s ON u.user_id = s.user_id WHERE s.grade_level = %s",
                (grade_level,),
            )
            students = cursor.fetchall() or []
            from gap_utils import fetch_student_gaps
            for (user_id,) in students:
                gaps = fetch_student_gaps(cursor, user_id)
                for gap in gaps:
                    topic_name, topic_id = gap['topic_name'], gap['topic_id']
                    if _dedup_recent(cursor, user_id, topic_name):
                        continue
                    try:
                        html, cite, questions, _ = _generate_material_core(
                            topic_name, grade_level, difficulty, num_questions=3
                        )
                        _insert_material(
                            cursor, topic_id, f'Practice: {topic_name}', html, cite, teacher_id
                        )
                        _record_generation(cursor, teacher_id, user_id, topic_name, grade_level, difficulty)
                        generated += 1
                    except Exception:
                        failed += 1
            conn.commit(); cursor.close(); conn.close()
            return jsonify({'generated': generated, 'failed': failed,
                            'total_students': len(students),
                            'message': 'Batch generation complete'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/materials/analytics', methods=['GET'])
    def materials_analytics():
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            stats = {'total_materials':0,'approved':0,'pending':0,'rejected':0,
                     'total_helpful':0,'total_not_helpful':0}
            cursor.execute("SELECT approval_status, COUNT(*) FROM material GROUP BY approval_status")
            for status, cnt in cursor.fetchall() or []:
                stats['total_materials'] += cnt
                k = (status or '').lower()
                if k == 'approved':  stats['approved'] = cnt
                elif k == 'pending': stats['pending'] = cnt
                elif k == 'rejected':stats['rejected'] = cnt
            try:
                cursor.execute("SELECT COALESCE(SUM(helpful_count),0), COALESCE(SUM(not_helpful_count),0) FROM material")
                row = cursor.fetchone()
                if row: stats['total_helpful'] = int(row[0]); stats['total_not_helpful'] = int(row[1])
            except Exception: pass
            try:
                cursor.execute("SELECT topic_name, COUNT(*) as cnt FROM generation_history GROUP BY topic_name ORDER BY cnt DESC LIMIT 10")
                top = [{'topic':r[0],'count':r[1]} for r in cursor.fetchall() or []]
            except Exception:
                cursor.execute("SELECT t.topic_name,COUNT(*) FROM material m JOIN topics t ON m.topic_id=t.topic_id GROUP BY t.topic_name ORDER BY COUNT(*) DESC LIMIT 10")
                top = [{'topic':r[0],'count':r[1]} for r in cursor.fetchall() or []]
            from gap_utils import QUIZ_STUDENT_JOIN
            cursor.execute(
                f"SELECT t.topic_id,t.topic_name,t.grade_level,AVG(qa.score*100.0/NULLIF(q.total_marks,0)),COUNT(DISTINCT s_qa.user_id) "
                f"FROM quiz_attempt qa JOIN quizzes q ON qa.quiz_id=q.quiz_id "
                f"JOIN topics t ON q.topic_id=t.topic_id {QUIZ_STUDENT_JOIN} "
                f"GROUP BY t.topic_id,t.topic_name,t.grade_level HAVING AVG IS NOT NULL AND AVG<70 ORDER BY AVG ASC LIMIT 15"
            )
            strug = [{'topic_id':r[0],'topic_name':r[1],'grade_level':r[2],'avg_score':float(r[3]) if r[3] else 0,'num_students':r[4]}
                     for r in cursor.fetchall() or []]
            ai = 0
            try:
                cursor.execute("SELECT COUNT(*) FROM quiz_ai_generations")
                r = cursor.fetchone(); ai = r[0] if r else 0
            except Exception: pass
            cursor.close(); conn.close()
            return jsonify({'approval_stats':stats,'top_topics':top,'struggling_topics':strug,'ai_quizzes_generated':ai})
        except Exception as e:
            return jsonify({'error':str(e)}),500

    @app.route('/api/materials/<int:material_id>/rate', methods=['POST'])
    def rate_material(material_id):
        data = request.get_json() or {}
        student_id, rating = data.get('student_id'), data.get('rating')
        if not student_id or rating not in ('helpful','not_helpful'):
            return jsonify({'error':'student_id and rating required'}), 400
        try:
            conn = get_db_connection(); cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO material_ratings (material_id, student_id, rating) "
                "VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE rating=VALUES(rating),created_at=NOW()",
                (material_id, student_id, rating))
            col = 'helpful_count' if rating=='helpful' else 'not_helpful_count'
            cursor.execute(f"UPDATE material SET {col}={col}+1 WHERE material_id=%s",(material_id,))
            conn.commit(); cursor.close(); conn.close()
            return jsonify({'message':'Rating saved'})
        except Exception as e:
            return jsonify({'error':str(e)}),500

    @app.route('/api/quiz/generate-ai', methods=['POST'])
    def generate_ai_quiz():
        data = request.get_json() or {}
        topic = (data.get('topic') or '').strip()
        grade_level = int(data.get('grade_level', 10))
        num_questions = min(max(int(data.get('num_questions', 5)), 5), 10)
        difficulty = data.get('difficulty', 'medium')
        if not topic:
            return jsonify({'error': 'topic is required'}), 400
        try:
            rag.search_all_books(topic, grade_level, k_per_phase=3)
            questions = generate_questions(topic, count=num_questions, difficulty=difficulty)
            conn = get_db_connection(); cursor = conn.cursor()
            topic_id = _resolve_topic_id(cursor, topic)
            if not topic_id: cursor.close(); conn.close()
            title = f'AI Quiz: {topic} (Grade {grade_level})'
            cursor.execute("INSERT INTO quizzes (topic_id, title, total_marks, time_limit, created_at) VALUES (%s,%s,%s,%s,NOW())",
                           (topic_id, title, len(questions), 30))
            quiz_id = cursor.lastrowid
            for q in questions:
                opts = q.get('options', ['','','',''])
                cursor.execute(
                    "INSERT INTO quiz_questions (quiz_id, question_text, option_a, option_b, option_c, option_d, correct_answer) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s)",
                    (quiz_id, q.get('question',''),
                     opts[0] if len(opts)>0 else '',
                     opts[1] if len(opts)>1 else '',
                     opts[2] if len(opts)>2 else '',
                     opts[3] if len(opts)>3 else '',
                     q.get('correct_letter','A'))
                )
            try:
                cursor.execute(
                    "INSERT INTO quiz_ai_generations (quiz_id,topic,grade_level,num_questions,difficulty) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (quiz_id, topic, grade_level, len(questions), difficulty))
            except Exception: pass
            conn.commit(); cursor.close(); conn.close()
            return jsonify({'quiz_id':quiz_id,'title':title,'num_questions':len(questions),
                            'topic':topic,'grade_level':grade_level}), 201
        except Exception as e:
            return jsonify({'error':str(e)}),500

    @app.route('/api/assistant/ask', methods=['POST'])
    def assistant_ask():
        """
        Full conversational math assistant with greeting support, scope check,
        textbook search across all 6 books, and step-by-step explanations.
        """
        data = request.get_json() or {}
        question = (data.get('question') or '').strip()
        student_id = data.get('student_id')
        if not question or not student_id:
            return jsonify({'error': 'question and student_id required'}), 400

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            grade = _student_grade(cursor, student_id)
            cursor.close()
            conn.close()

            # ── Use new math answer engine ────────────────────────────────────────
            result = rag.generate_math_answer(question, grade_level=grade)

            # ── Store conversation in DB ─────────────────────────────────────────
            try:
                conn2 = get_db_connection()
                cursor2 = conn2.cursor()
                cursor2.execute(
                    """
                    INSERT INTO assistant_conversations
                        (student_id, user_message, ai_response, source_citation)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (student_id, question,
                     result['answer'],
                     result.get('source_citation', '')),
                )
                conn2.commit()
                cursor2.close()
                conn2.close()
            except Exception:
                pass

            return jsonify({
                'answer':         result['answer'],
                'source_citation': result.get('source_citation', ''),
                'source_file':    result.get('source_file', ''),
                'source_page':    result.get('source_page', ''),
                'source_grade':   result.get('source_grade'),
                'section':        result.get('section', ''),
                'confidence':     result.get('confidence', 'medium'),
                'topic':          result.get('topic', ''),
                'is_greeting':    result.get('topic') == 'greeting',
                'is_welcome':     result.get('topic') == 'greeting' and not question,
            })
        except Exception as e:
            return jsonify({'error': str(e), 'answer': 'Something went wrong. Please try again.'}), 500

    @app.route('/api/assistant/history/<int:student_id>', methods=['GET'])
    def assistant_history(student_id):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT user_message, ai_response, source_citation, created_at
                FROM assistant_conversations
                WHERE student_id = %s
                ORDER BY created_at ASC LIMIT 200
                """,
                (student_id,),
            )
            rows = cursor.fetchall() or []
            cursor.close()
            conn.close()
            history = []
            for row in rows:
                history.append({
                    'user_message':    row[0],
                    'ai_response':     row[1],
                    'source_citation': row[2] or '',
                    'created_at':      str(row[3]) if row[3] else '',
                })
            return jsonify({'history': history})
        except Exception as e:
            return jsonify({'history': [], 'error': str(e)})

    @app.route('/api/assistant/history', methods=['DELETE'])
    def assistant_delete_history():
        """Clear all conversation history for a student."""
        data = request.get_json() or {}
        student_id = data.get('student_id')
        if not student_id:
            return jsonify({'error': 'student_id required'}), 400
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM assistant_conversations WHERE student_id = %s", (student_id,))
            deleted = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'deleted': deleted})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return {
        'generate_material_core': _generate_material_core,
        'resolve_topic_id': _resolve_topic_id,
        'student_grade': _student_grade,
        'dedup_recent': _dedup_recent,
        'insert_material': _insert_material,
        'record_generation': _record_generation,
    }
