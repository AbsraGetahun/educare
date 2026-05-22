"""
Part 1: Question Pattern Generator
Generates math questions using patterns and random numbers. No AI or external APIs.
Now supports ALL 6 curriculum textbooks with priority sourcing and source citation.
"""

import random
import math

# ── Textbook Source Name Mapping ─────────────────────────────────────────────
BOOK_NAME_MAP = {
    # Extreme Mathematics books (HIGH priority)
    'extreme mathematics grade 9&10.pdf':
        'Extreme Mathematics: Grade 9 & 10, Ethiopia MOE',
    'extreme mathematics grade 11&12.pdf':
        'Extreme Mathematics: Grade 11 & 12, Ethiopia MOE',
    # Standard grade textbooks (MEDIUM priority)
    'grade9_math.pdf':
        'Ethiopian Grade 9 Mathematics Textbook',
    'grade10_math.pdf':
        'Ethiopian Grade 10 Mathematics Textbook',
    'grade11_math.pdf':
        'Ethiopian Grade 11 Mathematics Textbook',
    'grade12_math.pdf':
        'Ethiopian Grade 12 Mathematics Textbook',
}

BOOK_PRIORITY = {
    'extreme mathematics grade 9&10.pdf':    'high',
    'extreme mathematics grade 11&12.pdf':   'high',
    'grade9_math.pdf':                        'medium',
    'grade10_math.pdf':                       'medium',
    'grade11_math.pdf':                       'medium',
    'grade12_math.pdf':                       'medium',
}

EXAM_STYLE = {
    'extreme mathematics grade 9&10.pdf',
    'extreme mathematics grade 11&12.pdf',
}


def _get_book_meta(source_file: str):
    """Return (book_name, priority, book_type) for a source filename."""
    if not source_file:
        return ('Curriculum Source', 'medium', 'unknown')
    key = source_file.lower().strip()
    name = BOOK_NAME_MAP.get(key)
    priority = BOOK_PRIORITY.get(key, 'medium')
    btype = 'extreme' if source_file.lower().strip() in EXAM_STYLE else 'grade'
    return (name or source_file.replace('.pdf', '').replace('_', ' ').title(),
            priority, btype)


def _make_options(correct, distractors):
    """Build 4 options list with correct answer at a random position."""
    opts = distractors[:3]
    pos = random.randint(0, 3)
    opts.insert(pos, correct)
    return opts, pos


def _letter(idx):
    return ['A', 'B', 'C', 'D'][idx]


def _build_question_dict(question, options, correct_index, correct_letter,
                         explanation, topic, source_file='', source_page='',
                         difficulty='medium', book_type='grade',
                         question_style='standard'):
    """Standardize question dict with all required fields including source citation."""
    bn, _priority, _btype = _get_book_meta(source_file)
    if source_page:
        citation = f'{bn}, page {source_page}'
    else:
        citation = bn
    return {
        'question': question,
        'options': [str(o) for o in options],
        'correct_index': correct_index,
        'correct_letter': correct_letter,
        'explanation': explanation,
        'topic': topic,
        'difficulty': difficulty,
        'book_type': book_type,
        'question_style': question_style,
        'source_file': source_file,
        'source_page': source_page,
        'source_citation': citation,
    }

# ── Topic → Book Allocation ──────────────────────────────────────────────────
# Maps each topic key to the books that contain relevant content.
# Score = number of questions to draw from each source for a 7-question set:
#   3 from Extreme (exam-style) + 2 from grade book (foundational) + 2 mixed

TOPIC_BOOK_ALLOCATION = {
    # ── Grade 9–10 band ───────────────────────────────────────────────────────
    'algebra': {
        'priority_sources': ['extreme mathematics grade 9&10.pdf', 'grade9_math.pdf'],
        'grade_sources':     ['grade9_math.pdf', 'grade10_math.pdf'],
        'mix_sources':       ['extreme mathematics grade 9&10.pdf', 'grade10_math.pdf'],
    },
    'linear equations': {
        'priority_sources': ['extreme mathematics grade 9&10.pdf', 'grade9_math.pdf'],
        'grade_sources':     ['grade9_math.pdf', 'grade10_math.pdf'],
        'mix_sources':       ['extreme mathematics grade 9&10.pdf', 'grade9_math.pdf'],
    },
    'quadratic': {
        'priority_sources': ['extreme mathematics grade 9&10.pdf', 'grade10_math.pdf'],
        'grade_sources':     ['grade10_math.pdf', 'grade9_math.pdf'],
        'mix_sources':       ['extreme mathematics grade 9&10.pdf', 'grade10_math.pdf'],
    },
    'systems of equations': {
        'priority_sources': ['extreme mathematics grade 9&10.pdf', 'grade10_math.pdf'],
        'grade_sources':     ['grade9_math.pdf', 'grade10_math.pdf'],
        'mix_sources':       ['extreme mathematics grade 9&10.pdf', 'grade9_math.pdf'],
    },
    'sets': {
        'priority_sources': ['extreme mathematics grade 9&10.pdf', 'grade9_math.pdf'],
        'grade_sources':     ['grade9_math.pdf', 'grade10_math.pdf'],
        'mix_sources':       ['extreme mathematics grade 9&10.pdf', 'grade9_math.pdf'],
    },
    'coordinate geometry': {
        'priority_sources': ['extreme mathematics grade 9&10.pdf', 'grade10_math.pdf'],
        'grade_sources':     ['grade10_math.pdf', 'grade9_math.pdf'],
        'mix_sources':       ['extreme mathematics grade 9&10.pdf', 'grade10_math.pdf'],
    },
    # ── Grade 11–12 band ───────────────────────────────────────────────────────
    'limits': {
        'priority_sources': ['extreme mathematics grade 11&12.pdf', 'grade11_math.pdf'],
        'grade_sources':     ['grade11_math.pdf', 'grade12_math.pdf'],
        'mix_sources':       ['extreme mathematics grade 11&12.pdf', 'grade11_math.pdf'],
    },
    'integration': {
        'priority_sources': ['extreme mathematics grade 11&12.pdf', 'grade12_math.pdf'],
        'grade_sources':     ['grade12_math.pdf', 'grade11_math.pdf'],
        'mix_sources':       ['extreme mathematics grade 11&12.pdf', 'grade12_math.pdf'],
    },
    'differentiation': {
        'priority_sources': ['extreme mathematics grade 11&12.pdf', 'grade12_math.pdf'],
        'grade_sources':     ['grade11_math.pdf', 'grade12_math.pdf'],
        'mix_sources':       ['extreme mathematics grade 11&12.pdf', 'grade12_math.pdf'],
    },
    'matrix': {
        'priority_sources': ['extreme mathematics grade 11&12.pdf', 'grade11_math.pdf'],
        'grade_sources':     ['grade11_math.pdf', 'grade12_math.pdf'],
        'mix_sources':       ['extreme mathematics grade 11&12.pdf', 'grade11_math.pdf'],
    },
    'probability': {
        'priority_sources': ['extreme mathematics grade 11&12.pdf', 'grade11_math.pdf'],
        'grade_sources':     ['grade11_math.pdf', 'grade12_math.pdf'],
        'mix_sources':       ['extreme mathematics grade 11&12.pdf', 'grade11_math.pdf'],
    },
    'trigonometry': {
        'priority_sources': ['extreme mathematics grade 11&12.pdf', 'grade11_math.pdf'],
        'grade_sources':     ['grade11_math.pdf', 'grade12_math.pdf'],
        'mix_sources':       ['extreme mathematics grade 11&12.pdf', 'grade11_math.pdf'],
    },
    'statistics': {
        'priority_sources': ['extreme mathematics grade 11&12.pdf', 'grade12_math.pdf'],
        'grade_sources':     ['grade12_math.pdf', 'grade11_math.pdf'],
        'mix_sources':       ['extreme mathematics grade 11&12.pdf', 'grade12_math.pdf'],
    },
}


def get_book_allocation(topic_key: str) -> dict:
    """Return book allocation dict for a topic key (fallback to algebra)."""
    return TOPIC_BOOK_ALLOCATION.get(topic_key, TOPIC_BOOK_ALLOCATION['algebra'])


# ── ALGEBRA PATTERNS ──────────────────────────────────────────────────────────

def _algebra_linear(difficulty):
    """x + a = b  →  x = b - a"""
    a = random.randint(1, 20)
    b = random.randint(a + 1, a + 30)
    x = b - a
    question = f"Solve for x:  x + {a} = {b}"
    distractors = [x + random.choice([-2, -1, 1, 2, 3, -3]) for _ in range(5)]
    distractors = list({d for d in distractors if d != x})[:3]
    while len(distractors) < 3:
        distractors.append(x + random.randint(4, 10))
    opts, pos = _make_options(x, distractors)
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Subtract {a} from both sides: x = {b} - {a} = {x}",
        topic='algebra', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _algebra_multiply(difficulty):
    """ax = b  →  x = b/a"""
    a = random.randint(2, 12)
    x = random.randint(1, 15)
    b = a * x
    question = f"Solve for x:  {a}x = {b}"
    distractors = list({b + a, b - a, a + x, x + 1, x - 1} - {x})[:3]
    while len(distractors) < 3:
        distractors.append(x + random.randint(2, 8))
    opts, pos = _make_options(x, distractors[:3])
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Divide both sides by {a}: x = {b} / {a} = {x}",
        topic='algebra', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _algebra_quadratic(difficulty):
    """x² - (r1+r2)x + r1*r2 = 0  →  roots r1, r2"""
    r1 = random.randint(1, 8)
    r2 = random.randint(1, 8)
    b_coef = -(r1 + r2)
    c_coef = r1 * r2
    b_str = f"- {r1+r2}" if b_coef < 0 else f"+ {b_coef}"
    question = f"Find the roots of:  x\u00b2 {b_str}x + {c_coef} = 0"
    correct = f"x = {r1} and x = {r2}" if r1 != r2 else f"x = {r1} (double root)"
    wrong = [
        f"x = {r1+1} and x = {r2+1}",
        f"x = -{r1} and x = -{r2}",
        f"x = {r1*r2} and x = {r1+r2}",
    ]
    opts, pos = _make_options(correct, wrong)
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Factor: (x - {r1})(x - {r2}) = 0  \u2192  x = {r1} or x = {r2}",
        topic='quadratic', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _algebra_system(difficulty):
    """Simple 2-variable system: x+y=s, x-y=d"""
    x = random.randint(1, 10)
    y = random.randint(1, 10)
    s = x + y
    d = x - y
    d_str = f"- {abs(d)}" if d < 0 else f"+ {d}" if d > 0 else ""
    question = f"Solve the system:  x + y = {s}  and  x - y = {d}"
    correct = f"x = {x}, y = {y}"
    wrong = [
        f"x = {y}, y = {x}",
        f"x = {x+1}, y = {y-1}",
        f"x = {s}, y = {d}",
    ]
    opts, pos = _make_options(correct, wrong)
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Add equations: 2x = {s+d}  \u2192  x = {x};  then y = {s} - {x} = {y}",
        topic='systems of equations', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


# ── LIMITS / CALCULUS PATTERNS ─────────────────────────────────────────────────

def _limit_polynomial(difficulty):
    """lim(x→a) (x + c)"""
    a = random.randint(1, 10)
    c = random.randint(1, 10)
    result = a + c
    question = f"Evaluate:  lim(x \u2192 {a})  (x + {c})"
    distractors = list({result + 1, result - 1, a, c, result + 2} - {result})[:3]
    opts, pos = _make_options(result, distractors[:3])
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Direct substitution: {a} + {c} = {result}",
        topic='limits', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _limit_rational(difficulty):
    """lim(x→a) (x² - a²)/(x - a) = 2a"""
    a = random.randint(2, 8)
    result = 2 * a
    question = f"Evaluate:  lim(x \u2192 {a})  (x\u00b2 - {a**2}) / (x - {a})"
    distractors = list({result + 1, result - 1, a, a**2} - {result})[:3]
    opts, pos = _make_options(result, distractors[:3])
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Factor numerator: (x-{a})(x+{a})/(x-{a}) = x+{a}  \u2192  at x={a}: {a}+{a} = {result}",
        topic='limits', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _limit_infinity(difficulty):
    """lim(x→∞) (ax + b)/(cx + d) = a/c"""
    a = random.randint(1, 6)
    c = random.randint(1, 6)
    b = random.randint(1, 10)
    d = random.randint(1, 10)
    from fractions import Fraction
    frac = Fraction(a, c)
    result_str = str(frac)
    question = f"Evaluate:  lim(x \u2192 \u221e)  ({a}x + {b}) / ({c}x + {d})"
    wrong = [
        str(Fraction(a + 1, c)),
        str(Fraction(a, c + 1)),
        str(Fraction(b, d)),
    ]
    opts, pos = _make_options(result_str, wrong)
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Divide numerator and denominator by x: limit = {a}/{c} = {result_str}",
        topic='limits', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _limit_trig(difficulty):
    """lim(x→0) sin(ax)/ax = 1"""
    a = random.randint(2, 5)
    question = f"Evaluate:  lim(x \u2192 0)  sin({a}x) / ({a}x)"
    opts, pos = _make_options("1", ["0", str(a), f"1/{a}"])
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Using the standard limit lim(u\u21920) sin(u)/u = 1, with u = {a}x, the answer is 1",
        topic='limits', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _diff_power(difficulty):
    """d/dx (x^n) = n*x^(n-1)"""
    n = random.randint(1, 5)
    question = f"Find the derivative: d/dx (x^{n})"
    correct = f"{n}x^{n-1}" if n > 1 else "1"
    wrong = [
        f"{n+1}x^{n}",
        f"x^{n-1}",
        f"{n}x^{n}" if n > 1 else f"x^{n}",
    ]
    opts, pos = _make_options(correct, wrong[:3])
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Power rule for differentiation: d/dx (x^{n}) = {n}\u00b7x^{n-1} = {correct}",
        topic='differentiation', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _diff_constant(difficulty):
    """d/dx (c) = 0"""
    c = random.randint(5, 99)
    question = f"Find the derivative: d/dx ({c})"
    opts, pos = _make_options("0", [str(c), f"{c}x", f"1/{c}"])
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"The derivative of any constant is 0",
        topic='differentiation', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _diff_sum(difficulty):
    """d/dx (ax+b) = a"""
    a = random.randint(2, 8)
    b = random.randint(1, 12)
    question = f"Find the derivative: d/dx ({a}x + {b})"
    opts, pos = _make_options(str(a), [str(b), f"{a}{b}", str(a + b)])
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"d/dx ({a}x + {b}) = {a} + 0 = {a}",
        topic='differentiation', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


# ── INTEGRATION PATTERNS ─────────────────────────────────────────────────────────

def _integral_power(difficulty):
    """∫ ax^n dx = a x^(n+1)/(n+1) + C"""
    a = random.randint(1, 8)
    n = random.randint(1, 5)
    n1 = n + 1
    from fractions import Fraction
    coef = Fraction(a, n1)
    coef_str = str(coef)
    question = f"Find:  \u222b {a}x^{n} dx"
    correct = f"({coef_str})x^{n1} + C"
    wrong = [
        f"({a})x^{n1} + C",
        f"({coef_str})x^{n} + C",
        f"({a*n})x^{n-1} + C",
    ]
    opts, pos = _make_options(correct, wrong)
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Power rule: \u222b ax^n dx = a\u00b7x^(n+1)/(n+1) + C = {coef_str}x^{n1} + C",
        topic='integration', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _integral_definite(difficulty):
    """∫[0 to b] x dx = b²/2"""
    b = random.randint(2, 8)
    result = (b * b) // 2
    remainder = (b * b) % 2
    result_str = f"{b*b}/2" if remainder != 0 else str(result)
    question = f"Evaluate:  \u222b\u2080^{b} x dx"
    wrong = [str(b), str(b * b), str(result + 1)]
    opts, pos = _make_options(result_str, wrong)
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"\u222b x dx = x\u00b2/2  \u2192  [{b}\u00b2/2 - 0\u00b2/2] = {b*b}/2 = {result_str}",
        topic='integration', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _integral_constant(difficulty):
    """∫ a dx = ax + C"""
    a = random.randint(2, 12)
    question = f"Find:  \u222b {a} dx"
    opts, pos = _make_options(f"{a}x + C", [f"{a}x\u00b2/2 + C", f"{a+1}x + C", f"{a-1}x + C"])
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"\u222b constant dx = constant\u00b7x + C  \u2192  \u222b {a} dx = {a}x + C",
        topic='integration', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _integral_sum(difficulty):
    """∫ (ax + b) dx = ax²/2 + bx + C"""
    a = random.randint(2, 6)
    b = random.randint(1, 8)
    from fractions import Fraction
    coef = Fraction(a, 2)
    question = f"Find:  \u222b ({a}x + {b}) dx"
    correct = f"({coef})x\u00b2 + {b}x + C"
    wrong = [
        f"({a})x\u00b2 + {b}x + C",
        f"({coef})x\u00b2 + {b+1}x + C",
        f"{a} + C",
    ]
    opts, pos = _make_options(correct, wrong)
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Integrate term by term: {a}x\u00b2/2 + {b}x + C = {correct}",
        topic='integration', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


# ── PROBABILITY & STATISTICS PATTERNS ─────────────────────────────────────────

def _prob_dice(difficulty):
    """Probability of rolling a target value on one die = 1/6"""
    die_sides = 6
    target = random.randint(1, 6)
    question = f"A fair 6-sided die is rolled. What is the probability of rolling a {target}?"
    correct = f"1/{die_sides}"
    wrong = [
        f"{target}/{die_sides}",
        f"1/{target}",
        f"{(die_sides-target)}/{die_sides}",
    ]
    opts, pos = _make_options(correct, wrong)
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"There is 1 favorable outcome (rolling a {target}) out of {die_sides} total. P({target}) = 1/{die_sides}",
        topic='probability', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _prob_simple(difficulty):
    """P(A) = number of A outcomes / total possible outcomes"""
    total = random.randint(4, 12)
    favorable = random.randint(1, total - 1)
    import random as rnd
    items = ['red ball', 'blue ball', 'green ball', 'yellow ball', 'white ball', 'black ball',
             'heads', 'tails', 'boy', 'girl', 'ace', 'king', 'queen', 'jack']
    faces = rnd.sample(items, 2)
    question = (f"A bag contains {total} identical objects, of which {favorable} are {faces[0]}. "
                f"If one object is drawn at random, what is the probability it is a {faces[0]}?")
    correct = f"{favorable}/{total}"
    wrong = [
        f"{(total-favorable)}/{total}",
        f"{favorable}/{total-favorable}",
        f"{total}/{favorable}",
    ]
    opts, pos = _make_options(correct, wrong)
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"P({faces[0]}) = favorable / total = {favorable}/{total}",
        topic='probability', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _stats_mean(difficulty):
    """Mean = sum / count"""
    from fractions import Fraction
    count = random.randint(4, 8)
    values = [random.randint(5, 30) for _ in range(count)]
    total = sum(values)
    mean_val = Fraction(total, count)
    question = f"Find the mean of: {', '.join(str(v) for v in values)}"
    correct = str(mean_val) if mean_val.denominator != 1 else str(int(mean_val))
    wrong = [str(total), str(min(values)), str(max(values)), str(sorted(values)[count // 2])]
    opts, pos = _make_options(correct, wrong[:3])
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Mean = ({' + '.join(str(v) for v in values)}) / {count} = {total}/{count} = {correct}",
        topic='statistics', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _stats_median(difficulty):
    """Median: middle value when sorted"""
    count = random.choice([5, 7])
    values = sorted([random.randint(1, 20) for _ in range(count)])
    q_text = f"Find the median of: {', '.join(str(v) for v in values)}"
    if count == 5:
        median = values[2]
    else:
        median_str = f"({values[2]}+{values[3]})/2 = {(values[2]+values[3])/2}"
        correct_display = str((values[2]+values[3])/2)
        correct_display = correct_display if '.' in correct_display else str(int(correct_display))
        median = correct_display
    wrong = [str(values[0]), str(values[-1]), str(values[count // 2])]
    opts, pos = _make_options(str(median), list(set(wrong))[:3])
    return _build_question_dict(
        q_text, opts, pos, _letter(pos),
        f"Arrange in order: {values}. Median = {median} (the middle value)",
        topic='statistics', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


# ── TRIGONOMETRY PATTERNS ─────────────────────────────────────────────────────

def _trig_ratio(difficulty):
    """Basic trig: sin(theta), cos(theta) for common angles"""
    angles = [0, 30, 45, 60, 90]
    angle = random.choice(angles)
    trig_fn = random.choice(['sin', 'cos'])
    known = {
        (0, 'sin'): '0', (0, 'cos'): '1',
        (30, 'sin'): '1/2', (30, 'cos'): '\u221a3/2',
        (45, 'sin'): '\u221a2/2', (45, 'cos'): '\u221a2/2',
        (60, 'sin'): '\u221a3/2', (60, 'cos'): '1/2',
        (90, 'sin'): '1', (90, 'cos'): '0',
    }
    correct = known.get((angle, trig_fn), str(angle) + '/180')
    distractors_map = {
        '1/2': ['\u221a3/2', '0', '\u221a2/2'],
        '\u221a3/2': ['1/2', '1', '0'],
        '\u221a2/2': ['1', '1/2', '\u221a3/2'],
    }
    distractors = distractors_map.get(correct, ['0', '1', str(angle) + '/180'])
    distractors = list(dict.fromkeys(distractors))
    while len(distractors) < 3:
        distractors.append(f"{random.randint(1,4)}/{random.randint(2,8)}")
    opts, pos = _make_options(correct, distractors[:3])
    question = f"Find: {trig_fn}({angle}\u00b0)"
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Using the unit circle / special angles table: {trig_fn}({angle}\u00b0) = {correct}",
        topic='trigonometry', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _trig_convert(difficulty):
    """Convert degrees to radians: rad = degrees × π/180"""
    deg = random.choice([30, 45, 60, 90, 180])
    correct_rad = {30: '\u03c0/6', 45: '\u03c0/4', 60: '\u03c0/3', 90: '\u03c0/2', 180: '\u03c0'}
    rad = correct_rad[deg]
    wrong_map = {30: ['\u03c0/3', '\u03c0/2'], 45: ['\u03c0/2', '\u03c0'],
                 60: ['\u03c0/4', '\u03c0/6'], 90: ['\u03c0', '\u03c0/4'], 180: ['\u03c0/2', '2\u03c0']}
    question = f"Convert {deg}\u00b0 to radians (in terms of \u03c0)"
    wrong = wrong_map.get(deg, [])
    dist_all = wrong + ['0', str(deg), rad + '/2']
    dist_all = list(dict.fromkeys(dist_all))[:3]
    opts, pos = _make_options(rad, dist_all)
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"{deg}\u00b0 \u00d7 (\u03c0/180) = {deg}\u03c0/180 = {rad}",
        topic='trigonometry', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


# ── SETS PATTERNS ─────────────────────────────────────────────────────────────

def _sets_cardinality(difficulty):
    """n(U) = n(A) + n(B) - n(A∩B) + n(neither)"""
    total = random.randint(20, 60)
    a = random.randint(4, 16)
    b = random.randint(4, 16)
    neither = random.randint(2, 8)
    both = random.randint(1, min(a, b) - 2)
    union = total - neither
    a = union + both - b + random.randint(-2, 2)
    a = max(a, both + 1)
    b = max(b, both + 1)
    question = (f"A survey of {total} students found {a} study Math and {b} study Science. "
                f"{both} study both, and {neither} study neither. How many study Math ONLY?")
    math_only = a - both
    wrong = [both, b, total - a, a]
    wrong = list(set(wrong) - {math_only})[:3]
    while len(wrong) < 3:
        wrong.append(math_only + random.randint(1, 4))
    opts, pos = _make_options(math_only, wrong)
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Math only = n(Math) - n(Math\u2229Science) = {a} - {both} = {math_only}",
        topic='sets', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _sets_union(difficulty):
    """n(A∪B) = n(A) + n(B) - n(A∩B)"""
    a = random.randint(8, 20)
    b = random.randint(6, 18)
    both = random.randint(1, min(a, b) - 2)
    union = a + b - both
    question = f"In a class, {a} students play football and {b} play basketball. {both} play both sports. How many play at least one sport?"
    wrong = [a + b, a - both, b - both, a + b + both]
    wrong = list(set(wrong) - {union})[:3]
    while len(wrong) < 3:
        wrong.append(union + random.randint(1, 5))
    opts, pos = _make_options(union, wrong)
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"n(A\u222aB) = {a} + {b} - {both} = {union}",
        topic='sets', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


# ── COORDINATE GEOMETRY PATTERNS ───────────────────────────────────────────────

def _coord_distance(difficulty):
    """Distance between (x1,y1) and (x2,y2): sqrt((x2-x1)^2 + (y2-y1)^2)"""
    x1, y1 = random.randint(1, 9), random.randint(1, 9)
    x2, y2 = random.randint(1, 9), random.randint(1, 9)
    dx, dy = x2 - x1, y2 - y1
    dist_sq = dx**2 + dy**2
    question = f"Find the distance between A({x1},{y1}) and B({x2},{y2})"
    correct = f"\u221a{dist_sq}"
    wrong = [
        f"\u221a{dist_sq + 1}",
        f"\u221a{dist_sq - 1}" if dist_sq > 1 else f"\u221a{dist_sq + 2}",
        f"\u221a{dx**2 + dy if dy >= dx else dx + dy**2}",
        f"{dist_sq}",
    ]
    wrong = list(set(wrong) - {correct})[:3]
    while len(wrong) < 3:
        wrong.append(f"\u221a{random.randint(1,20)}")
    opts, pos = _make_options(correct, wrong)
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"d = \u221a(({x2}-{x1})\u00b2 + ({y2}-{y1})\u00b2) = \u221a({dx}\u00b2+{dy}\u00b2) = \u221a{dist_sq}",
        topic='coordinate geometry', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _coord_slope(difficulty):
    """Slope between (x1,y1) and (x2,y2): (y2-y1)/(x2-x1)"""
    x1, y1 = random.randint(1, 9), random.randint(1, 9)
    x2 = random.randint(1, 9)
    slope_num = random.randint(1, 8)
    y2 = y1 + slope_num * (x2 - x1)
    question = f"Find the slope of the line passing through ({x1},{y1}) and ({x2},{y2})"
    opts, pos = _make_options(str(slope_num), [str(slope_num + 1), str(slope_num - 1), str(y2 - y1), str(x2 - x1)])
    return _build_question_dict(
        question, opts, pos, _letter(pos),
        f"Slope = ({y2}-{y1})/({x2}-{x1}) = {y2-y1}/{x2-x1} = {slope_num}",
        topic='coordinate geometry', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


# ── MATRIX PATTERNS ───────────────────────────────────────────────────────────

def _matrix_add(difficulty):
    """[a;b] + [c;d] = [a+c; b+d]"""
    rows = 2
    a1 = [random.randint(1, 9) for _ in range(rows)]
    a2 = [random.randint(1, 9) for _ in range(rows)]
    result = [a1[i] + a2[i] for i in range(rows)]
    m1_str = '[' + '; '.join(str(x) for x in a1) + ']'
    m2_str = '[' + '; '.join(str(x) for x in a2) + ']'
    res_str = '[' + '; '.join(str(x) for x in result) + ']'
    correct = res_str
    wrong1 = '[' + '; '.join(str(a1[i]+a2[(i+1)%rows]) for i in range(rows)) + ']'
    wrong2 = '[' + '; '.join(str(a1[i]-a2[i]) for i in range(rows)) + ']'
    wrong3 = '[' + '; '.join(str(x) for x in a1) + ']'
    opts, pos = _make_options(correct, [wrong1, wrong2, wrong3])
    return _build_question_dict(
        f"Find: {m1_str} + {m2_str}", opts, pos, _letter(pos),
        f"Add corresponding elements: {m1_str} + {m2_str} = {res_str}",
        topic='matrix', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


def _matrix_mult(difficulty):
    """[a;b] x [c d] = [ac, ad; bc, bd]"""
    a = random.randint(1, 6)
    b = random.randint(1, 6)
    c = random.randint(1, 6)
    r1, r2 = a*c, a*(c+1)
    r3, r4 = b*c, b*(c+1)
    result_str = '[%d, %d; %d, %d]' % (r1, r2, r3, r4)
    correct = result_str
    wrong1 = '[%d, %d; %d, %d]' % (r1+1, r2+1, r3+1, r4+1)
    wrong2 = '[%d, %d; %d, %d]' % (r1, r2, a*c, b*c)
    wrong3 = '[%d; %d]' % (a*c, b*c)
    opts, pos = _make_options(correct, [wrong1, wrong2, wrong3])
    return _build_question_dict(
        f"Find: [{a};{b}] \u00d7 [{c}, {c+1}]", opts, pos, _letter(pos),
        f"[{a};{b}] \u00d7 [{c},{c+1}] = [{r1},{r2}; {r3},{r4}]",
        topic='matrix', difficulty=difficulty,
        source_file='', source_page='',
        book_type='grade', question_style='standard',
    )


# ── SHARED PATTERN REGISTRY ────────────────────────────────────────────────────

PATTERNS = {
    'algebra': [_algebra_linear, _algebra_multiply, _algebra_quadratic, _algebra_system],
    'limits': [_limit_polynomial, _limit_rational, _limit_infinity, _limit_trig],
    'integration': [_integral_power, _integral_definite, _integral_constant, _integral_sum],
    'differentiation': [_diff_power, _diff_constant, _diff_sum],
    'probability': [_prob_dice, _prob_simple],
    'statistics': [_stats_mean, _stats_median],
    'trigonometry': [_trig_ratio, _trig_convert],
    'sets': [_sets_cardinality, _sets_union],
    'coordinate geometry': [_coord_distance, _coord_slope],
    'matrix': [_matrix_add, _matrix_mult],
}

# Map common topic name variations to canonical keys
TOPIC_MAP = {
    # Algebra
    'algebra': 'algebra',
    'linear equations': 'algebra',
    'linear equation': 'algebra',
    'simultaneous equations': 'algebra',
    'quadratic': 'algebra',
    'quadratics': 'algebra',
    'factoring': 'algebra',
    'factorization': 'algebra',
    'systems of equations': 'algebra',
    'system of equations': 'algebra',
    # Limits / Calculus
    'limits': 'limits',
    'limit': 'limits',
    'calculus': 'limits',
    'continuity': 'limits',
    'l\'hospital': 'limits',
    'lhospital': 'limits',
    'polynomial limits': 'limits',
    'rational limits': 'limits',
    # Integration
    'integration': 'integration',
    'integral': 'integration',
    'integrals': 'integration',
    'integrating': 'integration',
    'definite integral': 'integration',
    'antiderivatives': 'integration',
    # Differentiation
    'differentiation': 'differentiation',
    'derivative': 'differentiation',
    'derivatives': 'differentiation',
    'chain rule': 'differentiation',
    'product rule': 'differentiation',
    # Probability
    'probability': 'probability',
    'probabilities': 'probability',
    'prob': 'probability',
    'chance': 'probability',
    'chances': 'probability',
    'random': 'probability',
    'random variable': 'probability',
    'outcomes': 'probability',
    'event': 'probability',
    'sample space': 'probability',
    'probability distributions': 'probability',
    # Statistics
    'statistics': 'statistics',
    'statistic': 'statistics',
    'mean': 'statistics',
    'median': 'statistics',
    'mode': 'statistics',
    'variance': 'statistics',
    'standard deviation': 'statistics',
    'average': 'statistics',
    'frequency': 'statistics',
    'normal distribution': 'statistics',
    # Trigonometry
    'trigonometry': 'trigonometry',
    'trig': 'trigonometry',
    'trigonometric': 'trigonometry',
    'trigonometric functions': 'trigonometry',
    'sin': 'trigonometry',
    'cos': 'trigonometry',
    'tan': 'trigonometry',
    'sine': 'trigonometry',
    'cosine': 'trigonometry',
    'radians': 'trigonometry',
    'radian': 'trigonometry',
    # Sets
    'sets': 'sets',
    'set theory': 'sets',
    'set': 'sets',
    'union': 'sets',
    'intersection': 'sets',
    'venn': 'sets',
    'subsets': 'sets',
    'cardinality': 'sets',
    'complement': 'sets',
    # Coordinate Geometry
    'coordinate geometry': 'coordinate geometry',
    'coordinate': 'coordinate geometry',
    'coordinates': 'coordinate geometry',
    'distance formula': 'coordinate geometry',
    'slope': 'coordinate geometry',
    'midpoint': 'coordinate geometry',
    'line equation': 'coordinate geometry',
    # Matrix
    'matrix': 'matrix',
    'matrices': 'matrix',
    'matrix algebra': 'matrix',
    'matrix addition': 'matrix',
    'matrix multiplication': 'matrix',
}


def _resolve_topic_key(raw: str) -> str:
    """Normalise a topic name to a canonical PATTERNS key."""
    raw = raw.strip()
    lookup = ' '.join(raw.lower().split())
    key = TOPIC_MAP.get(lookup)
    if key is None:
        for word in lookup.split():
            if len(word) > 2:
                key = TOPIC_MAP.get(word)
                if key:
                    break
    if key is None:
        for k in TOPIC_MAP:
            if k and len(k) > 2 and k in lookup:
                key = TOPIC_MAP[k]
                break
    if key is None:
        for k in TOPIC_MAP:
            for word in lookup.split():
                if len(word) > 2 and word in k:
                    key = TOPIC_MAP[k]
                    break
            if key:
                break
    if key is None:
        key = 'algebra'
    return key


# ── Priority Search Helpers ────────────────────────────────────────────────────

SOURCE_ORDER = {
    # Key = canonical source filename lowercased; value = sort weight (lower = higher priority)
    'extreme mathematics grade 9&10.pdf':    1,
    'extreme mathematics grade 11&12.pdf':   2,
    'grade9_math.pdf':                       3,
    'grade10_math.pdf':                      4,
    'grade11_math.pdf':                      5,
    'grade12_math.pdf':                      6,
}


def rank_hits_by_priority(hits: list) -> list:
    """Sort hit list so that Extreme Mathematics books appear first, then grade books."""
    seen_order = []
    seen_keys = set()
    for h in hits:
        sf = (h.get('source_file') or h.get('source') or '').lower().strip()
        weight = SOURCE_ORDER.get(sf, 99)
        if sf not in seen_keys:
            seen_keys.add(sf)
            seen_order.append((weight, h))
    seen_order.sort(key=lambda x: x[0])
    return [h for _, h in seen_order]


def generate_questions(
    topic_name: str,
    count: int = 4,
    difficulty: str = 'medium',
    source_files: list = None,
    source_pages: list = None,
) -> list:
    """
    Generate `count` multiple-choice questions for the given topic.
    Uses priority ordering: 3 from Extreme books (exam-style), remainder from grade books.

    Args:
        topic_name: topic string
        count: number of questions to generate
        difficulty: 'easy', 'medium', or 'hard'
        source_files: optional list of source filenames (from FAISS hits) for citation
        source_pages: optional list of page numbers matching source_files

    Returns:
        List of question dicts with question, options, correct_index, correct_letter,
        explanation, topic, difficulty, source_file, source_page, source_citation
    """
    raw = topic_name.strip()
    lookup = ' '.join(raw.lower().split())

    # Resolve canonical topic key
    key = _resolve_topic_key(lookup)
    pattern_fns = PATTERNS.get(key) or PATTERNS['algebra']

    allocation = TOPIC_BOOK_ALLOCATION.get(key, TOPIC_BOOK_ALLOCATION['algebra'])
    prio_files = allocation['priority_sources']   # Extreme books
    grade_files = allocation['grade_sources']      # Grade books

    # Build available sources from provided source_files / source_pages, falling back
    # to configured allocation
    avail = {}
    if source_files:
        for i, sf in enumerate(source_files[:count * 2]):
            sf_lower = sf.lower().strip()
            if sf_lower not in avail:
                avail[sf_lower] = source_pages[i] if source_pages and i < len(source_pages) else ''
    else:
        for sf in prio_files + grade_files:
            avail[sf.lower().strip()] = ''

    questions = []
    used = set()
    attempts = 0

    # ── Phase 1: First 3 questions from Extreme (priority) books ──────────────
    extreme_count = 0
    max_extreme = min(3, count)
    while extreme_count < max_extreme and attempts < count * 30:
        attempts += 1
        fn = random.choice(pattern_fns)
        q = fn(difficulty)
        sig = q['question'][:40]
        if sig in used:
            continue
        used.add(sig)
        # Assign to an extreme source if available
        for sf in prio_files:
            sf_key = sf.lower()
            if sf_key in avail:
                _, priority, btype = _get_book_meta(sf)
                q['book_type'] = btype
                q['source_file'] = sf
                q['source_page'] = avail[sf_key] or ''
                bn, _, _ = _get_book_meta(sf)
                pg = avail[sf_key] or ''
                q['source_citation'] = f'{bn}, page {pg}' if pg else bn
                q['question_style'] = 'exam-style'
                extreme_count += 1
                break
        questions.append(q)

    # ── Phase 2: Next 2 from grade book (foundational) ────────────────────────
    grade_count = 0
    max_grade = min(2, count - len(questions))
    while grade_count < max_grade and attempts < count * 30:
        attempts += 1
        fn = random.choice(pattern_fns)
        q = fn(difficulty)
        sig = q['question'][:40]
        if sig in used:
            continue
        used.add(sig)
        for sf in grade_files:
            sf_key = sf.lower()
            if sf_key in avail:
                _, priority, btype = _get_book_meta(sf)
                q['book_type'] = btype
                q['source_file'] = sf
                q['source_page'] = avail[sf_key] or ''
                bn, _, _ = _get_book_meta(sf)
                pg = avail[sf_key] or ''
                q['source_citation'] = f'{bn}, page {pg}' if pg else bn
                q['question_style'] = 'foundational'
                grade_count += 1
                break
        questions.append(q)

    # ── Phase 3: Fill remainder mixing both styles ─────────────────────────────
    remaining = count - len(questions)
    mix_attempts = 0
    while len(questions) < count and mix_attempts < remaining * 20:
        mix_attempts += 1
        fn = random.choice(pattern_fns)
        q = fn(difficulty)
        sig = q['question'][:40]
        if sig in used:
            continue
        used.add(sig)
        # Prefer sources from mix list (which includes all relevant books)
        for sf in allocation['mix_sources']:
            sf_key = sf.lower().strip()
            if sf_key in avail:
                _, priority, btype = _get_book_meta(sf)
                q['book_type'] = btype
                q['source_file'] = sf
                q['source_page'] = avail[sf_key] or ''
                bn, _, _ = _get_book_meta(sf)
                pg = avail[sf_key] or ''
                q['source_citation'] = f'{bn}, page {pg}' if pg else bn
                q['question_style'] = 'mixed'
                break
        q['topic'] = topic_name
        questions.append(q)

    return questions[:count]
