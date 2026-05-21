"""Quick sanity-check: verify topic matching works correctly."""
import sys
sys.path.insert(0, '.')
from question_generator import generate_questions, TOPIC_MAP, PATTERNS

topics = [
    'Probability', 'Statistics', 'Trigonometry', 'Sets',
    'Linear Equations', 'Quadratic Equations', 'Limits',
    'Integration', 'Derivatives', 'basic probability',
    'Trig Functions', 'Matrix', 'Coordinate Geometry',
    'Random Variable', 'Normal Distribution', 'coordinate geometry',
]

errors = []
for t in topics:
    raw = t.strip()
    lookup = ' '.join(raw.lower().split())

    # Replicate generate_questions matching logic
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

    pts = PATTERNS.get(key) if key else None
    n = len(pts) if pts else 0
    status = 'OK' if (key and key in PATTERNS) else 'WARN'
    try:
        qs = generate_questions(t, count=1, difficulty='medium')
        sample = qs[0]['question'][:50] if qs else 'NONE'
    except Exception as e:
        sample = 'ERROR: ' + str(e)
        errors.append(t)
    print("  %-35s -> key=%-20s (%d patterns) [%s] | %s" % (t, str(key), n, status, sample))

print()
if errors:
    print("ERRORS:", errors)
else:
    print("All topics OK")
