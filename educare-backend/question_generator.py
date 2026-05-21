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


# ── LIMITS / CALCULUS PATTERNS ────────────────────────────────────────────────

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


def _diff_power(difficulty):
    """d/dx (x^n) = n·x^(n-1)"""
    n = random.randint(1, 5)
    question = f"Find the derivative: d/dx (x^{n})"
    correct = f"{n}x^{n-1}" if n > 1 else "1"
    wrong = [
        f"{n+1}x^{n}",
        f"x^{n-1}",
        f"{n}x^{n}" if n > 1 else f"x^{n}",
    ]
    opts, pos = _make_options(correct, wrong[:3])
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Power rule for differentiation: d/dx (x^{n}) = {n}·x^{n-1} = {correct}"
    }


def _diff_constant(difficulty):
    """d/dx (c) = 0"""
    c = random.randint(5, 99)
    question = f"Find the derivative: d/dx ({c})"
    correct = "0"
    wrong = [str(c), f"{c}x", f"1/{c}"]
    opts, pos = _make_options(correct, wrong)
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"The derivative of any constant is 0"
    }


def _diff_sum(difficulty):
    """d/dx (ax+b) = a"""
    a = random.randint(2, 8)
    b = random.randint(1, 12)
    question = f"Find the derivative: d/dx ({a}x + {b})"
    correct = str(a)
    wrong = [str(b), f"{a}{b}", str(a + b)]
    opts, pos = _make_options(correct, wrong)
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"d/dx ({a}x + {b}) = {a} + 0 = {a}"
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
        "explanation": f"Integrate term by term: {a}x²/2 + {b}x + C = ({a}/{2})x² + {b}x + C = {coef}x² + {b}x + C"
    }


# ── PROBABILITY & STATISTICS PATTERNS ─────────────────────────────────────────

def _prob_dice(difficulty):
    """Probability of rolling a target value on one die = 1/targets"""
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
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"There is 1 favorable outcome (rolling a {target}) out of {die_sides} total outcomes. P({target}) = 1/{die_sides}"
    }


def _prob_simple(difficulty):
    """P(A) = number of A outcomes / total possible outcomes"""
    total = random.randint(4, 12)
    favorable = random.randint(1, total - 1)
    # Build scenario
    import random as rnd
    items = ['red ball', 'blue ball', 'green ball', 'yellow ball', 'white ball', 'black ball',
             'heads', 'tails', 'boy', 'girl', 'ace', 'king', 'queen', 'jack']
    faces = rnd.sample(items, 2)
    question = f"A bag contains {total} identical objects, of which {favorable} are {faces[0]}. If one object is drawn at random, what is the probability it is a {faces[0]}?"
    correct = f"{favorable}/{total}"
    wrong = [
        f"{(total-favorable)}/{total}",
        f"{favorable}/{total-favorable}",
        f"{total}/{favorable}",
    ]
    opts, pos = _make_options(correct, wrong)
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"P({faces[0]}) = favorable / total = {favorable}/{total}"
    }


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
    return {
        "question": question,
        "options": [str(o) for o in opts],
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Mean = ({' + '.join(str(v) for v in values)}) / {count} = {total}/{count} = {correct}"
    }


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
    return {
        "question": q_text,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Arrange in order: {values}. Median = {median} (the middle value)"
    }


# ── TRIGONOMETRY PATTERNS ─────────────────────────────────────────────────────

def _trig_ratio(difficulty):
    """Basic trig: sin(θ), cos(θ) for common angles"""
    angles = [0, 30, 45, 60, 90]
    angle = random.choice(angles)
    trig_fn = random.choice(['sin', 'cos'])
    known = {
        (0,'sin'): '0', (0,'cos'): '1',
        (30,'sin'): '1/2', (30,'cos'): '√3/2',
        (45,'sin'): '√2/2', (45,'cos'): '√2/2',
        (60,'sin'): '√3/2', (60,'cos'): '1/2',
        (90,'sin'): '1', (90,'cos'): '0',
    }
    correct = known.get((angle, trig_fn), str(angle)+'/180')
    distractors_map = {
        '1/2': ['√3/2', '0', '√2/2'],
        '√3/2': ['1/2', '1', '0'],
        '√2/2': ['1', '1/2', '√3/2'],
    }
    distractors = distractors_map.get(correct, ['0','1', str(angle)+'/180'])
    # Deduplicate (correct may partially overlap with distractors for symmetric angles)
    distractors = list(dict.fromkeys(distractors))
    while len(distractors) < 3:
        distractors.append(f"{random.randint(1,4)}/{random.randint(2,8)}")
    opts, pos = _make_options(correct, distractors[:3])
    question = f"Find: {trig_fn}({angle}°)"
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Using the unit circle / special angles table: {trig_fn}({angle}°) = {correct}"
    }


def _trig_convert(difficulty):
    """Convert degrees to radians: rad = degrees × π/180"""
    deg = random.choice([30, 45, 60, 90, 180])
    correct_rad = {30: 'π/6', 45: 'π/4', 60: 'π/3', 90: 'π/2', 180: 'π'}
    rad = correct_rad[deg]
    wrong_map = {30: ['π/3', 'π/2'], 45: ['π/2', 'π'], 60: ['π/4', 'π/6'], 90: ['π', 'π/4'], 180: ['π/2', '2π']}
    question = f"Convert {deg}° to radians (in terms of π)"
    wrong = wrong_map.get(deg, [])
    dist_all = wrong + ['0', str(deg), rad + '/2']
    dist_all = list(dict.fromkeys(dist_all))[:3]
    opts, pos = _make_options(rad, dist_all)
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"{deg}° × (π/180) = {deg}π/180 = {rad}"
    }


# ── SETS PATTERNS ─────────────────────────────────────────────────────────────

def _sets_cardinality(difficulty):
    """n(U) = n(A) + n(B) - n(A∩B) + n(neither)"""
    total = random.randint(20, 60)
    a = random.randint(4, 16)
    b = random.randint(4, 16)
    neither = random.randint(2, 8)
    both = random.randint(1, min(a, b) - 2)
    # Recalculate a to be consistent
    union = total - neither
    a = union + both - b + random.randint(-2, 2)
    a = max(a, both + 1)
    b = max(b, both + 1)
    question = f"A survey of {total} students found {a} study Math and {b} study Science. {both} study both, and {neither} study neither. How many study Math ONLY?"
    math_only = a - both
    wrong = [both, b, total - a, a]
    wrong = list(set(wrong) - {math_only})[:3]
    while len(wrong) < 3:
        wrong.append(math_only + random.randint(1, 4))
    opts, pos = _make_options(math_only, wrong)
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Math only = n(Math) - n(Math∩Science) = {a} - {both} = {math_only}"
    }


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
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"n(A∪B) = {a} + {b} - {both} = {union}"
    }


# ── COORDINATE GEOMETRY PATTERNS ──────────────────────────────────────────────

def _coord_distance(difficulty):
    """Distance between (x1,y1) and (x2,y2): √((x2-x1)²+(y2-y1)²)"""
    x1, y1 = random.randint(1, 9), random.randint(1, 9)
    x2, y2 = random.randint(1, 9), random.randint(1, 9)
    dx, dy = x2 - x1, y2 - y1
    dist_sq = dx**2 + dy**2
    question = f"Find the distance between A({x1},{y1}) and B({x2},{y2})"
    correct = f"√{dist_sq}"
    # Simplify roots we know from Pythagoras: 5->√5, 13->√13, etc.
    wrong = [
        f"√{dist_sq + 1}",
        f"√{dist_sq - 1}" if dist_sq > 1 else f"√{dist_sq + 2}",
        f"√{dx**2 + dy if dy >= dx else dx + dy**2}",
        f"{dist_sq}",
    ]
    wrong = list(set(wrong) - {correct})[:3]
    while len(wrong) < 3:
        wrong.append(f"√{random.randint(1,20)}")
    opts, pos = _make_options(correct, wrong)
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"d = √(({x2}-{x1})² + ({y2}-{y1})²) = √({dx}²+{dy}²) = √{dist_sq}"
    }


def _coord_slope(difficulty):
    """Slope between (x1,y1) and (x2,y2): (y2-y1)/(x2-x1)"""
    x1, y1 = random.randint(1, 9), random.randint(1, 9)
    x2 = random.randint(1, 9)
    slope_num = random.randint(1, 8)
    y2 = y1 + slope_num * (x2 - x1)
    question = f"Find the slope of the line passing through ({x1},{y1}) and ({x2},{y2})"
    correct = str(slope_num)
    wrong = [str(slope_num + 1), str(slope_num - 1), str(y2 - y1), str(x2 - x1)]
    wrong = list(set(wrong) - {correct})[:3]
    opts, pos = _make_options(correct, wrong)
    return {
        "question": question,
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Slope = ({y2}-{y1})/({x2}-{x1}) = {y2-y1}/{x2-x1} = {slope_num}"
    }


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
    return {
        "question": f"Find: {m1_str} + {m2_str}",
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"Add corresponding elements: {m1_str} + {m2_str} = {res_str}"
    }


def _matrix_mult(difficulty):
    """[a;b] × [c d] = [ac, ad; bc, bd]"""
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
    return {
        "question": f"Find: [{a};{b}] × [{c}, {c+1}]",
        "options": opts,
        "correct_index": pos,
        "correct_letter": _letter(pos),
        "explanation": f"[{a};{b}] × [{c},{c+1}] = [{a}×{c},{a}×{c+1}; {b}×{c},{b}×{c+1}] = [{r1},{r2};{r3},{r4}]"
    }


# ── SHARED UPPER SECTION ──────────────────────────────────────────────────────

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
    'quadratic': 'algebra',
    'quadratics': 'algebra',
    'factoring': 'algebra',
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
    # General / fall-through — no plot/sequence entries
}


def generate_questions(topic_name: str, count: int = 4, difficulty: str = 'medium') -> list:
    """
    Generate `count` multiple-choice questions for the given topic.
    Returns a list of question dicts with keys:
      question, options (list of 4 str), correct_index, correct_letter, explanation
    """
    # Normalise: strip whitespace but keep original casing for display
    raw = topic_name.strip()
    # Build a clean lookup string: lowercase, collapse internal spaces
    lookup = ' '.join(raw.lower().split())

    # 1. Exact canonical match
    key = TOPIC_MAP.get(lookup)
    # 2. Try each word individually
    if key is None:
        for word in lookup.split():
            if len(word) > 2:
                key = TOPIC_MAP.get(word)
                if key:
                    break
    # 3. Substring match: any map key is contained in the clean string
    if key is None:
        for k in TOPIC_MAP:
            if k and len(k) > 2 and k in lookup:
                key = TOPIC_MAP[k]
                break
    # 4. Reverse: any word in lookup is contained in a map key
    if key is None:
        for k in TOPIC_MAP:
            for word in lookup.split():
                if len(word) > 2 and word in k:
                    key = TOPIC_MAP[k]
                    break
            if key:
                break

    if key is None:
        key = 'algebra'   # last-resort fallback

    pattern_fns = PATTERNS.get(key) or PATTERNS['algebra']
    questions = []
    used = set()
    attempts = 0
    while len(questions) < count and attempts < count * 20:
        attempts += 1
        fn = random.choice(pattern_fns)
        q = fn(difficulty)
        sig = q['question'][:40]
        if sig not in used:
            used.add(sig)
            q['topic'] = topic_name
            questions.append(q)
    return questions
