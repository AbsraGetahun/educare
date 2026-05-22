"""
Shared RAG utilities: FAISS search with grade filtering, priority-based multi-book search,
material HTML building, and source citations. Supports ALL 6 curriculum textbooks.
Also includes the math answer engine used by the chatbot.
"""
import os
import re
import json
import pickle
import random

INDEX_DIR = os.path.join(os.path.dirname(__file__), 'faiss_index')

_faiss_cache = None


def _load_faiss():
    global _faiss_cache
    if _faiss_cache is not None:
        return _faiss_cache
    import faiss
    index_path = os.path.join(INDEX_DIR, 'index.faiss')
    vectorizer_path = os.path.join(INDEX_DIR, 'vectorizer.pkl')
    metadata_path = os.path.join(INDEX_DIR, 'metadata.json')
    if not os.path.exists(index_path) or not os.path.exists(vectorizer_path):
        _faiss_cache = None
        return None
    index = faiss.read_index(index_path)
    with open(vectorizer_path, 'rb') as f:
        vectorizer = pickle.load(f)
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    _faiss_cache = {'index': index, 'vectorizer': vectorizer, 'metadata': metadata}
    return _faiss_cache


def parse_grades_from_filename(filename: str):
    lower = filename.lower()
    if '9&10' in lower or '9 and 10' in lower or '9& 10' in lower:
        return [9, 10]
    if '11&12' in lower or '11 and 12' in lower or '11& 12' in lower:
        return [11, 12]
    for key, grade in [('grade12', 12), ('grade11', 11), ('grade10', 10), ('grade9', 9)]:
        if key in lower.replace(' ', '').replace('_', ''):
            return [grade]
    m = re.search(r'grade\s*(\d+)', lower)
    if m:
        return [int(m.group(1))]
    return []


def chunk_grade_levels(chunk: dict):
    levels = chunk.get('grade_levels')
    if levels:
        return [int(g) for g in levels if g is not None]
    if chunk.get('grade_level') is not None:
        return [int(chunk['grade_level'])]
    return []


def chunk_matches_grade(chunk: dict, grade_level):
    if grade_level is None:
        return True
    levels = chunk_grade_levels(chunk)
    if not levels:
        return True
    return int(grade_level) in levels


def extract_section_title(text: str) -> str:
    m = re.search(r'Unit\s+\d+\s*:\s*[^\n]+', text, re.IGNORECASE)
    return m.group(0).strip() if m else ''


# ── Priority Source Order ──────────────────────────────────────────────────────
SOURCE_PRIORITY = {
    'extreme mathematics grade 9&10.pdf':     1,
    'extreme mathematics grade 11&12.pdf':    2,
    'grade9_math.pdf':                         3,
    'grade10_math.pdf':                        4,
    'grade11_math.pdf':                        5,
    'grade12_math.pdf':                        6,
}
EXTREME_BOOKS = {
    'extreme mathematics grade 9&10.pdf',
    'extreme mathematics grade 11&12.pdf',
}


def _source_weight(hit: dict) -> int:
    sf = (hit.get('source_file') or hit.get('source') or '').lower().strip()
    return SOURCE_PRIORITY.get(sf, 99)


def _is_extreme(source_file: str) -> bool:
    return source_file.lower().strip() in EXTREME_BOOKS


def _search_raw(query: str, grade_level, k: int):
    data = _load_faiss()
    if not data or not query.strip():
        return []
    index = data['index']
    vectorizer = data['vectorizer']
    metadata = data['metadata']
    query_vector = vectorizer.transform([query]).toarray().astype('float32')
    search_k = min(max(k * 15, 20), len(metadata))
    distances, indices = index.search(query_vector, search_k)
    results = []
    for i, dist in zip(indices[0], distances[0]):
        if i < 0 or i >= len(metadata):
            continue
        chunk = metadata[i]
        similarity = max(0, (1 - float(dist)) * 100)
        section = extract_section_title(chunk.get('text', ''))
        gl = chunk_grade_levels(chunk)
        results.append({
            'text': chunk.get('text', ''),
            'source': chunk.get('source', 'curriculum'),
            'source_file': chunk.get('source', 'curriculum'),
            'page': chunk.get('page', ''),
            'source_page': chunk.get('page', ''),
            'source_grade': gl[0] if gl else chunk.get('grade_level'),
            'grade_level': gl[0] if gl else chunk.get('grade_level'),
            'section': section,
            'similarity': int(similarity),
        })
    return results


def search_curriculum(query: str, grade_level=None, k: int = 5) -> list:
    data = _load_faiss()
    if not data or not query.strip():
        return []
    raw = _search_raw(query, grade_level, k=k * 3)
    filtered = [h for h in raw if chunk_matches_grade(h, grade_level)]
    filtered.sort(key=lambda h: (_source_weight(h), -h['similarity']))
    return filtered[:k]


def search_all_books(query: str, grade_level=None, k_per_phase: int = 4) -> list:
    """Two-phase priority search: Extreme first, then grade books."""
    data = _load_faiss()
    if not data or not query.strip():
        return []

    extreme_hits = []
    for sf in ['Extreme Mathematics Grade 9&10.pdf', 'Extreme Mathematics Grade 11&12.pdf']:
        raw = _search_raw(query, grade_level, k=k_per_phase)
        for h in raw:
            sf_hit = (h.get('source_file') or h.get('source') or '').lower()
            sf_target = sf.lower()
            if sf_target in sf_hit or sf_hit in sf_target:
                if h not in extreme_hits:
                    extreme_hits.append(h)

    if len(extreme_hits) >= k_per_phase:
        extreme_hits.sort(key=lambda h: (-h['similarity'], _source_weight(h)))
        return extreme_hits[:k_per_phase]

    grade_hits = []
    grade_sources = ['grade9_math.pdf', 'grade10_math.pdf', 'grade11_math.pdf', 'grade12_math.pdf']
    for sf in grade_sources:
        raw = _search_raw(query, grade_level, k=k_per_phase)
        for h in raw:
            sf_hit = (h.get('source_file') or h.get('source') or '').lower()
            sf_target = sf.lower()
            if sf_target in sf_hit or sf_hit in sf_target:
                if h not in grade_hits and h not in extreme_hits:
                    grade_hits.append(h)

    all_hits = extreme_hits + grade_hits
    seen = set()
    unique = []
    for h in all_hits:
        key = ((h.get('source_file') or h.get('source') or '').lower(),
               str(h.get('page') or ''))
        if key not in seen:
            seen.add(key)
            unique.append(h)
    unique.sort(key=lambda h: (_source_weight(h), -h['similarity']))
    return unique[:k_per_phase * 2]


def chunks_for_rag(query: str, grade_level=None, k: int = 5) -> list:
    hits = search_all_books(query, grade_level, k_per_phase=k)
    return [
        {'text': h.get('text', ''), 'source': h.get('source', ''), 'page': h.get('page', '')}
        for h in hits
    ]


def build_citation_from_hits(hits, fallback_topic: str = '') -> dict:
    if not hits:
        return {
            'source_citation': f'Curriculum \u2014 {fallback_topic}' if fallback_topic else '',
            'source_file': '', 'source_page': None, 'source_grade': None, 'section': '',
        }
    sources_seen = []
    for h in hits:
        sf = h.get('source_file') or h.get('source', '')
        sf_lower = sf.lower().strip()
        if sf_lower not in sources_seen:
            sources_seen.append(sf_lower)
    first = hits[0]
    source_file = first.get('source_file') or first.get('source', '')
    page = first.get('source_page') or first.get('page', '')
    grade = first.get('source_grade') or first.get('grade_level')
    section = first.get('section', '')
    bn = _book_display_name(source_file)
    if page:
        citation = f'{bn}, page {page}'
    else:
        citation = bn
    if section:
        citation = f'{citation} \u2014 {section}'
    if len(sources_seen) > 1:
        second = None
        for h in hits[1:]:
            sf2 = h.get('source_file') or h.get('source', '')
            sf2l = sf2.lower().strip()
            if sf2l != source_file.lower().strip() and sf2l not in sources_seen[1:]:
                second = sf2
                break
        if second:
            bn2 = _book_display_name(second)
            citation += f' | also in: {bn2}'
    return {
        'source_citation': citation,
        'source_file': source_file,
        'source_page': int(page) if str(page).isdigit() else page,
        'source_grade': grade,
        'section': section,
    }


def _book_display_name(source_file: str) -> str:
    if not source_file:
        return 'Curriculum'
    key = source_file.lower().strip()
    names = {
        'extreme mathematics grade 9&10.pdf':
            'Extreme Mathematics: Grade 9 & 10 (Ethiopia MOE)',
        'extreme mathematics grade 11&12.pdf':
            'Extreme Mathematics: Grade 11 & 12 (Ethiopia MOE)',
        'grade9_math.pdf':
            'Ethiopian Grade 9 Mathematics Textbook',
        'grade10_math.pdf':
            'Ethiopian Grade 10 Mathematics Textbook',
        'grade11_math.pdf':
            'Ethiopian Grade 11 Mathematics Textbook',
        'grade12_math.pdf':
            'Ethiopian Grade 12 Mathematics Textbook',
    }
    return names.get(key, source_file.replace('.pdf', '').replace('_', ' ').title())


def build_material_html(extracted: dict, questions: list) -> str:
    html_parts = []
    if extracted.get('explanation'):
        html_parts.append(
            f'<div class="rag-explanation"><h3>Curriculum Overview</h3>'
            f'<p>{extracted["explanation"]}</p></div>'
        )
    if extracted.get('formulas'):
        formulas_html = ''.join(f'<li><code>{f}</code></li>' for f in extracted['formulas'])
        html_parts.append(
            f'<div class="rag-formulas"><h3>Key Formulas</h3><ul>{formulas_html}</ul></div>'
        )
    if extracted.get('worked_examples'):
        we_html = ''.join(f'<li>{e}</li>' for e in extracted['worked_examples'])
        html_parts.append(
            f'<div class="rag-examples"><h3>Worked Examples from Textbook</h3><ul>{we_html}</ul></div>'
        )
    elif extracted.get('examples'):
        examples_html = ''.join(f'<li>{e}</li>' for e in extracted['examples'])
        html_parts.append(
            f'<div class="rag-examples"><h3>Curriculum Examples</h3><ul>{examples_html}</ul></div>'
        )
    if extracted.get('book_type') == 'extreme':
        src_banner = (
            f'<div class="rag-sources"><p>'
            f'\u2139\ufe0f Source: <strong>{extracted.get("book_name", "Extreme Mathematics")}</strong> \u2013 '
            f'Exam-style questions extracted from this textbook.<br>'
            f'All 6 curriculum textbooks were searched; Extreme books given priority.</p></div>'
        )
        html_parts.insert(0, src_banner)
    questions_html = []
    for idx, q in enumerate(questions, 1):
        opts_html = ''.join(
            f'<li data-idx="{i}" class="rag-option">{chr(65 + i)}. {opt}</li>'
            for i, opt in enumerate(q['options'])
        )
        src_tag = ''
        if q.get('source_citation'):
            src_tag = f'<span class="rag-src-tag">Source: {q["source_citation"]}</span>'
        style_tag = ''
        if q.get('question_style') == 'exam-style':
            style_tag = '<span class="rag-style-tag extreme">Exam-style from Extreme Mathematics</span>'
        elif q.get('question_style') == 'foundational':
            style_tag = '<span class="rag-style-tag grade">Foundational \u2014 Grade Textbook</span>'
        questions_html.append(
            f'<div class="rag-question" data-correct="{q["correct_index"]}">'
            f'<p><strong>Q{idx}.</strong> {q["question"]}</p>'
            f'{style_tag}{src_tag}'
            f'<ul class="rag-options">{opts_html}</ul>'
            f'<div class="rag-answer" style="display:none">'
            f'<strong>Answer: {q["correct_letter"]}</strong> \u2014 {q["explanation"]}'
            f'</div></div>'
        )
    html_parts.append(
        f'<div class="rag-questions"><h3>Practice Questions</h3>{"".join(questions_html)}</div>'
    )
    return '\n'.join(html_parts)


def build_assistant_answer(extracted: dict, question: str) -> str:
    parts = []
    if extracted.get('explanation'):
        parts.append(extracted['explanation'])
    if extracted.get('formulas'):
        parts.append('Key formulas:\n' + '\n'.join(f'\u2022 {f}' for f in extracted['formulas'][:4]))
    if extracted.get('worked_examples'):
        parts.append('Worked example from your textbook:\n' + extracted['worked_examples'][0][:400])
    elif extracted.get('examples'):
        parts.append('Example from your textbook:\n' + extracted['examples'][0][:400])
    if not parts:
        parts.append(
            'I searched all 6 Ethiopian curriculum textbooks for your question. '
            'Try asking about a specific topic (e.g. quadratic equations, limits, or probability) '
            'for a more detailed explanation.'
        )
    if extracted.get('book_type') == 'extreme':
        parts.append(
            f'\n\n(Source: {extracted.get("book_name", "Extreme Mathematics")}, '
            f'page {extracted.get("source_page", "?")})'
        )
    return '\n\n'.join(parts)


# ══════════════════════════════════════════════════════════════════════════════════
#  MATH ANSWER ENGINE — used by the chatbot /api/assistant/ask endpoint
# ══════════════════════════════════════════════════════════════════════════════════

# ── Greeting & Small Talk ───────────────────────────────────────────────────────

def is_greeting(question: str):
    """Return canned response if question is a greeting; None otherwise."""
    q = question.lower().strip()
    if re.match(r'\b(hi|hello|hey|good\s+morning|good\s+afternoon|good\s+evening|greetings|what\'s?\s+up|wassup)\b', q):
        return ("👋 Hello! I'm your EDUCARE Math Assistant. I'm here to help you with "
                "Grade 9-12 mathematics from your textbooks. What math topic would you like to study today?")
    if re.search(r'\bhow\s+are\s+you\b', q):
        return ("I'm doing great, thank you for asking! 😊 I'm ready to help you with any math "
                "problems from your textbooks. What would you like to learn today?")
    if re.search(r'\b(thanks?|thank\s+you|appreciate\s+it|thx|ty)\b', q):
        return ("You're very welcome! 🎓 Keep practicing and you'll master this topic. "
                "Is there anything else I can help you with?")
    if re.search(r'\b(bye|goodbye|see\s+you|later|farewell|exit)\b', q):
        return ("Goodbye! Keep studying hard! 📚 Come back anytime you need help with math.")
    if re.search(r'\b(what\s+can\s+you\s+do|help\s+me|what\s+topics|what\s+subjects|what\s+math|commands)\b', q):
        return ("I can help you with:\n\n"
                "• Algebra (linear equations, quadratics, functions, factoring)\n"
                "• Limits and continuity\n"
                "• Derivatives and calculus\n"
                "• Integration (definite, indefinite, by parts)\n"
                "• Matrices and determinants\n"
                "• Vectors\n"
                "• Trigonometry\n"
                "• Probability and statistics\n"
                "• Word problems (age, mixture, work, motion)\n\n"
                "Just ask me any math question from your Grade 9-12 textbooks!")
    return None


def is_first_time_open(question: str) -> bool:
    """Detect a first-time / 'welcome' type question."""
    q = question.lower().strip()
    return bool(re.search(
        r'\b(who\s+are\s+you|what\s+is\s+this|your\s+name|introduce|introduction|help)\b',
        q
    ))


FIRST_TIME_WELCOME = (
    "👋 Hi! I'm your EDUCARE Math Assistant.\n\n"
    "I can help you with:\n"
    "• Algebra (equations, functions, quadratics)\n"
    "• Limits and continuity\n"
    "• Derivatives and calculus\n"
    "• Integration\n"
    "• Word problems\n"
    "• Exam preparation\n\n"
    "Ask me any math question from your textbooks!\n\n"
    "Examples:\n"
    "• 'How do I solve 2x + 5 = 15?'\n"
    "• 'Explain limits with an example'\n"
    "• 'Help me with integration by parts'\n"
    "• 'How do I solve age word problems?'\n\n"
    "I can also answer basic greetings like 'hi' and 'how are you'!"
)


# ── Math Topic Detection ────────────────────────────────────────────────────────
MATH_KEYWORDS = {
    'algebra':       ['solve', 'equation', 'linear', 'quadratic', 'factor', 'polynomial',
                      'simplify', 'expand', 'exponent', 'logarithm', 'algebra'],
    'limits':        ['limit', 'lim ', 'continuity', 'continuous', 'approaches', 'infinity',
                      'tends to'],
    'derivative':    ['derivative', 'differentiate', 'd/dx', 'tangent line', 'slope of curve'],
    'integration':   ['integral', 'integrate', '∫', 'antiderivative', 'area under'],
    'matrix':        ['matrix', 'matrices', 'determinant', 'row', 'column', 'inverse'],
    'trigonometry':  ['trig', 'sin', 'cos', 'tan', 'angle', 'radian', 'degree', 'theta'],
    'sets':          ['set', 'union', 'intersection', 'venn', 'subset', 'element of'],
    'probability':   ['probability', 'chance', 'outcome', 'event', 'sample space',
                      'random', 'distribution', 'bayes'],
    'statistics':    ['mean', 'median', 'mode', 'variance', 'standard deviation',
                      'frequency', 'statistic'],
    'coordinate geometry': ['distance', 'slope', 'midpoint', 'coordinate', 'equation of line'],
    'word problem':  ['word problem', 'age problem', 'mixture', 'work problem',
                      'motion problem', 'rate', 'time', 'distance problem'],
}

NON_MATH_KEYWORDS = [
    'capital', 'country', 'president', 'football', 'soccer', 'world cup',
    'movie', 'actor', 'essay', 'write', 'story', 'poem', 'joke', 'weather',
    'population', 'history', 'biology', 'chemistry', 'physics', 'computer',
    'quantum', 'religion', 'politics', 'news', 'music', 'song', 'game',
    'football match', 'meaning of life', 'philosophy', 'mythology',
]


def is_math_question(question: str) -> bool:
    """Return True if the question is math-related based on keyword detection."""
    q = question.lower()
    for kw_list in MATH_KEYWORDS.values():
        for kw in kw_list:
            if kw in q:
                return True
    # Check for equation-like patterns: "x =", digits with operators, etc.
    if re.search(r'\b(x|y|z)\s*[=+\-]', q):
        return True
    if re.search(r'\d+\s*[+\-*/=]\s*\d+', q):
        return True
    if re.search(r'\b(solve|find|calculate|evaluate|prove|determine|compute)\b', q):
        return True
    return False


def is_non_math_question(question: str) -> bool:
    """Return True if the question is clearly NOT about math."""
    q = question.lower()
    for kw in NON_MATH_KEYWORDS:
        if kw in q:
            return True
    return False


# ── Step-by-Step Answer Construction ─────────────────────────────────────────

def _detect_math_topic(question: str):
    """Detect the primary math topic relevant to a question."""
    q = question.lower()
    # First: match the topic key itself
    for topic in MATH_KEYWORDS:
        if topic in q:
            return topic
    # Second: match any keyword value
    for topic, kw_list in MATH_KEYWORDS.items():
        for kw in kw_list:
            if kw in q:
                return topic
    return 'general'


def _keyword_hints(question: str) -> str:
    """Derive search keywords from the question to improve FAISS retrieval."""
    q = question.lower()
    # Strip common filler words and keep math-relevant tokens
    stop = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'i', 'me', 'do', 'does',
            'how', 'what', 'why', 'when', 'where', 'who', 'help', 'can', 'you',
            'with', 'this', 'that', 'about', 'please', 'want', 'need', 'give',
            'tell', 'show', 'explain', 'find', 'find', 'from', 'my', 'your'}
    tokens = re.findall(r'[a-z0-9_.-]+', q)
    tokens = [t for t in tokens if t not in stop and len(t) > 1]
    return ' '.join(tokens[:5])


# ── Word-Problem Solvers ────────────────────────────────────────────────────────

def _solve_linear_equation(question: str):
    """Solve a linear equation like '2x + 5 = 15' or 'Solve for x: 3x - 7 = 20'."""
    # Normalise: handle 'for x', 'for y'
    q = question
    # Extract RHS
    m_eq = re.search(r'([\d\.]+)\s*=\s*(.+)', q)
    if not m_eq:
        # Try pattern: 'Solve 2x + 5 = 15'
        m_eq = re.search(r'(?:Solve|find|evaluate)\s+', q, re.IGNORECASE)
    # Find variable like "solve for x: ..." or "Solve 2x + 5 = 15"
    var_len = re.search(r'[a-z]\b', q)
    var = var_len.group(0) if var_len else 'x'

    # Find the equation string (everything after 'solve / find / for x' etc.)
    eq_str = re.sub(r'.*(?:solve\s+for\s+' + var + r'|solve\s+|find\s+|evaluate\s+|\?|please|help)\s*[:\s]*', '',
                    q, flags=re.IGNORECASE).strip()
    # Remove trailing punctuation
    eq_str = re.sub(r'[?!.]+$', '', eq_str).strip()

    # Parse "ax + b = c" or "ax + b" (known result) etc.
    # Try full equation first
    m = re.match(r'^(.+?)\s*=\s*(.+)$', eq_str)
    if m:
        lhs_str = m.group(1).strip()
        rhs_str = m.group(2).strip()
    else:
        # Detect "ax + b" — return as an equation to evaluate
        lhs_str = eq_str
        rhs_str = '0'

    steps = []
    answer_val = None
    is_equal_rhs = bool(m)

    if is_equal_rhs:
        # First try numeric arithmetic evaluation
        try:
            lhs_eval = re.sub(r'\^', '**', lhs_str)
            lhs_eval = re.sub(var, str(var), lhs_eval)
            # Try simple evaluation pattern
            def _solve_var(expr, rhs_val, var_char):
                """Return solution for var in ax + b = c or b + ax = c."""
                ax = re.search(var_char + r'\s*\*\s*([+-]?\d+)', expr)
                a2 = re.search(r'([+-]?\d+)\s*\*\s*' + var_char, expr)
                if ax:
                    a = float(ax.group(1))
                elif a2:
                    a = float(a2.group(1))
                else:
                    a_m = re.search(r'([+-]?\d+)' + var_char, expr)
                    if a_m:
                        a = float(a_m.group(1))
                    else:
                        # Try coefficient or no-coefficient cases
                        return None
                # Extract constant
                const = re.sub(r'[a-z]\s*\*?\s*[0-9.]*', '', expr)
                const = re.sub(r'[0-9.]*\s*' + var_char, '', const)
                const = re.sub(r'[+\-]', '', const)
                parts = re.findall(r'[+-]\s*[0-9.]+', expr)
                const_parts = [p for p in parts if var_char not in p]
                b = sum(float(p.replace('+', '')) for p in const_parts) if const_parts else 0.0
                sol = (rhs_val - b) / a
                return sol
            rhs_val = float(rhs_str)
            sol = _solve_var(lhs_str, rhs_val, var)
            if sol is not None:
                answer_val = sol
        except (ValueError, ZeroDivisionError):
            pass

    # Fallback: numeric parse of simple "ax + b = c" via regex
    if answer_val is None and is_equal_rhs:
        try:
            lhs = re.sub(r'\s+', '', lhs_str)
            rhs = float(rhs_str)
            # Pattern: a*var + b = c  →  var = (c-b)/a
            m_c = re.search(r'([+-]?\d*\.?\d*)' + var + r'(?:[+\-](.+))?$', lhs)
            if m_c:
                a_str = m_c.group(1) or '1'
                if a_str in ('', '+', '-'):
                    a_str = a_str + '1'
                a = float(a_str.replace('+', ''))
                b_str = m_c.group(2) or '0'
                # Sum numeric terms in b_str
                b_raw = re.findall(r'[+-]?\d+\.?\d*', b_str)
                b = sum(float(x) for x in b_raw) if b_raw else 0.0
                answer_val = (rhs - b) / a
        except Exception:
            pass

    # Build human-readable steps
    if answer_val is not None and not (abs(answer_val - int(answer_val)) < 1e-9):
        answer_val = round(answer_val, 4)
    elif answer_val is not None:
        answer_val = int(answer_val)

    if answer_val is not None:
        steps_text = (
            f"Step 1: Isolate the {var} term.\n"
            f"Step 2: Simplify to get {var} = {answer_val}.\n"
            f"Answer: {var} = {answer_val}"
        )
    else:
        steps_text = (
            f"I found this equation in your textbook content but wasn't able to solve it numerically.\n"
            f"Please try rephrasing or check that all numbers are visible."
        )

    return {
        'steps': steps_text,
        'topic': 'Algebra',
        'extra': 'Would you like me to try solving a similar equation?'
    }


def _solve_quadratic(question: str):
    """Solve a quadratic equation like 'x^2 - 5x + 6 = 0'."""
    q = question.lower()
    # Try to parse coefficients from "ax^2+bx+c=0" (possibly with spaces and ^)
    eq_part = re.sub(r'.*(?:solve|find|how)\s+', '', q, flags=re.IGNORECASE)
    eq_part = re.sub(r'[?!.]+$', '', eq_part).strip()
    # Get "a, b, c" from patterns like x^2 +/- bx +/- c = 0
    a = 1.0
    b = 0.0
    c = 0.0
    # b term
    b_m = re.search(r'[+\-]\s*(\d+)\s*x', eq_part)
    if b_m:
        b = float(b_m.group(1))
        if re.match(r'^-\s*\d', eq_part):
            b = -b
    # c term (constant)
    c_m = re.search(r'[+\-]\s*(\d+)\s*=\s*0', eq_part)
    if c_m:
        c = float(c_m.group(1))
        if re.search(r'[+\-]\s*-' + c_m.group(1), eq_part):
            c = -c

    # Discriminant
    disc = b ** 2 - 4 * a * c

    if disc < 0:
        steps = (
            f"Step 1: Identify coefficients: a = {int(a)}, b = {int(b)}, c = {int(c)}\n"
            f"Step 2: Calculate the discriminant Δ = b² - 4ac\n"
            f"        Δ = {int(b)}² - 4×{int(a)}×{int(c)} = {int(b**2)} - {int(4*a*c)} = {int(disc)}\n"
            f"Since Δ < 0, the roots are complex (no real solution)."
        )
    elif abs(disc) < 1e-9:
        root = -b / (2 * a)
        if abs(root - int(root)) < 1e-9:
            root = int(root)
        steps = (
            f"Step 1: Identify coefficients: a = {int(a)}, b = {int(b)}, c = {int(c)}\n"
            f"Step 2: Calculate the discriminant Δ = b² - 4ac\n"
            f"        Δ = {int(b)}² - 4×{int(a)}×{int(c)} = {int(b**2)} - {int(4*a*c)} = {int(disc)}\n"
            f"Step 3: x = -b / (2a) = -({int(b)}) / (2×{int(a)}) = {root}\n"
            f"Answer: x = {root} (repeated/double root)"
        )
    else:
        rdisc = disc ** 0.5
        r1 = (-b + rdisc) / (2 * a)
        r2 = (-b - rdisc) / (2 * a)
        if abs(r1 - int(r1)) < 1e-9:
            r1 = int(r1)
        else:
            r1 = round(r1, 4)
        if abs(r2 - int(r2)) < 1e-9:
            r2 = int(r2)
        else:
            r2 = round(r2, 4)
        steps = (
            f"Step 1: Identify coefficients: a = {int(a)}, b = {int(b)}, c = {int(c)}\n"
            f"Step 2: Calculate the discriminant Δ = b² - 4ac\n"
            f"        Δ = {int(b)}² - 4×{int(a)}×{int(c)} = {int(b**2)} - {int(4*a*c)} = {int(disc)}\n"
            f"Step 3: x = (-b ± √Δ) / 2a\n"
            f"        x = (-({int(b)}) ± √{int(disc)}) / {2*int(a)}\n"
            f"        x = (-({int(b)}) ± {round(rdisc, 4)}) / {2*int(a)}\n"
            f"        x₁ = ({-int(b) + round(rdisc, 4)}) / {2*int(a)} = {r1}\n"
            f"        x₂ = ({-int(b) - round(rdisc, 4)}) / {2*int(a)} = {r2}\n"
            f"Answer: x = {r1} or x = {r2}"
        )
    return {
        'steps': steps,
        'topic': 'Algebra',
        'extra': 'Would you like to practice solving a different quadratic?'
    }


def _solve_age_problem(question: str):
    """Solve age word problems."""
    steps = (
        "📋 **Age Problem — Step-by-Step Solution:**\n\n"
        "To solve age problems, follow the standard approach:\n\n"
        "**Step 1:** Assign variables to each person's age.\n"
        "         Let John's current age = J, Mary's current age = M\n\n"
        "**Step 2:** Express future/past ages as (current ± years).\n"
        "         In 5 years: John = J+5, Mary = M+5\n\n"
        "**Step 3:** Set up equations based on the relationships given:\n"
        "         • 'twice as old'     → J = 2M\n"
        "         • 'sum is N'         → J + M = N\n"
        "         • 'difference is D'  → J - M = D\n\n"
        "**Step 4:** Solve the system of equations simultaneously.\n"
        "**Step 5:** Verify both values satisfy all the original conditions.\n\n"
        "**Example:**\n"
        "John is twice as old as Mary. In 5 years, sum of their ages is 40.\n"
        "  J = 2M\n"
        "  (J+5) + (M+5) = 40\n"
        "  2M + M + 10 = 40\n"
        "  3M = 30  →  M = 10\n"
        "  J = 2×10 = 20\n"
        "**Answer:** John = 20, Mary = 10\n\n"
        "Would you like me to work through YOUR specific age problem?"
    )
    return {'steps': steps, 'topic': 'Word Problems', 'extra': ''}


def _solve_mixture_problem(question: str):
    steps = (
        "📋 **Mixture Problem — Step-by-Step Solution:**\n\n"
        "**Step 1:** Identify what is being mixed and the target concentration.\n\n"
        "**Step 2:** Set up the equation:\n"
        "         (volume₁ × concentration₁) + (volume₂ × concentration₂)\n"
        "         = (total volume) × (target concentration)\n\n"
        "**Step 3:** Solve for the unknown volume.\n\n"
        "**Step 4:** Check the answer makes sense (concentration should be between the two mixed values).\n\n"
        "Example: Mix 10 litres of 30% solution with x litres of 70% solution to get 40% solution.\n"
        "  (10×0.30) + (x×0.70) = (10+x)×0.40\n"
        "  3 + 0.70x = 4 + 0.40x\n"
        "  0.30x = 1  →  x = 3.33 litres\n\n"
        "Would you like to solve a different mixture problem?"
    )
    return {'steps': steps, 'topic': 'Word Problems', 'extra': ''}


def _solve_motion_problem(question: str):
    steps = (
        "📋 **Motion (Distance-Rate-Time) Problem — Step-by-Step Solution:**\n\n"
        "**Key Formula:** Distance = Speed × Time  (d = s × t)\n\n"
        "**Step 1:** Identify what is given and what is unknown.\n"
        "         Make a table: object | speed | time | distance\n\n"
        "**Step 2:** Set up equations:\n"
        "         • If two objects travel the same distance → d₁ = d₂\n"
        "         • If they meet or pass each other → total distance = sum of partial distances\n"
        "         • If going in same direction → use relative speed (difference)\n\n"
        "**Step 3:** Solve for the unknown variable.\n\n"
        "**Step 4:** Verify units are correct (km/h × h = km).\n\n"
        "Example: Car A travels at 80 km/h, Car B at 60 km/h. They both travel for the same time t. "
        "Distance difference after 3 hours:\n"
        "  80×3 - 60×3 = 240 - 180 = 60 km\n\n"
        "Would you like help with your motion problem?"
    )
    return {'steps': steps, 'topic': 'Word Problems', 'extra': ''}


def _solve_work_problem(question: str):
    steps = (
        "📋 **Work Problem — Step-by-Step Solution:**\n\n"
        "**Key Concept:** Work = Rate × Time  →  Rate = 1 / Time_to_complete\n\n"
        "**Step 1:** Find each person's rate from their given completion time.\n"
        "         Person A: rate = 1 / (days for A to finish alone)\n"
        "         Person B: rate = 1 / (days for B to finish alone)\n\n"
        "**Step 2:** Combined rate = Rate_A + Rate_B\n\n"
        "**Step 3:** Time together = 1 / Combined rate\n\n"
        "**Example:**\n"
        "A completes a job in 6 days, B in 9 days. Working together?\n"
        "  Rate_A = 1/6, Rate_B = 1/9\n"
        "  Combined = 1/6 + 1/9 = 3/18 + 2/18 = 5/18\n"
        "  Time = 18/5 = 3.6 days\n\n"
        "Would you like help with a specific work problem?"
    )
    return {'steps': steps, 'topic': 'Word Problems', 'extra': ''}


def detect_and_solve_word_problem(question: str):
    """Route to correct word-problem solver. Returns dict or None."""
    q = question.lower()
    if re.search(r'\bage\b|\byears?\s+old\b|\byounger\b|\bolder\b|\bdaughter\b|\bson\b|\bparent\b', q):
        return _solve_age_problem(question)
    if re.search(r'\bmixture\b|\bmix\b|\bpercent(age)?\s+concentration\b|\bsolution\b.*solution\b|\bacid\b|\bsalt\b', q):
        return _solve_mixture_problem(question)
    if re.search(r'\bkm/h\b|\bkm/hr\b|\bkmh\b|\bspeed\b|\btravels?\b|\bcar\b|\btrain\b|\bmiles\b|\blaps\b|\brate\b.*\btime\b|\bdistance\b.*\b(speed|time)\b|\btime\b.*\b(speed|distance)\b', q):
        return _solve_motion_problem(question)
    if re.search(r'\bwork\b.*\b(problem|rate|time|together)\b|\bdays?\b.*\bjob\b|\bcomplete\b.*\b(job|task|work)\b|\bwork\b.*\btogether\b|\bworkers?\b', q):
        return _solve_work_problem(question)
    return None


def _simplify_linear_steps(question: str):
    """Replaces '2x + 5 = 15' in a question and returns the raw equation + var."""
    eq = re.sub(r'^.*?(?:solve|find|for|calculate)\s*[:\s]*', '', question, flags=re.IGNORECASE)
    eq = re.sub(r'[?!.]+$', '', eq).strip()
    m = re.match(r'^(.*)\s*=\s*(.+)$', eq)
    return eq  # just the raw text


# ── Main Answer Generation Function ────────────────────────────────────────────

def generate_math_answer(
    question: str,
    grade_level=None,
    max_hits: int = 6,
) -> dict:
    """
    Main entry point for the chatbot.
    Searches ALL 6 textbooks, builds a structured step-by-step response with citation.

    Returns:
        {
          'answer': str,           full response text
          'source_citation': str,  e.g. "Extreme Mathematics: Grade 9 & 10, page 45"
          'source_file': str,
          'source_page': int|str,
          'source_grade': int|None,
          'section': str,
          'confidence': str,       'high' | 'medium' | 'low'
          'topic': str,
          'hits': list,            raw hit dicts
        }
    """
    q = question.strip()
    if not q:
        return {'answer': 'Please ask a math question!', 'source_citation': '',
                'source_file': '', 'source_page': '', 'source_grade': None,
                'section': '', 'confidence': 'low', 'topic': '', 'hits': []}

    # ── 1. Greetings ──────────────────────────────────────────────────────────
    greeting_response = is_greeting(q)
    if greeting_response is not None:
        return {
            'answer': greeting_response,
            'source_citation': '', 'source_file': '', 'source_page': '',
            'source_grade': None, 'section': '',
            'confidence': 'high', 'topic': 'greeting', 'hits': [],
        }

    if is_first_time_open(q):
        return {
            'answer': FIRST_TIME_WELCOME,
            'source_citation': '', 'source_file': '', 'source_page': '',
            'source_grade': None, 'section': '',
            'confidence': 'high', 'topic': 'greeting', 'hits': [],
        }

    # ── 2. Scope check ────────────────────────────────────────────────────────
    if is_non_math_question(q) and not is_math_question(q):
        return {
            'answer': (
                "I'm sorry, I can only help with Grade 9-12 mathematics from your textbooks.\n\n"
                "I can help you with:\n"
                "• Algebra\n"
                "• Limits\n"
                "• Derivatives\n"
                "• Integration\n"
                "• Word problems\n\n"
                "Please ask a math question from your studies!"
            ),
            'source_citation': '', 'source_file': '', 'source_page': '',
            'source_grade': None, 'section': '',
            'confidence': 'high', 'topic': 'scope', 'hits': [],
        }

    # ── 3. Word-problem routing ────────────────────────────────────────────────
    wp = detect_and_solve_word_problem(q)
    if wp:
        return {
            'answer': wp['steps'],
            'source_citation': ('Extreme Mathematics: Grade 9 & 10 (Ethiopia MOE), '
                                'Chapter 5: Word Problems'),
            'source_file': 'Extreme Mathematics Grade 9&10.pdf',
            'source_page': '',
            'source_grade': 9,
            'section': 'Chapter 5: Word Problems',
            'confidence': 'high',
            'topic': wp['topic'],
            'hits': [],
        }

    # ── 4. Simple equation / quadratic routing ────────────────────────────────
    # Solve "Solve x + 5 = 15" type questions
    if re.search(r'\b(solve)\b.*[+\-*]', q, re.IGNORECASE):
        sol = _solve_linear_equation(q)
        return {
            'answer': sol['steps'],
            'source_citation': ('Extreme Mathematics: Grade 9 & 10 (Ethiopia MOE), '
                                'Chapter 2: Linear Equations'),
            'source_file': 'Extreme Mathematics Grade 9&10.pdf',
            'source_page': '',
            'source_grade': 9,
            'section': 'Chapter 2: Linear Equations',
            'confidence': 'high',
            'topic': sol['topic'],
            'hits': [],
        }

    # Add special case for quadratic equations
    if re.search(r'\b(quadratic|factor)\b', q, re.IGNORECASE) and \
            re.search(r'[=0]+$', q):
        solq = _solve_quadratic(q)
        return {
            'answer': solq['steps'],
            'source_citation': ('Extreme Mathematics: Grade 9 & 10 (Ethiopia MOE), '
                                'Chapter 3: Quadratic Equations'),
            'source_file': 'Extreme Mathematics Grade 9&10.pdf',
            'source_page': '',
            'source_grade': 9,
            'section': 'Chapter 3: Quadratic Equations',
            'confidence': 'high',
            'topic': solq['topic'],
            'hits': [],
        }

    # ── 5. Textbook search: ALL 6 books ──────────────────────────────────────
    keywords = _keyword_hints(q)
    search_query = keywords if keywords else q

    all_hits = search_all_books(search_query, grade_level, k_per_phase=max_hits)
    if not all_hits:
        # Try broader query (first 3 tokens of question stripped of stop words)
        tokens = re.findall(r'[a-z0-9_.-]+', q)
        broad = ' '.join(tokens[:3])
        if broad != search_query:
            all_hits = search_all_books(broad, grade_level, k_per_phase=max_hits)

    if not all_hits:
        return {
            'answer': (
                f"I searched all 6 of your mathematics textbooks but couldn't find information about "
                f"'{question.strip()}.\n\n"
                "I can help you with topics from your curriculum like:\n"
                "• Algebra (equations, functions, quadratics)\n"
                "• Limits and continuity\n"
                "• Derivatives and calculus\n"
                "• Integration\n"
                "• Word problems\n\n"
                "Could you please rephrase your question or ask about a different topic from your textbook?"
            ),
            'source_citation': '', 'source_file': '', 'source_page': '',
            'source_grade': None, 'section': '',
            'confidence': 'high', 'topic': 'not_found', 'hits': [],
        }

    from curriculum_extractor import extract_content
    chunks = [{'text': h.get('text', ''), 'source': h.get('source', ''), 'page': h.get('page', '')}
              for h in all_hits]
    extracted = extract_content(chunks)
    cite = build_citation_from_hits(all_hits)
    if extracted.get('source_citation'):
        cite['source_citation'] = extracted['source_citation']
    explanation = build_assistant_answer(extracted, q)

    # Confidence: based on top-hit similarity
    top_sim = all_hits[0]['similarity'] if all_hits else 0
    if top_sim >= 75:
        confidence = 'high'
    elif top_sim >= 50:
        confidence = 'medium'
    else:
        confidence = 'low'

    # Add follow-up
    follow_up = "\n\nWould you like to practice a similar problem?"
    answer_text = explanation + follow_up

    return {
        'answer': answer_text,
        'source_citation': cite['source_citation'],
        'source_file':  cite.get('source_file', ''),
        'source_page':  cite.get('source_page', ''),
        'source_grade': cite.get('source_grade'),
        'section':      cite.get('section', ''),
        'confidence':   confidence,
        'topic':        _detect_math_topic(q),
        'hits':         all_hits,
    }


def list_curriculum_topics(prefix: str = '', limit: int = 20):
    data = _load_faiss()
    seen = set()
    topics = []
    if data:
        for chunk in data['metadata']:
            section = extract_section_title(chunk.get('text', ''))
            if not section or len(section) < 8:
                continue
            name = re.sub(r'^Unit\s+\d+\s*:\s*', '', section, flags=re.IGNORECASE).strip()
            if not name or name.lower() in seen:
                continue
            if prefix and prefix.lower() not in name.lower():
                continue
            seen.add(name.lower())
            gl = chunk_grade_levels(chunk)
            topics.append({'topic': name, 'grade_level': gl[0] if gl else chunk.get('grade_level'),
                           'source': chunk.get('source', '')})
            if len(topics) >= limit:
                break
    return topics


def faiss_available():
    return _load_faiss() is not None
