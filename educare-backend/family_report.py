"""
Generate downloadable HTML student progress reports for the Family Dashboard.
"""
import html
from datetime import datetime


def _esc(value):
    return html.escape(str(value)) if value is not None else ''


def _pct(score, total_marks):
    if not total_marks:
        return 0.0
    return min(100.0, round((float(score) / float(total_marks)) * 100, 1))


def fetch_report_data(cursor, student_id):
    """Load all data needed for a family progress report."""
    from gap_utils import QUIZ_STUDENT_JOIN, fetch_student_gaps

    cursor.execute(
        """
        SELECT u.full_name, s.grade_level, s.section
        FROM users u
        JOIN students s ON u.user_id = s.user_id
        WHERE u.user_id = %s
        """,
        (student_id,),
    )
    student_info = cursor.fetchone()
    if not student_info:
        return None

    cursor.execute(
        f"""
        SELECT qa.attempt_id, qa.quiz_id, qa.score, qa.completed_at,
               q.title, t.topic_name, q.total_marks
        FROM quiz_attempt qa
        JOIN quizzes q ON qa.quiz_id = q.quiz_id
        JOIN topics t ON q.topic_id = t.topic_id
        {QUIZ_STUDENT_JOIN}
        WHERE s_qa.user_id = %s
        ORDER BY qa.completed_at DESC
        """,
        (student_id,),
    )
    attempts = cursor.fetchall() or []
    gaps_list = fetch_student_gaps(cursor, student_id)

    gap_topics = gaps_list[:5]
    recommendations = []
    for topic in gap_topics:
        topic_id = topic['topic_id']
        cursor.execute(
            f"""
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
            """,
            (topic_id, student_id),
        )
        for quiz in cursor.fetchall() or []:
            recommendations.append({
                'quiz_id': quiz[0],
                'title': quiz[1],
                'total_marks': quiz[2],
                'topic_name': topic['topic_name'],
                'avg_score': topic['avg_score'],
            })

    attempts_list = []
    for attempt in attempts:
        total_marks = attempt[6] or 0
        attempts_list.append({
            'quiz_title': attempt[4],
            'topic': attempt[5],
            'score': attempt[2],
            'total_marks': total_marks,
            'completed_at': str(attempt[3]) if attempt[3] else '',
            'percentage': _pct(attempt[2], total_marks),
        })

    total_attempts = len(attempts_list)
    avg_score = (
        round(sum(a['percentage'] for a in attempts_list) / total_attempts, 1)
        if total_attempts > 0 else 0
    )
    highest_score = max((a['percentage'] for a in attempts_list), default=0)
    lowest_score = min((a['percentage'] for a in attempts_list), default=0)

    return {
        'student': {
            'name': student_info[0],
            'grade_level': student_info[1],
            'section': student_info[2],
        },
        'stats': {
            'total_attempts': total_attempts,
            'average_score': avg_score,
            'highest_score': highest_score,
            'lowest_score': lowest_score,
            'topics_needing_work': len(gaps_list),
        },
        'attempts': attempts_list,
        'gaps': gaps_list,
        'recommendations': recommendations,
        'generated_at': datetime.now().strftime('%B %d, %Y at %I:%M %p'),
    }


def build_report_html(data: dict) -> str:
    """Build a printable HTML progress report."""
    student = data['student']
    stats = data['stats']
    attempts = data['attempts']
    gaps = data['gaps']
    recommendations = data['recommendations']
    generated_at = data.get('generated_at', '')

    attempts_rows = ''
    if attempts:
        for a in attempts:
            pct = a['percentage']
            badge = 'pass' if pct >= 70 else 'warn' if pct >= 40 else 'fail'
            attempts_rows += f"""
            <tr>
              <td>{_esc(a.get('quiz_title', ''))}</td>
              <td>{_esc(a.get('topic', ''))}</td>
              <td>{_esc(a.get('score'))} / {_esc(a.get('total_marks'))}</td>
              <td><span class="badge {badge}">{pct}%</span></td>
              <td>{_esc(a.get('completed_at', ''))}</td>
            </tr>"""
    else:
        attempts_rows = '<tr><td colspan="5" class="empty">No quiz attempts recorded yet.</td></tr>'

    gaps_rows = ''
    if gaps:
        for g in gaps:
            level = (g.get('weakness_level') or 'Moderate').lower()
            gaps_rows += f"""
            <tr>
              <td>{_esc(g.get('topic_name', ''))}</td>
              <td>{_esc(g.get('avg_score'))}%</td>
              <td><span class="badge {level}">{_esc(g.get('weakness_level', ''))}</span></td>
            </tr>"""
    else:
        gaps_rows = '<tr><td colspan="3" class="empty">No learning gaps identified — great work!</td></tr>'

    rec_rows = ''
    if recommendations:
        for r in recommendations:
            rec_rows += f"""
            <tr>
              <td>{_esc(r.get('title', ''))}</td>
              <td>{_esc(r.get('topic_name', ''))}</td>
              <td>{_esc(r.get('total_marks'))} marks</td>
            </tr>"""
    else:
        rec_rows = '<tr><td colspan="3" class="empty">No pending quiz recommendations.</td></tr>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>EDUCARE Progress Report — {_esc(student.get('name', ''))}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', system-ui, sans-serif; color: #1f2937; margin: 0; padding: 32px; background: #f9fafb; }}
    .page {{ max-width: 900px; margin: 0 auto; background: #fff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }}
    h1 {{ color: #2563eb; margin: 0 0 4px; font-size: 28px; }}
    .subtitle {{ color: #6b7280; margin: 0 0 24px; font-size: 14px; }}
    h2 {{ font-size: 18px; color: #111827; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; margin: 28px 0 12px; }}
    .info-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }}
    .info-card {{ background: #f3f4f6; padding: 14px; border-radius: 8px; }}
    .info-card label {{ display: block; font-size: 11px; text-transform: uppercase; color: #6b7280; margin-bottom: 4px; }}
    .info-card span {{ font-size: 16px; font-weight: 600; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 8px; }}
    .stat {{ text-align: center; padding: 16px; background: #eff6ff; border-radius: 8px; }}
    .stat .val {{ font-size: 24px; font-weight: 700; color: #2563eb; }}
    .stat .lbl {{ font-size: 11px; color: #6b7280; margin-top: 4px; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 8px; }}
    th {{ background: #f3f4f6; text-align: left; padding: 10px 12px; font-weight: 600; }}
    td {{ padding: 10px 12px; border-bottom: 1px solid #e5e7eb; }}
    tr:nth-child(even) td {{ background: #fafafa; }}
    .empty {{ text-align: center; color: #9ca3af; font-style: italic; }}
    .badge {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }}
    .badge.pass {{ background: #d1fae5; color: #065f46; }}
    .badge.warn {{ background: #fef3c7; color: #92400e; }}
    .badge.fail {{ background: #fee2e2; color: #991b1b; }}
    .badge.high {{ background: #fee2e2; color: #991b1b; }}
    .badge.moderate {{ background: #fef3c7; color: #92400e; }}
    .badge.low {{ background: #d1fae5; color: #065f46; }}
    .footer {{ margin-top: 32px; padding-top: 16px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #9ca3af; text-align: center; }}
    @media print {{
      body {{ background: #fff; padding: 0; }}
      .page {{ box-shadow: none; padding: 20px; }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <h1>EDUCARE Student Progress Report</h1>
    <p class="subtitle">Generated on {_esc(generated_at)}</p>

    <h2>Student Information</h2>
    <div class="info-grid">
      <div class="info-card"><label>Name</label><span>{_esc(student.get('name'))}</span></div>
      <div class="info-card"><label>Grade</label><span>{_esc(student.get('grade_level'))}</span></div>
      <div class="info-card"><label>Section</label><span>{_esc(student.get('section'))}</span></div>
    </div>

    <h2>Performance Summary</h2>
    <div class="stats-grid">
      <div class="stat"><div class="val">{stats.get('total_attempts', 0)}</div><div class="lbl">Quiz Attempts</div></div>
      <div class="stat"><div class="val">{stats.get('average_score', 0)}%</div><div class="lbl">Average Score</div></div>
      <div class="stat"><div class="val">{stats.get('highest_score', 0)}%</div><div class="lbl">Highest Score</div></div>
      <div class="stat"><div class="val">{stats.get('topics_needing_work', 0)}</div><div class="lbl">Topics Needing Work</div></div>
    </div>

    <h2>Quiz History</h2>
    <table>
      <thead><tr><th>Quiz</th><th>Topic</th><th>Score</th><th>Percentage</th><th>Date</th></tr></thead>
      <tbody>{attempts_rows}</tbody>
    </table>

    <h2>Learning Gaps</h2>
    <table>
      <thead><tr><th>Topic</th><th>Average Score</th><th>Weakness Level</th></tr></thead>
      <tbody>{gaps_rows}</tbody>
    </table>

    <h2>Recommended Practice</h2>
    <table>
      <thead><tr><th>Quiz</th><th>Topic</th><th>Marks</th></tr></thead>
      <tbody>{rec_rows}</tbody>
    </table>

    <div class="footer">
      EDUCARE — Personalized Learning Platform · Report for {_esc(student.get('name'))}
    </div>
  </div>
</body>
</html>"""
