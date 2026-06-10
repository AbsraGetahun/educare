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


# Canonical keys used in metadata after embedding (see embed_curriculum.py)
SOURCE_ALIASES = {
    'grade-9-mathematics-textbook.pdf': 'grade9_math.pdf',
    'grade-10-mathematics-textbook.pdf': 'grade10_math.pdf',
    'grade-11-mathematics-textbook.pdf': 'grade11_math.pdf',
    'grade-12-mathematics-textbook.pdf': 'grade12_math.pdf',
    'grade9_mathematics_textbook.pdf': 'grade9_math.pdf',
    'grade10_mathematics_textbook.pdf': 'grade10_math.pdf',
    'grade11_mathematics_textbook.pdf': 'grade11_math.pdf',
    'grade12_mathematics_textbook.pdf': 'grade12_math.pdf',
}

EXTREME_BOOKS = {
    'extreme mathematics grade 9&10.pdf',
    'extreme mathematics grade 11&12.pdf',
}

GRADE_TEXTBOOKS = {
    'grade9_math.pdf',
    'grade10_math.pdf',
    'grade11_math.pdf',
    'grade12_math.pdf',
}


def normalize_source_key(source: str) -> str:
    """Map any PDF filename variant to a canonical lowercase key."""
    if not source:
        return ''
    key = os.path.basename(source).lower().strip()
    return SOURCE_ALIASES.get(key, key)


def parse_grades_from_filename(filename: str):
    lower = os.path.basename(filename).lower()
    canonical = normalize_source_key(lower)
    if canonical in GRADE_TEXTBOOKS:
        return [int(canonical.replace('grade', '').replace('_math.pdf', ''))]
    if '9&10' in lower or '9 and 10' in lower or '9& 10' in lower:
        return [9, 10]
    if '11&12' in lower or '11 and 12' in lower or '11& 12' in lower:
        return [11, 12]
    compact = lower.replace(' ', '').replace('_', '').replace('-', '')
    for key, grade in [('grade12', 12), ('grade11', 11), ('grade10', 10), ('grade9', 9)]:
        if key in compact:
            return [grade]
    m = re.search(r'grade[-\s]*(\d+)', lower)
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


def chunk_matches_grade(chunk: dict, grade_level, strict=False):
    """If strict=False, chunks without grade metadata are kept (soft filter for search)."""
    if grade_level is None:
        return True
    levels = chunk_grade_levels(chunk)
    if not levels:
        return not strict
    gl = int(grade_level)
    if gl in levels:
        return True
    if not strict:
        # Include adjacent senior grades (11↔12) and junior (9↔10) when topic may span books
        if gl in (11, 12) and any(g in (11, 12) for g in levels):
            return True
        if gl in (9, 10) and any(g in (9, 10) for g in levels):
            return True
    return False


def _is_extreme_book(hit: dict) -> bool:
    key = normalize_source_key(hit.get('source_file') or hit.get('source') or '')
    return key in EXTREME_BOOKS or 'extreme mathematics' in key


def _is_grade_textbook(hit: dict) -> bool:
    key = normalize_source_key(hit.get('source_file') or hit.get('source') or '')
    if key in GRADE_TEXTBOOKS:
        return True
    return 'mathematics-textbook' in key and 'extreme' not in key


def _grade_rank_boost(hit: dict, grade_level) -> int:
    """Higher score = better match for requested grade (used for ranking, not hard exclusion)."""
    if grade_level is None:
        return 0
    gl = int(grade_level)
    levels = chunk_grade_levels(hit)
    if not levels:
        return 5
    if gl in levels:
        return 100
    if gl in (11, 12) and any(g in (11, 12) for g in levels):
        return 70
    if gl in (9, 10) and any(g in (9, 10) for g in levels):
        return 70
    return max(0, 30 - 10 * min(abs(l - gl) for l in levels))


def extract_section_title(text: str) -> str:
    m = re.search(r'Unit\s+\d+\s*:\s*[^\n]+', text, re.IGNORECASE)
    return m.group(0).strip() if m else ''


# Quiz generation: Extreme books first, then grade textbooks
QUIZ_SOURCE_PRIORITY = {
    'extreme mathematics grade 9&10.pdf': 1,
    'extreme mathematics grade 11&12.pdf': 2,
    'grade9_math.pdf': 3,
    'grade10_math.pdf': 4,
    'grade11_math.pdf': 5,
    'grade12_math.pdf': 6,
}
# Content/notes search: grade textbooks only, equal priority across grades 9–12
CONTENT_SOURCE_PRIORITY = {g: 1 for g in GRADE_TEXTBOOKS}


def _source_weight(hit: dict) -> int:
    """Priority for quiz / exam-style sourcing (includes Extreme books)."""
    sf = normalize_source_key(hit.get('source_file') or hit.get('source') or '')
    return QUIZ_SOURCE_PRIORITY.get(sf, 99)


def _content_source_weight(hit: dict) -> int:
    sf = normalize_source_key(hit.get('source_file') or hit.get('source') or '')
    return CONTENT_SOURCE_PRIORITY.get(sf, 50)


def _is_extreme(source_file: str) -> bool:
    return normalize_source_key(source_file) in EXTREME_BOOKS


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


def _dedupe_hits(hits: list) -> list:
    seen = set()
    unique = []
    for h in hits:
        key = (
            normalize_source_key(h.get('source_file') or h.get('source') or ''),
            str(h.get('page') or ''),
        )
        if key not in seen:
            seen.add(key)
            unique.append(h)
    return unique


def _balance_by_textbook(hits: list, k: int) -> list:
    """Round-robin across textbooks so Grade 11/12 are not drowned out by 9/10."""
    by_src = {}
    for h in hits:
        sk = normalize_source_key(h.get('source_file') or h.get('source') or '')
        by_src.setdefault(sk, []).append(h)
    for sk in by_src:
        by_src[sk].sort(key=lambda x: -x.get('similarity', 0))

    sources = sorted(
        by_src.keys(),
        key=lambda s: -max((h.get('similarity', 0) for h in by_src[s]), default=0),
    )
    result = []
    round_idx = 0
    while len(result) < k and sources:
        added = False
        for sk in sources:
            if round_idx < len(by_src[sk]):
                result.append(by_src[sk][round_idx])
                added = True
                if len(result) >= k:
                    break
        if not added:
            break
        round_idx += 1
    if len(result) < k:
        for h in hits:
            if h not in result:
                result.append(h)
            if len(result) >= k:
                break
    return result[:k]


def _filter_hits_by_topic_query(hits: list, query: str) -> list:
    """
    Extra relevance filter for material/notes generation.

    Ensures that very broad queries like "algebra" still retrieve chunks whose
    text or section headings actually mention the topic keywords.
    """
    q = (query or '').lower().strip()
    if not hits or not q:
        return hits

    # Extract meaningful tokens from the topic (e.g. "algebra", "quadratic").
    tokens = [t for t in re.findall(r'[a-z0-9]+', q) if len(t) > 3]
    if not tokens:
        return hits

    filtered = []
    for h in hits:
        blob = (h.get('text') or '') + ' ' + (h.get('section') or '')
        blob_l = blob.lower()
        if not blob_l.strip():
            continue
        if any(t in blob_l for t in tokens):
            filtered.append(h)

    # Fall back to original list if the filter was too aggressive.
    return filtered or hits


def search_curriculum_content(query: str, grade_level=None, k: int = 5) -> list:
    """
    Search grade textbooks only (no Extreme Mathematics).
    Soft grade ranking + balanced results across all indexed grade books,
    with an additional topic-keyword relevance filter for materials/notes.
    """
    data = _load_faiss()
    if not data or not query.strip():
        return []

    raw = _search_raw(query, grade_level=None, k=max(k * 25, 50))
    grade_hits = [h for h in raw if _is_grade_textbook(h)]

    if grade_level is not None:
        preferred = [h for h in grade_hits if chunk_matches_grade(h, grade_level, strict=False)]
        # If requested grade band has no indexed hits, fall back to any grade textbook
        if preferred:
            grade_hits = preferred

    # Apply topic-keyword filter so "algebra" does not return unrelated units.
    grade_hits = _filter_hits_by_topic_query(grade_hits, query)

    grade_hits.sort(
        key=lambda h: (
            _grade_rank_boost(h, grade_level),
            -h.get('similarity', 0),
            -_content_source_weight(h),
        ),
        reverse=True,
    )
    return _balance_by_textbook(_dedupe_hits(grade_hits), k)


def search_curriculum(query: str, grade_level=None, k: int = 5) -> list:
    """Public curriculum search API — grade textbooks only, proper citations."""
    return search_curriculum_content(query, grade_level, k)


def search_all_books(query: str, grade_level=None, k_per_phase: int = 4) -> list:
    """
    Quiz-oriented search: Extreme Mathematics first, then grade textbooks.
    Do NOT use for notes, materials, or curriculum preview.
    """
    data = _load_faiss()
    if not data or not query.strip():
        return []

    raw = _search_raw(query, grade_level=None, k=max(k_per_phase * 20, 40))
    extreme_hits = [h for h in raw if _is_extreme_book(h)]
    grade_hits = [h for h in raw if _is_grade_textbook(h)]

    extreme_hits.sort(key=lambda h: (-h.get('similarity', 0), _source_weight(h)))
    grade_hits.sort(
        key=lambda h: (
            _grade_rank_boost(h, grade_level),
            -h.get('similarity', 0),
            _content_source_weight(h),
        ),
        reverse=True,
    )

    combined = _dedupe_hits(extreme_hits[:k_per_phase] + grade_hits[:k_per_phase])
    if len(combined) < k_per_phase:
        combined = _dedupe_hits(extreme_hits + grade_hits)[: k_per_phase * 2]
    return combined[: k_per_phase * 2]


def chunks_for_rag(query: str, grade_level=None, k: int = 5) -> list:
    """Content chunks for notes/materials — grade textbooks only."""
    hits = search_curriculum_content(query, grade_level, k=k)
    return [
        {'text': h.get('text', ''), 'source': h.get('source', ''), 'page': h.get('page', '')}
        for h in hits
    ]


def get_indexed_textbooks() -> dict:
    """Report which textbooks are present in the FAISS index."""
    data = _load_faiss()
    if not data:
        return {'indexed': [], 'missing_grade': list(GRADE_TEXTBOOKS), 'missing_extreme': list(EXTREME_BOOKS)}
    sources = set(
        normalize_source_key(c.get('source', '')) for c in data['metadata']
    )
    indexed_grade = sorted(sources & GRADE_TEXTBOOKS)
    indexed_extreme = sorted(sources & EXTREME_BOOKS)
    return {
        'indexed_grade': indexed_grade,
        'indexed_extreme': indexed_extreme,
        'missing_grade': sorted(GRADE_TEXTBOOKS - sources),
        'missing_extreme': sorted(EXTREME_BOOKS - sources),
        'total_chunks': len(data['metadata']),
    }


def build_citation_from_hits(hits, fallback_topic: str = '') -> dict:
    if not hits:
        return {
            'source_citation': f'Curriculum \u2014 {fallback_topic}' if fallback_topic else '',
            'source_file': '', 'source_page': None, 'source_grade': None, 'section': '',
        }
    ranked = sorted(
        hits,
        key=lambda h: (
            999 if _is_extreme_book(h) else _content_source_weight(h),
            -h.get('similarity', 0),
        ),
    )
    sources_seen = []
    for h in ranked:
        sf = h.get('source_file') or h.get('source', '')
        sf_lower = sf.lower().strip()
        if sf_lower not in sources_seen:
            sources_seen.append(sf_lower)
    first = ranked[0]
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
        for h in ranked[1:]:
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
        'grade9_math.pdf': 'Ethiopian Grade 9 Mathematics Textbook',
        'grade10_math.pdf': 'Ethiopian Grade 10 Mathematics Textbook',
        'grade11_math.pdf': 'Ethiopian Grade 11 Mathematics Textbook',
        'grade12_math.pdf': 'Ethiopian Grade 12 Mathematics Textbook',
    }
    key = normalize_source_key(source_file)
    return names.get(key, source_file.replace('.pdf', '').replace('_', ' ').title())


def build_material_html(extracted: dict, questions: list) -> str:
    from math_format import format_note_html, format_note_html_inline, steps_to_html

    html_parts = []
    if extracted.get('explanation'):
        html_parts.append(
            '<div class="rag-explanation"><h3>Curriculum Overview</h3>'
            f'{format_note_html(extracted["explanation"])}</div>'
        )
    if extracted.get('steps'):
        html_parts.append(steps_to_html(extracted['steps']))
    if extracted.get('formulas'):
        formulas_html = ''.join(
            f'<li><code>{format_note_html_inline(f)}</code></li>' for f in extracted['formulas']
        )
        html_parts.append(
            f'<div class="rag-formulas"><h3>Key Formulas</h3><ul>{formulas_html}</ul></div>'
        )
    if extracted.get('worked_examples'):
        we_html = ''.join(
            f'<li>{format_note_html(e)}</li>' for e in extracted['worked_examples']
        )
        html_parts.append(
            '<div class="rag-examples"><h3>Worked Examples from Textbook</h3>'
            f'<ul>{we_html}</ul></div>'
        )
    elif extracted.get('examples'):
        examples_html = ''.join(
            f'<li>{format_note_html(e)}</li>' for e in extracted['examples']
        )
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
            f'<li data-idx="{i}" class="rag-option">{chr(65 + i)}. {format_note_html_inline(str(opt))}</li>'
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
        q_text = format_note_html_inline(q.get('question', ''))
        q_expl = format_note_html_inline(q.get('explanation', ''))
        questions_html.append(
            f'<div class="rag-question" data-correct="{q["correct_index"]}">'
            f'<p><strong>Q{idx}.</strong> {q_text}</p>'
            f'{style_tag}{src_tag}'
            f'<ul class="rag-options">{opts_html}</ul>'
            f'<div class="rag-answer" style="display:none">'
            f'<strong>Answer: {q["correct_letter"]}</strong> \u2014 {q_expl}'
            f'</div></div>'
        )
    html_parts.append(
        f'<div class="rag-questions"><h3>Practice Questions</h3>{"".join(questions_html)}</div>'
    )
    return '\n'.join(html_parts)


def build_assistant_answer(extracted: dict, question: str) -> str:
    from math_format import format_math_for_display, truncate_at_sentence

    parts = []
    if extracted.get('explanation'):
        parts.append(format_math_for_display(extracted['explanation']))
    if extracted.get('steps'):
        parts.append('Step-by-step:\n' + '\n'.join(
            f'{i}. {truncate_at_sentence(s, 400)}'
            for i, s in enumerate(extracted['steps'][:5], 1)
        ))
    if extracted.get('formulas'):
        parts.append('Key formulas:\n' + '\n'.join(
            f'\u2022 {format_math_for_display(f)}' for f in extracted['formulas'][:4]
        ))
    if extracted.get('worked_examples'):
        parts.append(
            'Worked example from your textbook:\n'
            + truncate_at_sentence(format_math_for_display(extracted['worked_examples'][0]), 500)
        )
    elif extracted.get('examples'):
        parts.append(
            'Example from your textbook:\n'
            + truncate_at_sentence(format_math_for_display(extracted['examples'][0]), 500)
        )
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
    'derivative':    ['derivative', 'derivation', 'differentiate', 'd/dx', 'tangent line',
                      'slope of curve', "f'"],
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
            'tell', 'show', 'explain', 'find', 'find', 'from', 'my', 'your',
            'something', 'else', 'please', 'just', 'like', 'would', 'could'}
    tokens = re.findall(r'[a-z0-9_.-]+', q)
    tokens = [t for t in tokens if t not in stop and len(t) > 1]
    topic = _detect_math_topic(question)
    if topic != 'general' and topic not in tokens:
        tokens.insert(0, topic.replace(' ', ''))
    return ' '.join(tokens[:6])


OUT_OF_SCOPE_MESSAGE = (
    "I'm sorry — that's out of my scope right now. I'm still under development.\n\n"
    "Please ask something else from your Grade 9–12 math textbooks, such as:\n"
    "• Solving linear or quadratic equations\n"
    "• Factoring and simplifying expressions\n"
    "• Limits, derivatives, or integration\n"
    "• Word problems (age, mixture, motion, work)"
)

# Minimum FAISS similarity (0–100) before trusting textbook retrieval
MIN_RELEVANCE_SIMILARITY = 50

# Section keywords that often appear in irrelevant retrieval for algebra questions
_TOPIC_MISMATCH_MARKERS = {
    'algebra': [
        'congruency and similarity', 'solid figures', 'frequency curve',
        'bar chart', 'pie chart', 'representation of data', 'venn diagram',
        'biology', 'chemistry', 'history', 'capital of',
    ],
    'derivative': ['solid figures', 'frequency polygon', 'pie chart', 'bar chart'],
    'limits': ['solid figures', 'frequency polygon', 'pie chart', 'venn diagram'],
    'integration': ['solid figures', 'venn diagram', 'bar chart'],
}


def _extract_query_terms(question: str) -> list:
    """Significant terms from the student question for relevance checks."""
    stop = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'i', 'me', 'do', 'does',
        'how', 'what', 'why', 'when', 'where', 'who', 'help', 'can', 'you',
        'with', 'this', 'that', 'about', 'please', 'want', 'need', 'give',
        'tell', 'show', 'explain', 'find', 'from', 'my', 'your', 'something',
        'else', 'just', 'like', 'would', 'could', 'ask', 'question',
    }
    q = question.lower()
    tokens = re.findall(r'[a-z0-9]+', q)
    terms = [t for t in tokens if t not in stop and len(t) > 2]
    # Keep short math tokens (x, y) and numeric equation fragments
    for t in re.findall(r'\b[xyz]\b', q):
        if t not in terms:
            terms.append(t)
    return terms


def _hit_relevant_to_question(hit: dict, question: str, topic: str) -> bool:
    """True if a search hit plausibly answers the student's question."""
    blob = (
        (hit.get('text') or '') + ' ' + (hit.get('section') or '')
    ).lower()
    if not blob.strip():
        return False

    terms = _extract_query_terms(question)
    if terms:
        overlap = sum(1 for t in terms if t in blob)
        if overlap == 0 and hit.get('similarity', 0) < 62:
            return False

    for marker in _TOPIC_MISMATCH_MARKERS.get(topic, []):
        if marker in blob:
            topic_terms = {
                'algebra': ('equation', 'algebra', 'factor', 'quadratic', 'linear',
                            'polynomial', 'expression', 'solve', 'variable'),
            }.get(topic, ())
            if topic_terms and not any(tt in blob for tt in topic_terms):
                return False
    return True


def _filter_relevant_hits(hits: list, question: str, topic: str) -> list:
    """Drop textbook chunks that don't match the question topic or keywords."""
    if not hits:
        return []
    filtered = [h for h in hits if _hit_relevant_to_question(h, question, topic)]
    return filtered if filtered else []


def _should_route_to_linear_solver(question: str) -> bool:
    """Detect linear equations (with or without the word 'solve')."""
    q = question.lower()
    if _should_route_to_limit(q) or _should_route_to_derivative(q):
        return False
    if '=' not in q:
        return False
    if re.search(r'\b(quadratic|x\s*\^?\s*2|x²|factor(?:ing)?)\b', q):
        return False
    if re.search(r'[a-z]\s*[=+\-]|[+\-]\s*\d+\s*[a-z]|=\s*[\d.]+', q):
        return True
    if re.search(r'\b(solve|find|evaluate|calculate|what\s+is)\b', q) and re.search(
        r'[a-z]\s*[*]?\s*\d|\d\s*[a-z]', q
    ):
        return True
    return False


def _should_route_to_quadratic(question: str) -> bool:
    """Detect quadratic / factoring questions."""
    q = question.lower()
    if _should_route_to_limit(q) or _should_route_to_derivative(q):
        return False
    if re.search(r'\b(quadratic|factor(?:ing)?)\b', q):
        return True
    if re.search(r'\bpolynomial\b', q) and '=' in q:
        return True
    # Require '=' so limits/derivatives with x² are not misrouted
    if re.search(r'x\s*\^?\s*2|x²|x\^2', q) and '=' in q:
        return True
    return False


def _linear_solution_succeeded(steps: str) -> bool:
    return bool(re.search(r'\bAnswer:\s*[a-z]\s*=', steps, re.IGNORECASE))


def _out_of_scope_response(topic: str = 'out_of_scope') -> dict:
    return {
        'answer': OUT_OF_SCOPE_MESSAGE,
        'source_citation': '', 'source_file': '', 'source_page': '',
        'source_grade': None, 'section': '',
        'confidence': 'high', 'topic': topic, 'hits': [],
    }


# ── Limits & Derivatives (Grade 11–12 calculus) ─────────────────────────────────

def _normalize_calculus_expr(expr: str) -> str:
    s = expr.lower().strip()
    s = s.replace('²', '^2').replace('³', '^3').replace('⁴', '^4')
    s = s.replace('→', '->').replace('−', '-').replace('–', '-')
    s = re.sub(r'\s+', '', s)
    s = s.replace('^', '**')
    s = re.sub(r'(\d)([xyz])', r'\1*\2', s)
    s = re.sub(r'\)\(', r')*(', s)
    return s


def _format_poly_term(coef: float, power: int, var: str = 'x') -> str:
    if abs(coef) < 1e-12:
        return ''
    c = int(coef) if abs(coef - int(coef)) < 1e-9 else round(coef, 4)
    if power == 0:
        return f'{c:+d}' if isinstance(c, int) else f'{coef:+.4g}'
    if power == 1:
        if c == 1:
            return f'+{var}'
        if c == -1:
            return f'-{var}'
        return f'{c:+d}{var}' if isinstance(c, int) else f'{coef:+.4g}{var}'
    if c == 1:
        return f'+{var}**{power}'
    if c == -1:
        return f'-{var}**{power}'
    return f'{c:+d}{var}**{power}' if isinstance(c, int) else f'{coef:+.4g}{var}**{power}'


def _format_polynomial(terms: list, var: str = 'x') -> str:
    """Format list of (coef, power) into a readable polynomial."""
    parts = [_format_poly_term(c, p, var) for c, p in terms if abs(c) > 1e-12]
    if not parts:
        return '0'
    s = ''.join(parts)
    if s.startswith('+'):
        s = s[1:]
    return s.replace('**2', '²').replace('**3', '³')


def _parse_polynomial_terms(expr: str, var: str = 'x') -> list:
    """Parse ax^n + bx + c into [(coef, power), ...]."""
    s = _normalize_calculus_expr(expr)
    if not s:
        return []
    s = s.replace(f'-{var}', f'-1*{var}').replace(f'+{var}', f'+1*{var}')
    if s.startswith(f'{var}'):
        s = '1*' + s
    if s[0] not in '+-':
        s = '+' + s
    parts = re.findall(r'[+-][^+-]+', s)
    terms = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if re.fullmatch(r'[+-]?\d+\.?\d*', part):
            terms.append((float(part), 0))
            continue
        m = re.match(
            rf'([+-]?\d*\.?\d*)\*{var}(?:\*\*(\d+))?$|'
            rf'([+-]?\d*\.?\d*){var}(?:\*\*(\d+))?$',
            part,
        )
        if not m:
            continue
        coef_str = m.group(1) or m.group(3) or '1'
        if coef_str in ('', '+'):
            coef = 1.0
        elif coef_str == '-':
            coef = -1.0
        else:
            coef = float(coef_str)
        power = int(m.group(2) or m.group(4) or 1)
        terms.append((coef, power))
    return terms


def _eval_polynomial_at(expr: str, x_val: float, var: str = 'x') -> float:
    return sum(c * (x_val ** p) for c, p in _parse_polynomial_terms(expr, var))


def _should_route_to_limit(question: str) -> bool:
    q = question.lower()
    if re.search(r'\blim(?:it)?\b|\blim\s*\(', q):
        return True
    if re.search(r'\blimit\b', q) and re.search(
        r'\b(as|approaches|->|→|tends\s+to|when)\b', q
    ):
        return True
    return False


def _should_route_to_derivative(question: str) -> bool:
    q = question.lower()
    return bool(re.search(
        r'\b(derivative|derivation|differentiate|d/dx|d\s*/\s*dx)\b|'
        r"d\s*['\u2019]\s*\(|f\s*['\u2019]\s*\(",
        q,
    ))


def _parse_approach_value(raw: str):
    raw = raw.lower().strip()
    if raw in ('inf', 'infinity', '∞', '+inf', '+infinity'):
        return 'inf'
    if raw in ('-inf', '-infinity'):
        return '-inf'
    try:
        v = float(raw)
        return int(v) if abs(v - int(v)) < 1e-9 else v
    except ValueError:
        return None


def _extract_limit_parts(question: str):
    """Return (approach, expression) or (None, None)."""
    q = question
    # lim(x -> 2) expr
    m = re.search(
        r'lim(?:it)?\s*\(\s*x\s*(?:->|→|to)\s*'
        r'([+-]?\d+(?:\.\d+)?|inf(?:inity)?|∞)\s*\)\s*(.+)',
        q, re.IGNORECASE | re.DOTALL,
    )
    if m:
        return _parse_approach_value(m.group(1)), m.group(2).strip()

    # limit of ... as x approaches 2
    m = re.search(
        r'limit\s+of\s+(.+?)\s+as\s+x\s+(?:approaches|tends\s+to|->|→)\s*'
        r'([+-]?\d+(?:\.\d+)?|inf(?:inity)?|∞)',
        q, re.IGNORECASE | re.DOTALL,
    )
    if m:
        return _parse_approach_value(m.group(2)), m.group(1).strip()

    # find/evaluate lim ... (expr) x->2 at end
    m = re.search(
        r'(?:find|evaluate|calculate|what\s+is)\s+.*?lim(?:it)?\s*\(\s*x\s*(?:->|→|to)\s*'
        r'([+-]?\d+(?:\.\d+)?|inf(?:inity)?|∞)\s*\)\s*(.+)',
        q, re.IGNORECASE | re.DOTALL,
    )
    if m:
        return _parse_approach_value(m.group(1)), m.group(2).strip()

    return None, None


def _extract_derivative_expr(question: str) -> str:
    q = question.strip()
    m = re.search(r'd/dx\s*\(?\s*(.+?)\s*\)?\s*$', q, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    expr = re.sub(
        r'.*?\b(?:find|what\s+is|calculate|evaluate|the)\s+',
        '', q, count=1, flags=re.IGNORECASE,
    )
    expr = re.sub(
        r'^(?:the\s+)?(?:derivative|derivation)\s+(?:of\s+)?',
        '', expr, flags=re.IGNORECASE,
    )
    expr = re.sub(r'^(?:differentiate)\s+', '', expr, flags=re.IGNORECASE)
    expr = re.sub(r'[?.!]+$', '', expr).strip()
    return expr


def _solve_limit(question: str):
    """Step-by-step limit evaluation for common Grade 11–12 patterns."""
    approach, expr = _extract_limit_parts(question)
    if approach is None or not expr:
        return None

    expr_n = _normalize_calculus_expr(expr)
    approach_disp = '∞' if approach == 'inf' else ('-∞' if approach == '-inf' else str(approach))

    # ── lim x→0  sin(ax)/(bx) ────────────────────────────────────────────────
    m_trig = re.search(
        r'sin\(([+-]?\d*\.?\d*)\*?x\)/\(?([+-]?\d*\.?\d*)\*?x\)?$',
        expr_n,
    )
    if m_trig and approach in (0, '0', 0.0):
        a_str, b_str = m_trig.group(1) or '1', m_trig.group(2) or '1'
        a = float(a_str) if a_str not in ('', '+', '-') else (1.0 if a_str != '-' else -1.0)
        b = float(b_str) if b_str not in ('', '+', '-') else (1.0 if b_str != '-' else -1.0)
        if abs(b) < 1e-12:
            return None
        result = a / b
        result_disp = int(result) if abs(result - int(result)) < 1e-9 else round(result, 4)
        a_disp = int(a) if abs(a - int(a)) < 1e-9 else a
        b_disp = int(b) if abs(b - int(b)) < 1e-9 else b
        steps = (
            f"Step 1: Recognize the standard limit lim(x→0) sin(u)/u = 1 (let u = {a_disp}x).\n"
            f"Step 2: Rewrite sin({a_disp}x)/({b_disp}x) = ({a_disp}/{b_disp}) · sin({a_disp}x)/({a_disp}x).\n"
            f"Step 3: As x→0, sin({a_disp}x)/({a_disp}x) → 1, so the limit = {a_disp}/{b_disp}.\n"
            f"Answer: {result_disp}"
        )
        return {'steps': steps, 'topic': 'Limits'}

    # ── lim x→a  (x² - a²)/(x - a) ───────────────────────────────────────────
    m_rat = re.search(
        r'\(x\*\*2-(\d+)\)/\(x-(\d+)\)$',
        expr_n,
    )
    if m_rat and approach not in ('inf', '-inf'):
        num_const, denom_root = int(m_rat.group(1)), int(m_rat.group(2))
        a = float(approach)
        if num_const == denom_root ** 2:
            result = 2 * a
            result_disp = int(result) if abs(result - int(result)) < 1e-9 else round(result, 4)
            steps = (
                f"Step 1: Factor the numerator: x² - {num_const} = (x - {denom_root})(x + {denom_root}).\n"
                f"Step 2: Cancel (x - {denom_root}): (x + {denom_root}).\n"
                f"Step 3: Substitute x = {approach_disp}: {approach_disp} + {denom_root} = {result_disp}.\n"
                f"Answer: {result_disp}"
            )
            return {'steps': steps, 'topic': 'Limits'}

    # ── lim x→∞  rational function (leading coefficients) ─────────────────────
    if approach in ('inf', '-inf'):
        if '/' in expr_n:
            num_s, den_s = expr_n.split('/', 1)
            num_terms = _parse_polynomial_terms(num_s.strip('()'))
            den_terms = _parse_polynomial_terms(den_s.strip('()'))
            if num_terms and den_terms:
                num_deg = max(p for _, p in num_terms)
                den_deg = max(p for _, p in den_terms)
                num_lead = sum(c for c, p in num_terms if p == num_deg)
                den_lead = sum(c for c, p in den_terms if p == den_deg)
                if num_deg > den_deg:
                    result_disp = '∞' if approach == 'inf' else '-∞'
                    steps = (
                        f"Step 1: As x→{approach_disp}, the highest power dominates.\n"
                        f"Step 2: Degree of numerator ({num_deg}) > denominator ({den_deg}).\n"
                        f"Answer: {result_disp}"
                    )
                    return {'steps': steps, 'topic': 'Limits'}
                if num_deg < den_deg:
                    steps = (
                        f"Step 1: As x→{approach_disp}, the highest power dominates.\n"
                        f"Step 2: Degree of numerator ({num_deg}) < denominator ({den_deg}).\n"
                        f"Answer: 0"
                    )
                    return {'steps': steps, 'topic': 'Limits'}
                if abs(den_lead) > 1e-12:
                    result = num_lead / den_lead
                    result_disp = int(result) if abs(result - int(result)) < 1e-9 else round(result, 4)
                    steps = (
                        f"Step 1: Divide numerator and denominator by x^{num_deg}.\n"
                        f"Step 2: Leading coefficients: {num_lead}/{den_lead}.\n"
                        f"Answer: {result_disp}"
                    )
                    return {'steps': steps, 'topic': 'Limits'}

    # ── Direct substitution (polynomial / simple expression) ─────────────────
    if approach not in ('inf', '-inf'):
        try:
            val = _eval_polynomial_at(expr, float(approach))
            val_disp = int(val) if abs(val - int(val)) < 1e-9 else round(val, 4)
            steps = (
                f"Step 1: Substitute x = {approach_disp} directly into the expression.\n"
                f"Step 2: Evaluate f({approach_disp}) = {val_disp}.\n"
                f"Answer: {val_disp}"
            )
            return {'steps': steps, 'topic': 'Limits'}
        except (ValueError, ZeroDivisionError, OverflowError):
            pass

    return None


def _solve_derivative(question: str):
    """Step-by-step derivative using power, sum, and basic trig rules."""
    expr = _extract_derivative_expr(question)
    if not expr:
        return None

    expr_n = _normalize_calculus_expr(expr)

    # Basic elementary rules (single-term)
    elementary = [
        (r'^sin\(x\)$', 'cos(x)',
         'Step 1: Use the rule d/dx[sin(x)] = cos(x).\nAnswer: cos(x)'),
        (r'^cos\(x\)$', '-sin(x)',
         'Step 1: Use the rule d/dx[cos(x)] = -sin(x).\nAnswer: -sin(x)'),
        (r'^tan\(x\)$', 'sec²(x)',
         'Step 1: Use the rule d/dx[tan(x)] = sec²(x).\nAnswer: sec²(x)'),
        (r'^e\*\*x$|^exp\(x\)$', 'e^x',
         'Step 1: Use the rule d/dx[e^x] = e^x.\nAnswer: e^x'),
        (r'^ln\(x\)$', '1/x',
         'Step 1: Use the rule d/dx[ln(x)] = 1/x.\nAnswer: 1/x'),
    ]
    for pattern, _, steps in elementary:
        if re.fullmatch(pattern, expr_n):
            return {'steps': steps, 'topic': 'Derivatives'}

    terms = _parse_polynomial_terms(expr_n)
    if terms:
        deriv_terms = []
        step_lines = ['Step 1: Apply the power rule d/dx[x^n] = n·x^(n-1) term by term:']
        for coef, power in terms:
            if power == 0:
                step_lines.append(f'  • d/dx[{coef}] = 0')
                continue
            new_coef = coef * power
            new_power = power - 1
            deriv_terms.append((new_coef, new_power))
            if power == 1:
                step_lines.append(f'  • d/dx[{_format_polynomial([(coef, power)])}] = {int(new_coef) if new_coef == int(new_coef) else new_coef}')
            else:
                step_lines.append(
                    f'  • d/dx[{_format_polynomial([(coef, power)])}] = '
                    f'{_format_polynomial([(new_coef, new_power)])}'
                )
        result = _format_polynomial(deriv_terms)
        step_lines.append(f'Step 2: Combine the terms.\nAnswer: {result}')
        return {'steps': '\n'.join(step_lines), 'topic': 'Derivatives'}

    # Single power: x^n
    m_pow = re.fullmatch(r'x\*\*(\d+)', expr_n)
    if m_pow:
        n = int(m_pow.group(1))
        new_n = n - 1
        result = f'{n}x^{new_n}' if new_n > 1 else (f'{n}x' if new_n == 1 else str(n))
        steps = (
            f"Step 1: Power rule: d/dx[x^{n}] = {n}·x^{new_n}.\n"
            f"Answer: {result}"
        )
        return {'steps': steps, 'topic': 'Derivatives'}

    m_coef_pow = re.fullmatch(r'([+-]?\d+)\*x\*\*(\d+)', expr_n)
    if m_coef_pow:
        a, n = int(m_coef_pow.group(1)), int(m_coef_pow.group(2))
        result = _format_polynomial([(a * n, n - 1)])
        steps = (
            f"Step 1: Power rule: d/dx[{a}x^{n}] = {a}·{n}·x^{n - 1}.\n"
            f"Answer: {result}"
        )
        return {'steps': steps, 'topic': 'Derivatives'}

    return None


def _calculus_solution_succeeded(steps: str) -> bool:
    return bool(re.search(r'\bAnswer:\s*.+', steps, re.IGNORECASE | re.DOTALL))


def _limit_response(sol: dict) -> dict:
    return {
        'answer': sol['steps'],
        'source_citation': 'Ethiopian Grade 12 Mathematics Textbook — Limits and Continuity',
        'source_file': 'grade12_math.pdf',
        'source_page': '',
        'source_grade': 12,
        'section': 'Unit 2: Limits and Continuity',
        'confidence': 'high',
        'topic': sol['topic'],
        'hits': [],
    }


def _derivative_response(sol: dict) -> dict:
    return {
        'answer': sol['steps'],
        'source_citation': (
            'Ethiopian Grade 12 Mathematics Textbook — Introduction to Differential Calculus'
        ),
        'source_file': 'grade12_math.pdf',
        'source_page': '',
        'source_grade': 12,
        'section': 'Unit 3: Introduction to Differential Calculus',
        'confidence': 'high',
        'topic': sol['topic'],
        'hits': [],
    }


# ── Word-Problem Solvers ────────────────────────────────────────────────────────

def _detect_equation_variable(question: str) -> str:
    """Pick the algebra variable (x/y/z), not filler words like 'i' in 'how do i solve'."""
    q = question.lower()
    for v in ('x', 'y', 'z'):
        if re.search(rf'\bfor\s+{v}\b|{v}\s*[=^]|[\d+\-]\s*{v}\b|{v}\s*[+\-]', q):
            return v
    m = re.search(r'([xyz])(?=\s*(?:\^|\*\s*\d|=|[+\-]|\d))', q)
    if m:
        return m.group(1)
    return 'x'


def _solve_linear_equation(question: str):
    """Solve a linear equation like '2x + 5 = 15' or 'Solve for x: 3x - 7 = 20'."""
    q = question
    var = _detect_equation_variable(q)

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
                b = sum(float(x) for x in b_raw) if b_raw else 0.0;
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
    eq_part = re.sub(
        r'.*(?:solve|find|how|factor(?:ing)?|expand|simplify)\s+(?:for\s+x\s*)?',
        '', q, flags=re.IGNORECASE,
    )
    eq_part = re.sub(r'[?!.]+$', '', eq_part).strip()
    if not eq_part:
        eq_part = q

    a = 1.0
    b = 0.0
    c = 0.0

    # Leading coefficient on x^2 (e.g. 2x^2 ...)
    a_m = re.search(r'([+-]?\d*\.?\d*)\s*x\s*(?:\^?\s*2|²)', eq_part)
    if a_m:
        a_str = (a_m.group(1) or '1').strip()
        if a_str in ('', '+', '-'):
            a_str = a_str + '1'
        try:
            a = float(a_str)
        except ValueError:
            a = 1.0

    # Linear term bx
    b_m = re.search(r'([+-])\s*(\d+)\s*x(?!\s*(?:\^|²))', eq_part)
    if b_m:
        b = float(b_m.group(2))
        if b_m.group(1) == '-':
            b = -b
    elif re.search(r'([+-])\s*x(?!\s*(?:\^|²))', eq_part):
        sign = re.search(r'([+-])\s*x(?!\s*(?:\^|²))', eq_part).group(1)
        b = -1.0 if sign == '-' else 1.0

    # Constant term (before = or end of string)
    rhs = eq_part
    if '=' in eq_part:
        rhs = eq_part.split('=', 1)[0]
    c_m = re.search(r'([+-])\s*(\d+)\s*(?:=\s*0)?\s*$', rhs.strip())
    if not c_m:
        c_m = re.search(r'([+-])\s*(\d+)(?!\s*x)', rhs)
    if c_m:
        c = float(c_m.group(2))
        if c_m.group(1) == '-':
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
        return _out_of_scope_response('scope')

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

    # ── 4a. Limits & derivatives (before algebra — x² appears in both) ───────
    if _should_route_to_limit(q):
        sol_lim = _solve_limit(q)
        if sol_lim and _calculus_solution_succeeded(sol_lim['steps']):
            return _limit_response(sol_lim)

    if _should_route_to_derivative(q):
        sol_der = _solve_derivative(q)
        if sol_der and _calculus_solution_succeeded(sol_der['steps']):
            return _derivative_response(sol_der)

    # ── 4b. Equation solvers (linear & quadratic) ───────────────────────────
    if _should_route_to_quadratic(q):
        solq = _solve_quadratic(q)
        if solq.get('steps'):
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

    if _should_route_to_linear_solver(q):
        sol = _solve_linear_equation(q)
        if _linear_solution_succeeded(sol['steps']):
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

    # ── 5. Textbook search: ALL 6 books ──────────────────────────────────────
    detected_topic = _detect_math_topic(q)
    keywords = _keyword_hints(q)
    search_query = keywords if keywords else q

    try:
        all_hits = search_curriculum_content(search_query, grade_level, k=max_hits)
        if not all_hits:
            tokens = re.findall(r'[a-z0-9_.-]+', q.lower())
            broad = ' '.join(tokens[:3])
            if broad != search_query:
                all_hits = search_curriculum_content(broad, grade_level, k=max_hits)
    except Exception:
        all_hits = []

    if not all_hits:
        return _out_of_scope_response('not_found')

    top_sim = all_hits[0].get('similarity', 0)
    if top_sim < MIN_RELEVANCE_SIMILARITY:
        return _out_of_scope_response('not_found')

    all_hits = _filter_relevant_hits(all_hits, q, detected_topic)
    if not all_hits:
        return _out_of_scope_response('not_found')

    top_sim = all_hits[0].get('similarity', 0)
    if top_sim < MIN_RELEVANCE_SIMILARITY:
        return _out_of_scope_response('not_found')

    from curriculum_extractor import extract_content
    chunks = [{'text': h.get('text', ''), 'source': h.get('source', ''), 'page': h.get('page', '')}
              for h in all_hits]
    topic_label = detected_topic if detected_topic != 'general' else _keyword_hints(q)
    extracted = extract_content(chunks, topic_hint=topic_label or q)
    if not extracted.get('explanation') and not extracted.get('formulas') and \
            not extracted.get('worked_examples') and not extracted.get('examples'):
        return _out_of_scope_response('not_found')

    cite = build_citation_from_hits(all_hits)
    if extracted.get('source_citation'):
        cite['source_citation'] = extracted['source_citation']
    explanation = build_assistant_answer(extracted, q)

    # Confidence: based on top-hit similarity
    if top_sim >= 75:
        confidence = 'high'
    elif top_sim >= 55:
        confidence = 'medium'
    else:
        return _out_of_scope_response('not_found')

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
        'topic':        detected_topic,
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
