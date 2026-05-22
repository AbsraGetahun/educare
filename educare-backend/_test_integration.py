# -*- coding: utf-8 -*-
"""Integration test: verify source citation, book priority, and topic-to-book mapping."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

# Force UTF-8 on Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from question_generator import (
    generate_questions, get_book_allocation, _get_book_meta,
    SOURCE_ORDER, TOPIC_BOOK_ALLOCATION, BOOK_NAME_MAP, BOOK_PRIORITY,
)
from rag_service import build_citation_from_hits, _book_display_name
from curriculum_extractor import BOOK_INFO, _get_book_info

errors = []

# ── 1. BOOK_INFO mapping ───────────────────────────────────────────────────────
print('=== BOOK INFO MAPPING ===')
expected = {
    'extreme mathematics grade 9&10.pdf':  ('Extreme Mathematics: Grade 9 & 10',  '9_10', 'extreme'),
    'extreme mathematics grade 11&12.pdf': ('Extreme Mathematics: Grade 11 & 12', '11_12', 'extreme'),
    'grade9_math.pdf':  ('Ethiopian Grade 9 Mathematics Textbook',  '9',  'grade'),
    'grade10_math.pdf': ('Ethiopian Grade 10 Mathematics Textbook', '10', 'grade'),
    'grade11_math.pdf': ('Ethiopian Grade 11 Mathematics Textbook', '11', 'grade'),
    'grade12_math.pdf': ('Ethiopian Grade 12 Mathematics Textbook', '12', 'grade'),
}
for k, exp in expected.items():
    got = _get_book_info(k)
    ok = got == exp
    status = 'OK' if ok else f'FAIL (expected {exp!r})'
    if not ok:
        errors.append(f'BOOK_INFO[{k!r}] = {got!r} expected {exp!r}')
    print(f'  {k}: {got} [{status}]')

# ── 2. BOOK_PRIORITY ──────────────────────────────────────────────────────────
print('\n=== BOOK PRIORITY ===')
assert _get_book_meta('extreme mathematics grade 9&10.pdf')[1] == 'high', 'Extreme 9&10 should be HIGH'
assert _get_book_meta('extreme mathematics grade 11&12.pdf')[1] == 'high', 'Extreme 11&12 should be HIGH'
assert _get_book_meta('grade9_math.pdf')[1] == 'medium', 'Grade 9 should be MEDIUM'
assert _get_book_meta('grade10_math.pdf')[1] == 'medium', 'Grade 10 should be MEDIUM'
print('  All priorities correct (Extreme=high, Grade=medium)')

# ── 3. TOPIC-TO-BOOK ALLOCATION ───────────────────────────────────────────────
print('\n=== TOPIC-TO-BOOK ALLOCATION ===')
for grade_band_topics in [
    ['algebra', 'linear equation', 'quadratic', 'systems of equations', 'sets', 'coordinate geometry'],
    ['limits', 'integration', 'differentiation', 'matrix', 'probability', 'trigonometry', 'statistics'],
]:
    for topic in grade_band_topics:
        key = (topic if topic in TOPIC_BOOK_ALLOCATION
               else next((k for k in TOPIC_BOOK_ALLOCATION
                           if k in topic.lower() or topic.lower() in k), 'algebra'))
        alloc = TOPIC_BOOK_ALLOCATION.get(key, TOPIC_BOOK_ALLOCATION['algebra'])
        pri = alloc.get('priority_sources', [])
        gra = alloc.get('grade_sources', [])
        mix = alloc.get('mix_sources', [])
        assert any('extreme' in s.lower() for s in pri), \
            f'{key}: priority_sources must include an Extreme book, got {pri}'
        assert len(pri) >= 2, f'{key}: priority_sources must have >=2 entries'
        assert len(gra) >= 2, f'{key}: grade_sources must have >=2 entries'
        assert len(mix) >= 2, f'{key}: mix_sources must have >=2 entries'
        print(f'  {key:30s}: pri={len(pri)}, grade={len(gra)}, mix={len(mix)} OK')

# ── 4. SOURCE PRIORITY ORDER ───────────────────────────────────────────────────
print('\n=== SOURCE PRIORITY ORDER ===')
sorted_pri = sorted(SOURCE_ORDER.items(), key=lambda x: x[1])
for sf, w in sorted_pri:
    ext = ' [EXTREME]' if sf in {'extreme mathematics grade 9&10.pdf', 'extreme mathematics grade 11&12.pdf'} else ''
    print(f'  weight={w}: {sf}{ext}')
# Extreme should have weight 1 and 2
assert SOURCE_ORDER['extreme mathematics grade 9&10.pdf'] == 1
assert SOURCE_ORDER['extreme mathematics grade 11&12.pdf'] == 2
print('  Extreme books have top priority (weight 1 and 2)')

# ── 5. SHARED UPPER SECTION ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
print('\n=== QUESTION GENERATION WITH CITATION (Quadratic, 7 qty) ===')
from question_generator import _resolve_topic_key
TOPIC_KEYS = ['Probability', 'Derivatives', 'Integration', 'Trigonometry', 'Sets',
              'Algebra', 'Limits', 'Coordinate Geometry', 'Matrix', 'Statistics']
for t in TOPIC_KEYS:
    key = _resolve_topic_key(t)
    from question_generator import PATTERNS
    pats = PATTERNS.get(key, [])
    status = 'OK' if pats else 'WARN'
    print(f'  {t:30s} -> key={key:25s} ({len(pats)} patterns) [{status}]')

# ── 6. GENERATE QUESTIONS WITH SOURCE PAYLOAD ─────────────────────────────────
print('\n=== GENERATE 7 QUESTIONS (Algebra) ===')
qs = generate_questions('Algebra', count=7, difficulty='medium',
                        source_files=[
                            'extreme mathematics grade 9&10.pdf',
                            'grade10_math.pdf', 'extreme mathematics grade 9&10.pdf',
                            'grade9_math.pdf', 'extreme mathematics grade 9&10.pdf',
                            'grade9_math.pdf', 'extreme mathematics grade 9&10.pdf',
                        ],
                        source_pages=[23, 45, 27, 31, 19, 22, 33])
print(f'  Generated {len(qs)} questions')
extreme = [q for q in qs if q.get('book_type') == 'extreme']
grade = [q for q in qs if q.get('book_type') == 'grade']
print(f'  Extreme book questions: {len(extreme)}')
print(f'  Grade book questions:   {len(grade)}')
for i, q in enumerate(qs, 1):
    print(f'  Q{i}: [{q.get("book_type",""):7s}] [{q.get("question_style",""):12s}] {q["question"][:65]:65s}')
    print(f'       cite={q.get("source_citation","")}')
# First 3 should be extreme/high exam-style
for i in range(min(3, len(qs))):
    assert qs[i].get('book_type') == 'extreme', f'Q{i+1} should be from Extreme book'
print('\n  First 3 are from Extreme books: PASS')

# ── 7. SECONDARY-SOURCE CITATION ───────────────────────────────────────────────
print('\n=== MULTI-SOURCE CITATION ===')
multi_hits = [
    {'source_file': 'Extreme Mathematics Grade 9&10.pdf', 'source_page': 45, 'source_grade': 9,
     'section': 'Unit 3: Quadratic Equations', 'text': 'ex', 'similarity': 95},
    {'source_file': 'grade10_math.pdf', 'source_page': 78, 'source_grade': 10,
     'section': 'Unit 2: Quadratic Functions', 'text': 'ex', 'similarity': 88},
    {'source_file': 'grade9_math.pdf', 'source_page': 60, 'source_grade': 9,
     'text': 'ex', 'similarity': 80},
]
cite = build_citation_from_hits(multi_hits, 'Quadratic Equations')
print(f'  Citation: {cite["source_citation"]}')
assert 'Extreme Mathematics' in cite['source_citation'], 'Citation must mention Extreme Mathematics'
assert cite['source_file'] == 'Extreme Mathematics Grade 9&10.pdf', 'Primary source must be Extreme'
print(f'  Source file: {cite["source_file"]}')
print(f'  Source page: {cite["source_page"]}')
print(f'  Source grade: {cite["source_grade"]}')
print('  Multi-source citation: PASS')

# ── 8. DISPLAY NAME ───────────────────────────────────────────────────────────
print('\n=== DISPLAY NAMES ===')
for f, expected_name in [
    ('extreme mathematics grade 9&10.pdf',  'Extreme Mathematics: Grade 9 & 10 (Ethiopia MOE)'),
    ('grade10_math.pdf',                     'Ethiopian Grade 10 Mathematics Textbook'),
    ('grade12_math.pdf',                     'Ethiopian Grade 12 Mathematics Textbook'),
]:
    got = _book_display_name(f)
    print(f'  {f!r} -> {got}')
    assert 'Textbook' in got or 'Extreme' in got or 'MOE' in got

print()
if errors:
    print('FAILURES:')
    for e in errors:
        print(f'  - {e}')
    sys.exit(1)
else:
    print('ALL CHECKS PASSED')
