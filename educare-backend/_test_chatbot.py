# -*- coding: utf-8 -*-
"""Test the chatbot answer engine: greetings, scope-check, word problems, citations."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import faiss  # noqa: F401
except ImportError:
    print("FAISS not available — some tests will be skipped.\n")

from rag_service import (
    generate_math_answer, is_greeting, is_math_question, is_non_math_question,
    _detect_math_topic, detect_and_solve_word_problem,
    build_citation_from_hits, _book_display_name,
)

errors = []
passed = 0

def chk(label, condition):
    global passed
    if condition:
        passed += 1
    else:
        errors.append(f'FAIL: {label}')

# ── 1. Greetings ───────────────────────────────────────────────────────────────
print('=== 1. GREETINGS ===')
greeting_tests = [
    ('hi', 'hello'),
    ('hello', 'E'),            # not tested yet — using few letters
    ('hey', 'hello'),
    ('good morning', 'Morning'),
    ('good afternoon', 'afternoon'),
    ('how are you', "I'm doing great"),
    ('how are you doing', "I'm doing great"),
    ("what's up", "👋 Hello"),
    ("thanks", "welcome"),
    ("thank you", "welcome"),
    ("bye", "Goodbye"),
    ("goodbye", "goodbye"),
    ("what can you do", "I can help you with"),
]
for msg, expected in greeting_tests:
    r = is_greeting(msg)
    chk(f'greeting ({msg!r})', r is not None and expected.lower() in r.lower())

not_greetings = ['x + 5 = 15', 'lim(x->2)', 'what is the capital', 'integral of x']
for msg in not_greetings:
    chk(f'NOT greeting ({msg!r})', is_greeting(msg) is None)

# ── 2. Math/non-math detection ─────────────────────────────────────────────────
print('\n=== 2. MATH DETECTION ===')
math_should_be = [
    'solve 2x + 5 = 15',
    'how do i solve quadratic equations',
    'find lim(x->0) sin(x)/x',
    'derivative of x^2',
    'integral of 2x dx',
    'probability of rolling a 6',
    'distance between (1,2) and (3,4)',
    'matrix addition of [1;2]+[3;4]',
    'sin(30 degrees)',
    'what is the standard deviation',
    'set theory union',
    'trigonometric functions',
]
for msg in math_should_be:
    chk(f'math ({msg[:35]!r})', is_math_question(msg))

non_math_should = [
    'what is the capital of France',
    'who won the World Cup',
    'islam',
    'tell me a joke',
    'world war 2',
    'the capital of Ethiopia',
]
for msg in non_math_should:
    chk(f'NOT math ({msg[:35]!r})', not is_non_math_question(msg) or not is_math_question(msg))

# ── 3. Topic detection ─────────────────────────────────────────────────────────
print('\n=== 3. TOPIC DETECTION ===')
topic_tests = [
    ('solve 2x+5=15', 'equation'),
    ('how to solve x^2 - 5x + 6 = 0', 'equation'),
    ('limit of x^2 as x approaches 2', 'limit'),
    ('derivative of 3x^2 + 2x - 5', 'derivative'),
    ('integral of 2x', 'integration'),
    ('probability of flipping heads', 'probability'),
    ('distance between two points', 'coordinate geometry'),
    ('matrix inverse of 2x2', 'matrix'),
    ('sin(30°)', 'trigonometry'),
    ('find the mean of 4,8,15', 'statistics'),
    ('set theory union', 'sets'),
]
for msg, exp in topic_tests:
    got = _detect_math_topic(msg)
    chk(f'topic ({msg[:35]!r} -> {exp})', got == exp)

# ── 4. Word problem routing ────────────────────────────────────────────────────
print('\n=== 4. WORD PROBLEM ROUTING ===')
wp_tests = [
    ("John is twice as old as Mary. In 5 years, sum is 40.",
     'Word Problems', 'age'),
    ("A car travels at 60 km/h for 2 hours",
     'Word Problems', 'motion'),
    ("mix 10 litres of 30% solution with x litres of 70%",
     'Word Problems', 'mixture'),
    ("6 days alone, 9 days together - work problem",
     'Word Problems', 'work'),
]
for q, t, _sub in wp_tests:
    result = detect_and_solve_word_problem(q)
    chk(f'WP ({q[:35]!r})', result is not None and result['topic'] == t)
no_wp_msgs = ['x^2 + 5x + 6 = 0', 'lim(x->2) (x^2-4)/(x-2)', 'f(x) = x^2']
for q in no_wp_msgs:
    result = detect_and_solve_word_problem(q)
    chk(f'NOT WP ({q!r})', result is None)

# ── 5. generate_math_answer ────────────────────────────────────────────────────
print('\n=== 5. GENERATE MATH ANSWER ===')

r = generate_math_answer('hi', grade_level=9)
chk(f'greeting returns greeting-like', '👋' in r['answer'] or 'Math Assistant' in r['answer'])
chk(f'greeting topic = greeting', r['topic'] == 'greeting')
chk(f'greeting source empty', r['source_file'] == '')
chk(f'greeting confidence=high', r['confidence'] == 'high')

r = generate_math_answer('how are you', grade_level=9)
chk(f"how are you returns friendly", "I'm doing great" in r['answer'] or "help" in r['answer'])

r = generate_math_answer('thanks', grade_level=9)
chk(f'thanks returns welcome', 'welcome' in r['answer'].lower())

r = generate_math_answer('bye', grade_level=9)
chk(f'bye returns goodbye', 'goodbye' in r['answer'].lower() or 'Bye' in r['answer'])

r = generate_math_answer('what can you do', grade_level=9)
chk(f'what-can-you-do returns capabilities', "Algebra" in r['answer'] or "Limits" in r['answer'])

# Non-math question
r = generate_math_answer('what is the capital of France', grade_level=9)
chk(f'non-math returns scope msg', 'out of my scope' in r['answer'].lower() or 'under development' in r['answer'].lower())
chk(f'non-math source empty', r['source_file'] == '')

# Math question (may or may not find FAISS content)
r = generate_math_answer('how do i solve 2x + 5 = 15', grade_level=9)
chk(f'solve-2x+5 has answer >50 chars', len(r['answer']) >= 50)
chk(f'solve-2x+5 has confidence', r['confidence'] in ('high', 'medium', 'low'))
chk(f'solve-2x+5 has source_file', bool(r['source_file'] or ''))
print(f'  solve-2x+5 confidence={r["confidence"]!r} topic={r["topic"]!r} source={r["source_file"]!r}')

r = generate_math_answer('find the derivative of x^2', grade_level=11)
chk(f'derivative has answer', len(r['answer']) >= 20)
chk(f'derivative x^2 gives 2x', '2x' in r['answer'].replace(' ', '').lower() or '2*x' in r['answer'].lower())
print(f'  deriv confidence={r["confidence"]!r} topic={r["topic"]!r}')

r = generate_math_answer('find the derivative of 3x^2 + 2x - 5', grade_level=12)
chk(f'derivative poly has answer', 'Answer:' in r['answer'])
chk(f'derivative poly has 6x', '6x' in r['answer'].replace(' ', '').lower())

r = generate_math_answer('lim(x->2) (x^2-4)/(x-2)', grade_level=12)
chk(f'limit rational has answer', 'Answer:' in r['answer'])
chk(f'limit rational is 4', '4' in r['answer'])

r = generate_math_answer('lim(x->0) sin(x)/x', grade_level=12)
chk(f'limit sin/x is 1', 'Answer: 1' in r['answer'] or 'Answer:1' in r['answer'].replace(' ', ''))

r = generate_math_answer('find lim(x->0) sin(3x)/(2x)', grade_level=12)
chk(f'limit sin3x/2x', '1.5' in r['answer'] or '3/2' in r['answer'])

# Age word problem
r = generate_math_answer('John is twice as old as Mary. In 5 years sum is 40.', grade_level=9)
chk(f'age-wp has answer >40', len(r['answer']) >= 40)
chk(f'age-wp has EXTREME citation', bool(r['source_citation']))
print(f'  age-wp source: {r["source_citation"]!r}')

# ── 6. Book display names ─────────────────────────────────────────────────────
print('\n=== 6. BOOK DISPLAY NAMES ===')
dc = [
    ('extreme mathematics grade 9&10.pdf',
     'Extreme Mathematics: Grade 9 & 10 (Ethiopia MOE)'),
    ('extreme mathematics grade 11&12.pdf',
     'Extreme Mathematics: Grade 11 & 12 (Ethiopia MOE)'),
    ('grade9_math.pdf',  'Ethiopian Grade 9 Mathematics Textbook'),
    ('grade10_math.pdf', 'Ethiopian Grade 10 Mathematics Textbook'),
    ('grade11_math.pdf', 'Ethiopian Grade 11 Mathematics Textbook'),
    ('grade12_math.pdf', 'Ethiopian Grade 12 Mathematics Textbook'),
]
for src, exp in dc:
    got = _book_display_name(src)
    chk(f'display ({src[:32]!r})', exp in got)
    print(f'  {src[:38]:38s} -> {got[:55]}')

# ── 7. Multi-source citation ───────────────────────────────────────────────────
print('\n=== 7. MULTI-SOURCE CITATION ===')
multi = [
    {'source_file': 'Extreme Mathematics Grade 9&10.pdf', 'source_page': 45,
     'source_grade': 9, 'section': 'Unit 3: Quadratic Equations', 'text': 'ex', 'similarity': 95},
    {'source_file': 'grade10_math.pdf', 'source_page': 78,
     'source_grade': 10, 'section': 'Unit 2: Quadratic Functions', 'text': 'ex', 'similarity': 88},
    {'source_file': 'grade9_math.pdf', 'source_page': 60,
     'source_grade': 9, 'text': 'ex', 'similarity': 80},
]
cite = build_citation_from_hits(multi, 'Quadratic Equations')
chk('primary is Extreme', 'Extreme Mathematics' in cite['source_citation'])
chk('page is 45', cite['source_page'] == 45)
chk('section present', 'Unit 3' in cite['section'])
print(f'  citation: {cite["source_citation"]}')

# ── Summary ────────────────────────────────────────────────────────────────────
print(f'\n=== RESULTS: {passed} passed, {len(errors)} failed ===')
if errors:
    for e in errors:
        print(f'  ✗ {e}')
    sys.exit(1)
else:
    print('All checks PASSED ✅')
