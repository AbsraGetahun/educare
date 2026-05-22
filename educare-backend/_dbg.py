# -*- coding: utf-8 -*-
"""Trace the _detect_math_topic logic for specific queries."""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

MATH_KEYWORDS = {
    'algebra':       ['solve', 'equation'],
    'limits':        ['limit'],
    'derivative':    ['derivative'],
    'integration':   ['integral'],
    'matrix':        ['matrix'],
    'trigonometry':  ['sin', 'cos', 'tan'],
    'sets':          ['union'],
    'probability':   ['probability'],
    'statistics':    ['mean'],
    'coordinate geometry': ['distance', 'slope'],
}

def _detect_math_topic(question):
    q = question.lower()
    for topic in MATH_KEYWORDS:
        if topic in q:
            return topic
    for topic, kw_list in MATH_KEYWORDS.items():
        for kw in kw_list:
            if kw in q:
                return topic
    return 'general'

tests = [
    ('sin(30 degrees)',       'trigonometry'),
    ('limit of x^2 as x approaches 2', 'limits'),
    ('distance between two points', 'coordinate geometry'),
    ('solve 2x+5=15',         'algebra'),
    ('integral of 2x',        'integration'),
    ('set theory union',      'sets'),
    ('find the mean of 4,8,15','statistics'),
]

for q, exp in tests:
    ql = q.lower()
    # Trace key-first check
    for topic in MATH_KEYWORDS:
        if topic in ql:
            print(f'  KEY-MATCH: {ql[:30]!r} -> topic={topic!r} (key found)')
            break
    # Trace keyword check
    for topic, kws in MATH_KEYWORDS.items():
        for kw in kws:
            if kw in ql:
                print(f'  KW-MATCH:  {ql[:30]!r} -> kw={kw!r} -> topic={topic!r}')
                break
    got = _detect_math_topic(q)
    status = 'OK' if got == exp else 'FAIL'
    print(f'  [{status}] got={got!r:25s} exp={exp!r}')
    print()
