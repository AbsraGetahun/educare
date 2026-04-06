"""
Part 1: Question Pattern Generator
Generates math questions using patterns and random numbers. No AI or external APIs.
"""
import random
import math


def _make_options(correct, distractors):
    """Build 4 options list with correct answer at a random position."""
    opts = distractors[:3]
    pos = random.randint(0, 3)
    opts.insert(pos, correct)
    return opts, pos  # pos = index of correct answer (0=A,1=B,2=C,3=D)


def _letter(idx):
    return ['A', 'B', 'C', 'D'][idx]


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
    return {
        "question": question,
        "options": [str(o) for o in opts],
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Subtract {a} from both sides: x = {b} - {a} = {x}"
    }


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
    return {
        "question": question,
        "options": [str(o) for o in opts],
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Divide both sides by {a}: x = {b} / {a} = {x}"
    }


def _algebra_quadratic(difficulty):
    """x² - (r1+r2)x + r1*r2 = 0  →  roots r1, r2"""
    r1 = random.randint(1, 8)
    r2 = random.randint(1, 8)
    b_coef = -(r1 + r2)
    c_coef = r1 * r2
    b_str = f"- {r1+r2}" if b_coef < 0 else f"+ {b_coef}"
    question = f"Find the roots of:  x² {b_str}x + {c_coef} = 0"
    correct = f"x = {r1} and x = {r2}" if r1 != r2 else f"x = {r1} (double root)"
    wrong = [
        f"x = {r1+1} and x = {r2+1}",
        f"x = -{r1} and x = -{r2}",
        f"x = {r1*r2} and x = {r1+r2}",
    ]
    opts, pos = _make_options(correct, wrong)
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Factor: (x - {r1})(x - {r2}) = 0  →  x = {r1} or x = {r2}"
    }


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
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Add equations: 2x = {s+d}  →  x = {x};  then y = {s} - {x} = {y}"
    }


# ── LIMITS PATTERNS ───────────────────────────────────────────────────────────

def _limit_polynomial(difficulty):
    """lim(x→a) (x + c)"""
    a = random.randint(1, 10)
    c = random.randint(1, 10)
    result = a + c
    question = f"Evaluate:  lim(x → {a})  (x + {c})"
    distractors = list({result + 1, result - 1, a, c, result + 2} - {result})[:3]
    opts, pos = _make_options(result, distractors[:3])
    return {
        "question": question,
        "options": [str(o) for o in opts],
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Direct substitution: {a} + {c} = {result}"
    }


def _limit_rational(difficulty):
    """lim(x→a) (x² - a²)/(x - a) = 2a"""
    a = random.randint(2, 8)
    result = 2 * a
    question = f"Evaluate:  lim(x → {a})  (x² - {a**2}) / (x - {a})"
    distractors = list({result + 1, result - 1, a, a**2} - {result})[:3]
    opts, pos = _make_options(result, distractors[:3])
    return {
        "question": question,
        "options": [str(o) for o in opts],
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Factor numerator: (x-{a})(x+{a})/(x-{a}) = x+{a}  →  at x={a}: {a}+{a} = {result}"
    }


def _limit_infinity(difficulty):
    """lim(x→∞) (ax + b)/(cx + d) = a/c"""
    a = random.randint(1, 6)
    c = random.randint(1, 6)
    b = random.randint(1, 10)
    d = random.randint(1, 10)
    from fractions import Fraction
    frac = Fraction(a, c)
    result_str = str(frac)
    question = f"Evaluate:  lim(x → ∞)  ({a}x + {b}) / ({c}x + {d})"
    wrong = [
        str(Fraction(a + 1, c)),
        str(Fraction(a, c + 1)),
        str(Fraction(b, d)),
    ]
    opts, pos = _make_options(result_str, wrong)
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Divide numerator and denominator by x: limit = {a}/{c} = {result_str}"
    }


def _limit_trig(difficulty):
    """lim(x→0) sin(ax)/ax = 1"""
    a = random.randint(2, 5)
    question = f"Evaluate:  lim(x → 0)  sin({a}x) / ({a}x)"
    opts, pos = _make_options("1", ["0", str(a), f"1/{a}"])
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Using the standard limit lim(u→0) sin(u)/u = 1, with u = {a}x, the answer is 1"
    }


# ── INTEGRATION PATTERNS ──────────────────────────────────────────────────────

def _integral_power(difficulty):
    """∫ ax^n dx = ax^(n+1)/(n+1) + C"""
    a = random.randint(1, 8)
    n = random.randint(1, 5)
    n1 = n + 1
    from fractions import Fraction
    coef = Fraction(a, n1)
    coef_str = str(coef)
    question = f"Find:  ∫ {a}x^{n} dx"
    correct = f"({coef_str})x^{n1} + C"
    wrong = [
        f"({a})x^{n1} + C",
        f"({coef_str})x^{n} + C",
        f"({a*n})x^{n-1} + C",
    ]
    opts, pos = _make_options(correct, wrong)
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Power rule: ∫ ax^n dx = a·x^(n+1)/(n+1) + C = ({a}/{n1})x^{n1} + C = {coef_str}x^{n1} + C"
    }


def _integral_definite(difficulty):
    """∫[0 to b] x dx = b²/2"""
    b = random.randint(2, 8)
    result = (b * b) // 2
    remainder = (b * b) % 2
    result_str = f"{b*b}/2" if remainder != 0 else str(result)
    question = f"Evaluate:  ∫₀^{b} x dx"
    wrong = [str(b), str(b * b), str(result + 1)]
    opts, pos = _make_options(result_str, wrong)
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"∫ x dx = x²/2  →  [{b}²/2 - 0²/2] = {b*b}/2 = {result_str}"
    }


def _integral_constant(difficulty):
    """∫ a dx = ax + C"""
    a = random.randint(2, 12)
    question = f"Find:  ∫ {a} dx"
    correct = f"{a}x + C"
    wrong = [f"{a}x²/2 + C", f"{a+1}x + C", f"{a-1}x + C"]
    opts, pos = _make_options(correct, wrong)
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"∫ constant dx = constant·x + C  →  ∫ {a} dx = {a}x + C"
    }


def _integral_sum(difficulty):
    """∫ (ax + b) dx = ax²/2 + bx + C"""
    a = random.randint(2, 6)
    b = random.randint(1, 8)
    from fractions import Fraction
    coef = Fraction(a, 2)
    question = f"Find:  ∫ ({a}x + {b}) dx"
    correct = f"({coef})x² + {b}x + C"
    wrong = [
        f"({a})x² + {b}x + C",
        f"({coef})x² + {b+1}x + C",
        f"{a} + C",
    ]
    opts, pos = _make_options(correct, wrong)
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Integrate term by term: {a}x²/2 + {b}x + C = {coef}x² + {b}x + C"
    }


# ── TOPIC DISPATCH ────────────────────────────────────────────────────────────

PATTERNS = {
    'algebra': [_algebra_linear, _algebra_multiply, _algebra_quadratic, _algebra_system],
    'limits': [_limit_polynomial, _limit_rational, _limit_infinity, _limit_trig],
    'integration': [_integral_power, _integral_definite, _integral_constant, _integral_sum],
}

# Map common topic name variations to canonical keys
TOPIC_MAP = {
    'algebra': 'algebra',
    'limits': 'limits',
    'limit': 'limits',
    'calculus': 'limits',
    'integration': 'integration',
    'integral': 'integration',
    'integrals': 'integration',
    'differentiation': 'algebra',  # fallback
}


def generate_questions(topic_name: str, count: int = 4, difficulty: str = 'medium') -> list:
    """
    Generate `count` multiple-choice questions for the given topic.
    Returns a list of question dicts with keys:
      question, options (list of 4 str), correct_index, correct_letter, explanation
    """
    key = TOPIC_MAP.get(topic_name.lower().strip())
    if key is None:
        # Try partial match
        for k in TOPIC_MAP:
            if k in topic_name.lower():
                key = TOPIC_MAP[k]
                break
    if key is None:
        key = 'algebra'  # default fallback

    pattern_fns = PATTERNS[key]
    questions = []
    used = set()
    attempts = 0
    while len(questions) < count and attempts < count * 10:
        attempts += 1
        fn = random.choice(pattern_fns)
        q = fn(difficulty)
        sig = q['question'][:40]
        if sig not in used:
            used.add(sig)
            q['topic'] = topic_name
            questions.append(q)
    return questions
