"""
Student material assignment helpers.
Links generated materials to specific students via student_materials junction table.
"""

OPTIONAL_MATERIAL_COLS = ('source_file', 'source_page', 'source_grade', 'section_title')


def existing_material_columns(cursor, colnames=None):
    """Return optional material columns that exist in the database."""
    colnames = colnames or OPTIONAL_MATERIAL_COLS
    existing = []
    for col in colnames:
        try:
            cursor.execute("SHOW COLUMNS FROM material LIKE %s", (col,))
            if cursor.fetchone():
                existing.append(col)
        except Exception:
            pass
    return existing


def build_material_select(m_alias='m', t_alias='t', include_topic_id=False):
    """Build SELECT column list for material queries (only existing optional cols)."""
    cols = [
        f'{m_alias}.material_id',
        f'{m_alias}.title',
        f'{m_alias}.content',
        f'{m_alias}.source_citation',
        f'{m_alias}.generated_date',
        f'{t_alias}.topic_name',
    ]
    if include_topic_id:
        cols.append(f'{m_alias}.topic_id')
    return cols


def material_row_to_dict(row, extra_cols, assigned_students=None, has_topic_id=False):
    """Map a material SELECT row tuple to a JSON-serializable dict."""
    item = {
        'material_id': row[0],
        'title': row[1],
        'content': row[2],
        'source_citation': row[3],
        'generated_date': str(row[4]) if row[4] else '',
        'topic_name': row[5] if row[5] else '',
    }
    idx = 6
    if has_topic_id:
        item['topic_id'] = row[idx]
        idx += 1
    for col in extra_cols:
        item[col] = row[idx]
        idx += 1
    if assigned_students is not None:
        item['assigned_students'] = assigned_students
    return item


def ensure_student_materials_table(cursor):
    """Create student_materials table if it does not exist."""
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_materials (
                id INT AUTO_INCREMENT PRIMARY KEY,
                material_id INT NOT NULL,
                student_id INT NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_assignment (material_id, student_id),
                INDEX idx_student (student_id),
                INDEX idx_material (material_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
    except Exception:
        pass


def table_exists(cursor, table_name):
    try:
        cursor.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = %s LIMIT 1",
            (table_name,),
        )
        return cursor.fetchone() is not None
    except Exception:
        return False


def ensure_student_profile(cursor, student_id, grade_level=None):
    """
    Return users.user_id for a student, creating a students row if the user exists
    but is missing from the students table (fixes assignment for partial accounts).
    """
    if student_id is None:
        return None
    try:
        sid = int(student_id)
    except (TypeError, ValueError):
        return None
    try:
        cursor.execute(
            """
            SELECT s.user_id FROM students s
            WHERE s.user_id = %s OR s.student_id = %s
            LIMIT 1
            """,
            (sid, sid),
        )
        row = cursor.fetchone()
        if row and row[0]:
            return int(row[0])

        cursor.execute(
            "SELECT user_id, role FROM users WHERE user_id = %s LIMIT 1",
            (sid,),
        )
        user = cursor.fetchone()
        if not user or (user[1] or '').lower() != 'student':
            return None

        gl = int(grade_level) if grade_level is not None else 10
        cursor.execute(
            """
            INSERT INTO students (user_id, grade_level, section)
            VALUES (%s, %s, 'A')
            ON DUPLICATE KEY UPDATE user_id = user_id
            """,
            (sid, gl),
        )
        return sid
    except Exception as exc:
        print(f"ensure_student_profile failed for {student_id}: {exc}")
        try:
            cursor.execute(
                """
                SELECT s.user_id FROM students s
                WHERE s.user_id = %s OR s.student_id = %s
                LIMIT 1
                """,
                (sid, sid),
            )
            row = cursor.fetchone()
            if row and row[0]:
                return int(row[0])
        except Exception:
            pass
    return None


def resolve_student_user_id(cursor, student_id, grade_level=None):
    """Normalize API id to users.user_id (for generation_history and API responses)."""
    return ensure_student_profile(cursor, student_id, grade_level)


def resolve_student_pk(cursor, student_id, grade_level=None):
    """
    Return students.student_id for student_materials FK.
    DB constraint references students(student_id), not user_id.
    """
    user_id = ensure_student_profile(cursor, student_id, grade_level)
    if not user_id:
        return None
    try:
        cursor.execute(
            "SELECT student_id FROM students WHERE user_id = %s LIMIT 1",
            (user_id,),
        )
        row = cursor.fetchone()
        if row and row[0] is not None:
            return int(row[0])
    except Exception as exc:
        print(f"resolve_student_pk failed for user_id={user_id}: {exc}")
    return None


def repair_student_materials_fk_values(cursor):
    """Fix rows where student_materials stored user_id instead of students.student_id."""
    if not table_exists(cursor, 'student_materials'):
        return 0
    try:
        cursor.execute(
            """
            UPDATE student_materials sm
            INNER JOIN students s ON sm.student_id = s.user_id
            SET sm.student_id = s.student_id
            WHERE sm.student_id <> s.student_id
            """
        )
        return cursor.rowcount or 0
    except Exception as exc:
        print(f"repair_student_materials_fk_values: {exc}")
        return 0


def assign_material_to_students(cursor, material_id, student_ids, grade_level=None):
    """Assign a material to one or more students (API ids → students.student_id)."""
    if not student_ids or not material_id:
        return 0
    ensure_student_materials_table(cursor)
    assigned = 0
    for sid in student_ids:
        student_pk = resolve_student_pk(cursor, sid, grade_level=grade_level)
        if not student_pk:
            print(f"assign_material_to_students: no students row for id={sid}")
            continue
        try:
            cursor.execute(
                """
                INSERT INTO student_materials (material_id, student_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE student_id = student_id
                """,
                (material_id, student_pk),
            )
            cursor.execute(
                """
                SELECT 1 FROM student_materials
                WHERE material_id = %s AND student_id = %s
                """,
                (material_id, student_pk),
            )
            if cursor.fetchone():
                assigned += 1
        except Exception as exc:
            print(
                f"assign_material_to_students failed material={material_id} "
                f"student_pk={student_pk}: {exc}"
            )
    return assigned


def set_material_assignments(cursor, material_id, student_ids, grade_level=None):
    """Replace all assignments for a material with the given student list."""
    if not material_id:
        return 0
    ensure_student_materials_table(cursor)
    try:
        cursor.execute(
            "DELETE FROM student_materials WHERE material_id = %s",
            (material_id,),
        )
    except Exception:
        pass
    return assign_material_to_students(
        cursor, material_id, student_ids, grade_level=grade_level
    )


def column_exists(cursor, table_name, column_name):
    try:
        cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE %s", (column_name,))
        return cursor.fetchone() is not None
    except Exception:
        return False


def ensure_generation_history_material_id(cursor):
    """Add material_id FK column to generation_history for precise assignment linking."""
    if not table_exists(cursor, 'generation_history'):
        return
    try:
        if not column_exists(cursor, 'generation_history', 'material_id'):
            cursor.execute(
                "ALTER TABLE generation_history "
                "ADD COLUMN material_id INT NULL AFTER difficulty"
            )
            cursor.execute(
                "ALTER TABLE generation_history "
                "ADD INDEX idx_material_id (material_id)"
            )
    except Exception:
        pass


def list_students_in_grade(cursor, grade_level):
    """Return user_ids for all students in a grade."""
    grade_level = int(grade_level)
    cursor.execute(
        """
        SELECT u.user_id
        FROM users u
        JOIN students s ON u.user_id = s.user_id
        WHERE u.role = 'student' AND s.grade_level = %s
        ORDER BY u.full_name
        """,
        (grade_level,),
    )
    ids = []
    for (uid,) in cursor.fetchall() or []:
        resolved = ensure_student_profile(cursor, uid, grade_level)
        if resolved and resolved not in ids:
            ids.append(resolved)
    return ids


def assign_material_to_grade(cursor, material_id, grade_level):
    """Assign a material to all students in a grade level."""
    student_ids = list_students_in_grade(cursor, grade_level)
    return assign_material_to_students(cursor, material_id, student_ids)


def get_assigned_students(cursor, material_id):
    """Return list of {user_id, full_name, grade_level} for a material."""
    if not table_exists(cursor, 'student_materials'):
        return []
    try:
        cursor.execute(
            """
            SELECT s.user_id, u.full_name, s.grade_level
            FROM student_materials sm
            INNER JOIN students s ON sm.student_id = s.student_id
            INNER JOIN users u ON s.user_id = u.user_id
            WHERE sm.material_id = %s
            ORDER BY u.full_name
            """,
            (material_id,),
        )
        return [
            {
                'user_id': int(r[0]),
                'full_name': r[1] or f'Student {r[0]}',
                'grade_level': r[2],
            }
            for r in cursor.fetchall() or []
            if r[0] is not None
        ]
    except Exception as exc:
        print(f"get_assigned_students: {exc}")
        return []


def find_pending_material_for_student_topic(cursor, student_id, topic_name):
    """Find a pending material for this student + topic (for dedup / repair flows)."""
    student_user_id = resolve_student_user_id(cursor, student_id)
    if not student_user_id or not topic_name:
        return None
    topic_name = (topic_name or '').strip()
    if not topic_name:
        return None

    ensure_generation_history_material_id(cursor)

    try:
        if table_exists(cursor, 'generation_history') and column_exists(
            cursor, 'generation_history', 'material_id'
        ):
            cursor.execute(
                """
                SELECT m.material_id
                FROM generation_history gh
                JOIN material m ON m.material_id = gh.material_id
                WHERE gh.student_id = %s
                  AND m.approval_status = 'Pending'
                  AND (
                    LOWER(gh.topic_name) = LOWER(%s)
                    OR LOWER(%s) LIKE CONCAT('%%', LOWER(gh.topic_name), '%%')
                    OR LOWER(gh.topic_name) LIKE CONCAT('%%', LOWER(%s), '%%')
                  )
                ORDER BY m.generated_date DESC
                LIMIT 1
                """,
                (student_user_id, topic_name, topic_name, topic_name),
            )
            row = cursor.fetchone()
            if row:
                return row[0]

        if table_exists(cursor, 'generation_history'):
            cursor.execute(
                """
                SELECT m.material_id
                FROM generation_history gh
                JOIN material m ON ABS(TIMESTAMPDIFF(SECOND, m.generated_date, gh.generated_at)) <= 120
                LEFT JOIN topics t ON m.topic_id = t.topic_id
                WHERE gh.student_id = %s
                  AND m.approval_status = 'Pending'
                  AND (
                    LOWER(gh.topic_name) = LOWER(%s)
                    OR LOWER(COALESCE(t.topic_name, '')) = LOWER(%s)
                    OR LOWER(m.title) LIKE CONCAT('%%', LOWER(%s), '%%')
                  )
                ORDER BY m.generated_date DESC
                LIMIT 1
                """,
                (student_user_id, topic_name, topic_name, topic_name),
            )
            row = cursor.fetchone()
            if row:
                return row[0]
    except Exception as exc:
        print(f"find_pending_material_for_student_topic: {exc}")
    return None


def link_generation_history_to_material(cursor, material_id, student_id, topic_name):
    """Attach material_id to recent generation_history rows missing the link."""
    student_user_id = resolve_student_user_id(cursor, student_id)
    if not student_user_id or not material_id or not table_exists(cursor, 'generation_history'):
        return
    if not column_exists(cursor, 'generation_history', 'material_id'):
        return
    try:
        cursor.execute(
            """
            UPDATE generation_history
            SET material_id = %s
            WHERE student_id = %s
              AND material_id IS NULL
              AND (
                LOWER(topic_name) = LOWER(%s)
                OR LOWER(%s) LIKE CONCAT('%%', LOWER(topic_name), '%%')
                OR LOWER(topic_name) LIKE CONCAT('%%', LOWER(%s), '%%')
              )
              AND generated_at >= DATE_SUB(NOW(), INTERVAL 14 DAY)
            ORDER BY generated_at DESC
            LIMIT 1
            """,
            (material_id, student_user_id, topic_name, topic_name, topic_name),
        )
    except Exception:
        pass


def _topic_name_for_material(cursor, material_id):
    """Resolve topic label from topics table or material title."""
    try:
        cursor.execute(
            """
            SELECT t.topic_name, m.title
            FROM material m
            LEFT JOIN topics t ON m.topic_id = t.topic_id
            WHERE m.material_id = %s
            """,
            (material_id,),
        )
        row = cursor.fetchone()
        if not row:
            return ''
        topic_name, title = row[0], row[1]
        if topic_name:
            return str(topic_name).strip()
        if title:
            title = str(title).strip()
            if title.lower().startswith('practice:'):
                return title.split(':', 1)[1].strip()
            return title
    except Exception:
        pass
    return ''


def student_materials_filter_by_user_sql(user_id_placeholder='%s'):
    """SQL joins: student_materials → students, filtered by users.user_id."""
    return f"""
        INNER JOIN student_materials sm ON sm.material_id = m.material_id
        INNER JOIN students s_sm ON sm.student_id = s_sm.student_id
          AND s_sm.user_id = {user_id_placeholder}
    """


def ensure_material_assigned(cursor, material_id, student_id=None, grade_level=None):
    """Ensure a material has at least one student assignment; backfill from history if needed."""
    if student_id:
        uid = resolve_student_user_id(cursor, student_id, grade_level)
        if uid:
            count = set_material_assignments(
                cursor, material_id, [uid], grade_level=grade_level
            )
            if count:
                link_generation_history_to_material(
                    cursor, material_id, uid, _topic_name_for_material(cursor, material_id)
                )
                return count

    existing = get_assigned_students(cursor, material_id)
    if existing:
        return len(existing)

    intended = get_intended_student_ids(cursor, material_id)
    if intended:
        resolved = []
        for sid in intended:
            uid = resolve_student_user_id(cursor, sid)
            if uid and uid not in resolved:
                resolved.append(uid)
        if resolved:
            count = set_material_assignments(
                cursor, material_id, resolved, grade_level=grade_level
            )
            if count:
                return count

    return 0


def repair_unassigned_pending_materials(cursor):
    """Backfill student_materials for pending materials missing assignments."""
    if not table_exists(cursor, 'material'):
        return 0
    repaired = 0
    try:
        cursor.execute(
            "SELECT material_id FROM material WHERE approval_status = 'Pending'"
        )
        for (material_id,) in cursor.fetchall() or []:
            if get_assigned_students(cursor, material_id):
                continue
            if ensure_material_assigned(cursor, material_id):
                repaired += 1
    except Exception as exc:
        print(f"repair_unassigned_pending_materials: {exc}")
    return repaired


def get_intended_student_ids(cursor, material_id):
    """
    Resolve which student(s) a material was generated for.
    Uses generation_history.material_id when available, else closest timestamp match.
    """
    if not table_exists(cursor, 'generation_history'):
        return []

    ids = []
    try:
        if column_exists(cursor, 'generation_history', 'material_id'):
            cursor.execute(
                """
                SELECT DISTINCT student_id FROM generation_history
                WHERE material_id = %s AND student_id IS NOT NULL
                """,
                (material_id,),
            )
            for r in cursor.fetchall() or []:
                uid = resolve_student_user_id(cursor, r[0])
                if uid and uid not in ids:
                    ids.append(uid)
            if ids:
                return ids

        cursor.execute(
            "SELECT generated_date FROM material WHERE material_id = %s",
            (material_id,),
        )
        row = cursor.fetchone()
        if not row or not row[0]:
            return ids

        gen_date = row[0]
        topic_name = _topic_name_for_material(cursor, material_id)

        if topic_name:
            cursor.execute(
                """
                SELECT gh.student_id
                FROM generation_history gh
                WHERE gh.student_id IS NOT NULL
                  AND ABS(TIMESTAMPDIFF(SECOND, gh.generated_at, %s)) <= 3600
                  AND (
                    LOWER(gh.topic_name) = LOWER(%s)
                    OR LOWER(%s) LIKE CONCAT('%%', LOWER(gh.topic_name), '%%')
                    OR LOWER(gh.topic_name) LIKE CONCAT('%%', LOWER(%s), '%%')
                  )
                ORDER BY ABS(TIMESTAMPDIFF(SECOND, gh.generated_at, %s))
                LIMIT 1
                """,
                (gen_date, topic_name, topic_name, topic_name, gen_date),
            )
            close = cursor.fetchone()
            if close and close[0]:
                uid = resolve_student_user_id(cursor, close[0])
                if uid:
                    return [uid]

        # Closest generation event to this material (any topic) within 1 hour
        cursor.execute(
            """
            SELECT gh.student_id
            FROM generation_history gh
            WHERE gh.student_id IS NOT NULL
              AND ABS(TIMESTAMPDIFF(SECOND, gh.generated_at, %s)) <= 3600
            ORDER BY ABS(TIMESTAMPDIFF(SECOND, gh.generated_at, %s))
            LIMIT 1
            """,
            (gen_date, gen_date),
        )
        close = cursor.fetchone()
        if close and close[0]:
            uid = resolve_student_user_id(cursor, close[0])
            if uid:
                return [uid]
    except Exception as exc:
        print(f"get_intended_student_ids material={material_id}: {exc}")
    return ids


def sync_material_assignments_on_approve(cursor, material_id):
    """
    On teacher approval, set assignments to ONLY the intended student(s).
    Preserves assignments created at generation time when history is missing.
    """
    return ensure_material_assigned(cursor, material_id)


def repair_overassigned_materials(cursor, max_assignments=2):
    """
    Fix materials wrongly assigned to many students (legacy grade-wide assigns).
    Uses generation_history when available; otherwise clears orphan assignments.
    """
    if not table_exists(cursor, 'student_materials'):
        return 0
    repaired = 0
    try:
        cursor.execute(
            """
            SELECT material_id, COUNT(DISTINCT student_id) AS n
            FROM student_materials
            GROUP BY material_id
            HAVING n > %s
            """,
            (max_assignments,),
        )
        for (material_id, _) in cursor.fetchall() or []:
            intended = get_intended_student_ids(cursor, material_id)
            if intended and len(intended) <= max_assignments:
                set_material_assignments(cursor, material_id, intended)
                repaired += 1
            # If intended cannot be resolved, leave assignments unchanged (avoid orphaning approved materials)
    except Exception:
        pass
    return repaired


def backfill_assignments_from_history(cursor, material_id):
    """Legacy alias — delegates to sync."""
    return sync_material_assignments_on_approve(cursor, material_id)


def _safe_teacher_id(cursor, teacher_id):
    """Use a teacher id that exists in teachers table (FK on generation_history)."""
    tid = teacher_id or 1
    try:
        cursor.execute("SELECT user_id FROM teachers WHERE user_id = %s LIMIT 1", (tid,))
        if cursor.fetchone():
            return tid
        cursor.execute("SELECT user_id FROM teachers ORDER BY user_id LIMIT 1")
        row = cursor.fetchone()
        if row:
            return row[0]
    except Exception:
        pass
    return tid


def record_generation_with_material(cursor, teacher_id, student_id, topic_name,
                                    grade_level, difficulty, material_id=None):
    """Record generation history linked to material_id when possible."""
    ensure_generation_history_material_id(cursor)
    student_user_id = resolve_student_user_id(cursor, student_id)
    if not student_user_id:
        print(f"record_generation: student {student_id} not in students table")
        return
    teacher_id = _safe_teacher_id(cursor, teacher_id)
    try:
        cols = ['teacher_id', 'student_id', 'topic_name', 'grade_level', 'difficulty']
        vals = [teacher_id, student_user_id, topic_name, grade_level, difficulty]
        if material_id is not None and column_exists(cursor, 'generation_history', 'material_id'):
            cols.append('material_id')
            vals.append(material_id)
        cursor.execute(
            f"INSERT INTO generation_history ({', '.join(cols)}) "
            f"VALUES ({', '.join(['%s'] * len(vals))})",
            vals,
        )
    except Exception:
        pass
