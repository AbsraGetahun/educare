"""
Part 2: Curriculum Content Extractor
Extracts explanations, examples, formulas, and step-by-step notes from FAISS chunks.
"""
import re

from math_format import (
    clean_pdf_text,
    format_math_for_display,
    is_complete_sentence,
    is_valid_formula_line,
    truncate_at_sentence,
)

METADATA_PATTERNS = [
    r'\bAuthors?\s*:',
    r'\bEditor\s*:',
    r'\bEvaluators?\s*:',
    r'\bFederal Democratic Republic of Ethiopia',
    r'\bMinistry of Education',
    r'\bISBN\b',
    r'\bCopyright\b',
    r'\bPublished\b.*\bby\b',
    r'\bFirst edition\b',
]

MATH_TERMS = [
    'equation', 'solve', 'function', 'limit', 'integral', 'derivative',
    'differentiate', 'quadratic', 'linear', 'polynomial', 'algebra',
    'trigonometry', 'calculus', 'differential', 'variable',
    'constant', 'coefficient', 'expression', 'graph', 'axis', 'slope',
    'tangent', 'curve', 'domain', 'range', 'continuous', 'discrete',
    'matrix', 'vector', 'determinant', 'sequence', 'series', 'factor',
    'simplify', 'evaluate', 'substitute', 'proof', 'theorem', 'lemma',
]

EXCLUDE_PAGES = list(range(1, 10))

BOOK_INFO = {
    'extreme mathematics grade 9&10.pdf':          ('Extreme Mathematics: Grade 9 & 10',  '9_10', 'extreme'),
    'extreme mathematics grade 11&12.pdf':         ('Extreme Mathematics: Grade 11 & 12', '11_12', 'extreme'),
    'grade9_math.pdf':                              ('Ethiopian Grade 9 Mathematics Textbook',  '9',  'grade'),
    'grade10_math.pdf':                             ('Ethiopian Grade 10 Mathematics Textbook', '10', 'grade'),
    'grade11_math.pdf':                             ('Ethiopian Grade 11 Mathematics Textbook', '11', 'grade'),
    'grade12_math.pdf':                             ('Ethiopian Grade 12 Mathematics Textbook', '12', 'grade'),
    'grade-9-mathematics-textbook.pdf':           ('Ethiopian Grade 9 Mathematics Textbook',  '9',  'grade'),
    'grade-10-mathematics-textbook.pdf':          ('Ethiopian Grade 10 Mathematics Textbook', '10', 'grade'),
    'grade-11-mathematics-textbook.pdf':          ('Ethiopian Grade 11 Mathematics Textbook', '11', 'grade'),
    'grade-12-mathematics-textbook.pdf':          ('Ethiopian Grade 12 Mathematics Textbook', '12', 'grade'),
}

METHOD_PATTERNS = [
    r'factorization\s+method',
    r'completing\s+the\s+square',
    r'quadratic\s+formula',
    r'power\s+rule',
    r'substitution\s+method',
    r'integration\s+by\s+parts',
    r'direct\s+substitution',
    r'product\s+rule',
    r'chain\s+rule',
]


def _get_book_info(source: str):
    key = source.lower().strip()
    if key in BOOK_INFO:
        return BOOK_INFO[key]
    for k, v in BOOK_INFO.items():
        if k in key or key in k:
            return v
    return (source.replace('.pdf', '').replace('_', ' ').title(), 'unknown', 'unknown')


def _is_metadata_chunk(text: str, page: int) -> bool:
    if page in EXCLUDE_PAGES:
        return True
    for pattern in METADATA_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _contains_math_content(text: str) -> bool:
    text_lower = text.lower()
    math_term_count = sum(1 for term in MATH_TERMS if term in text_lower)
    has_math_symbols = bool(re.search(r'[=+\-*/^√∫∏∑∞≤≥]', text))
    has_numbers = bool(re.search(r'\d+', text))
    return math_term_count >= 1 or (has_math_symbols and has_numbers)


def _is_likely_prose(text: str) -> bool:
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if not lines:
        return False
    name_count = 0
    for line in lines[:5]:
        words = line.split()
        if words and len(words) < 5:
            if all(w[0].isupper() for w in words if w and w[0].isalpha()):
                name_count += 1
    return name_count > 2


def _score_chunk(text: str, topic_hint: str = '') -> int:
    """Higher = better study-note source."""
    t = clean_pdf_text(text)
    if not t:
        return 0
    score = 0
    tl = t.lower()
    if topic_hint:
        for token in re.findall(r'[a-z]{4,}', topic_hint.lower()):
            if token in tl:
                score += 15
    if re.search(r'\b(definition|theorem|note|method|formula)\b', tl):
        score += 20
    if re.search(r'\b(example|solution|solve|evaluate)\b', tl):
        score += 12
    if re.search(r'unit\s+\d+\s*:', t, re.IGNORECASE):
        score += 8
    if _contains_math_content(t):
        score += 10
    if _is_likely_prose(t):
        score -= 25
    if re.search(r'\b(activity|exercise|group\s+work)\b', tl):
        score -= 8
    # Penalize very fragmented PDF lines
    short_lines = sum(1 for ln in t.split('\n') if 0 < len(ln.strip()) < 12)
    if short_lines > 8:
        score -= 15
    return score


def _extract_unit_section(text: str) -> str:
    m = re.search(r'Unit\s+\d+\s*:\s*[^\n]+', text, re.IGNORECASE)
    return m.group(0).strip() if m else ''


def _extract_worked_examples(text: str) -> list:
    examples = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if re.search(r'\b(Example|Worked Example|Solved Example)\s*\d+', line, re.IGNORECASE):
            example_lines = [line]
            j = i + 1
            while j < len(lines):
                nxt = lines[j].strip()
                if not nxt:
                    if len(example_lines) >= 3:
                        break
                    j += 1
                    continue
                if re.match(r'^(Example|Exercise|Activity)\s*\d', nxt, re.IGNORECASE) and j > i + 2:
                    break
                example_lines.append(nxt)
                j += 1
                if len(example_lines) >= 14:
                    break
            full = format_math_for_display(' '.join(example_lines))
            full = truncate_at_sentence(full, 700)
            if len(full) > 50 and is_complete_sentence(full):
                if re.search(r'\bSolution\b', full, re.IGNORECASE) or re.search(
                    r'=\s*[-+]?\d', full
                ):
                    examples.append(full)
            i = j
            continue
        i += 1
    return examples


def _extract_solution_steps(text: str) -> list:
    """Pull numbered steps from Solution / Step blocks."""
    steps = []
    t = clean_pdf_text(text)
    for m in re.finditer(
        r'(?:Step\s*(\d+)[.:]\s*|^(\d+)[.)]\s+)([^\n]+(?:\n(?!\d+[.)]|\s*Step)[^\n]+)*)',
        t,
        re.IGNORECASE | re.MULTILINE,
    ):
        body = format_math_for_display(m.group(3).strip())
        body = truncate_at_sentence(body, 320)
        if len(body) > 25:
            steps.append(body)
    sol = re.search(
        r'\bSolution\b\s*[:\n]?\s*(.+?)(?=\n\s*(?:Example|Exercise|Activity|Unit\s+\d)|\Z)',
        t,
        re.IGNORECASE | re.DOTALL,
    )
    if sol:
        block = format_math_for_display(sol.group(1).strip())
        sentences = re.split(r'(?<=[.!?])\s+', block)
        for s in sentences:
            s = s.strip()
            if len(s) > 30 and _contains_math_content(s):
                steps.append(truncate_at_sentence(s, 280))
                if len(steps) >= 5:
                    break
    return steps[:6]


def _extract_explanation(chunks: list, topic_hint: str = '') -> str:
    """Build a complete overview from the best chunk(s), not a mid-sentence fragment."""
    if not chunks:
        return ''

    ranked = sorted(
        chunks,
        key=lambda c: _score_chunk(c.get('text', ''), topic_hint),
        reverse=True,
    )

    paragraphs = []
    seen = set()
    section_added = False

    for chunk in ranked[:4]:
        text = clean_pdf_text(chunk.get('text', ''))
        if not text:
            continue

        section = _extract_unit_section(text)
        if section and not section_added:
            seen.add(section.lower())
            paragraphs.append(section)
            section_added = True

        sentences = re.split(r'(?<=[.!?])\s+', text)
        good = []
        for s in sentences:
            s = s.strip()
            if len(s) < 35 or len(s) > 400:
                continue
            if _is_likely_prose(s):
                continue
            sl = s.lower()
            if '?' in s or re.search(r'^\s*how to solve\b', sl):
                continue
            if section and section.lower() in sl and len(s) < 150:
                continue
            if s.lower().count('unit ') > 1:
                continue
            if re.search(r'\b(definition|method|formula|means|given by|is defined)\b', sl):
                good.insert(0, s)
            elif _contains_math_content(s):
                good.append(s)
        for s in good[:2]:
            key = s[:80].lower()
            if key not in seen:
                seen.add(key)
                paragraphs.append(s)

        if len(paragraphs) >= 4:
            break

    if not paragraphs:
        text = clean_pdf_text(ranked[0].get('text', ''))
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 40]
        paragraphs = sentences[:3]

    # Deduplicate overlapping unit headers / repeated phrases
    deduped = []
    seen_norm = set()
    for p in paragraphs[:6]:
        norm = re.sub(r'\s+', ' ', p.lower())[:120]
        if norm in seen_norm:
            continue
        seen_norm.add(norm)
        deduped.append(p)

    overview = ' '.join(deduped[:4])
    overview = format_math_for_display(overview)
    return truncate_at_sentence(overview, 900)


def _extract_examples(text: str) -> list:
    examples = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if re.search(r'\bexample\b', line, re.IGNORECASE):
            example_lines = [line]
            j = i + 1
            while j < len(lines) and len(lines[j].strip()) > 0:
                example_lines.append(lines[j].strip())
                j += 1
                if len(example_lines) >= 6:
                    break
            full = format_math_for_display(' '.join(example_lines))
            full = truncate_at_sentence(full, 400)
            if len(full) > 35:
                examples.append(full)
            i = j
            continue
        if re.search(r'\b(Solve|Evaluate|Find|Calculate)\b', line, re.IGNORECASE) and '=' in line:
            ex = format_math_for_display(line)
            if len(ex) > 25:
                examples.append(truncate_at_sentence(ex, 300))
        i += 1
    return examples[:4]


def _extract_formulas(text: str) -> list:
    formulas = []
    for line in text.split('\n'):
        line = format_math_for_display(line.strip())
        if is_valid_formula_line(line):
            formulas.append(line)
    return formulas


def _build_step_by_step(topic_hint: str, chunks: list, explanation: str,
                        formulas: list, worked_examples: list) -> list:
    """Structured learning steps for study notes."""
    steps = []
    topic = (topic_hint or 'this topic').strip()

    if explanation:
        first = re.split(r'(?<=[.!?])\s+', explanation)[0]
        steps.append(
            f'Start with the overview above, then apply these steps for {topic}: '
            f'{truncate_at_sentence(first, 180)}'
        )

    # Method steps from chunk text
    combined = ' '.join(clean_pdf_text(c.get('text', '')) for c in chunks[:3])
    methods_found = []
    for pat in METHOD_PATTERNS:
        m = re.search(pat, combined, re.IGNORECASE)
        if m:
            methods_found.append(m.group(0))
    if methods_found:
        steps.append(
            f'Use these standard methods for {topic}: {", ".join(dict.fromkeys(methods_found))}.'
        )
    elif re.search(r'\b(solve|factor|integrate|differentiate|evaluate)\b', combined, re.IGNORECASE):
        steps.append(f'Identify what the problem asks, then apply the rules for {topic} step by step.')

    if formulas:
        key = formulas[0]
        steps.append(f'Key formula to remember: {key}')
        if len(formulas) > 1:
            steps.append(f'Also useful: {formulas[1]}')

    if worked_examples:
        ex = worked_examples[0]
        inner_steps = _extract_solution_steps(ex)
        if inner_steps:
            for s in inner_steps[:3]:
                steps.append(s)
        elif re.search(r'\bExample\s*\d', ex, re.IGNORECASE):
            steps.append(f'Follow this worked example from your textbook: {truncate_at_sentence(ex, 400)}')
    elif explanation:
        steps.append('Practice with similar problems and check each step before moving on.')

    steps.append('Verify your final answer by substituting back or using a quick estimate.')

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for s in steps:
        key = s[:60].lower()
        if key not in seen and len(s.strip()) > 20:
            seen.add(key)
            unique.append(truncate_at_sentence(s, 450))
    return unique[:6]


def extract_content(chunks: list, topic_hint: str = '') -> dict:
    """
    Takes FAISS chunks and returns structured study-note content.
    topic_hint: optional topic name to rank relevant chunks (e.g. from material title).
    """
    empty = {
        'explanation': '', 'examples': [], 'formulas': [],
        'source_citation': '', 'book_type': 'unknown',
        'book_name': '', 'grade_band': 'unknown',
        'source_file': '', 'source_page': '', 'source_grade': None,
        'worked_examples': [], 'all_sources': [], 'steps': [],
    }
    if not chunks:
        return empty

    filtered_chunks = []
    all_sources = []

    for chunk in chunks:
        text = chunk.get('text', '')
        page = chunk.get('page', 0)
        source = chunk.get('source', 'curriculum')
        if _is_metadata_chunk(text, page):
            continue
        if _is_likely_prose(text):
            continue
        if not _contains_math_content(text):
            continue
        filtered_chunks.append(chunk)
        if source not in all_sources:
            all_sources.append(source)

    if not filtered_chunks:
        filtered_chunks = sorted(
            chunks,
            key=lambda c: _score_chunk(c.get('text', ''), topic_hint),
            reverse=True,
        )[:3]
    else:
        filtered_chunks = sorted(
            filtered_chunks,
            key=lambda c: _score_chunk(c.get('text', ''), topic_hint),
            reverse=True,
        )

    first_source = filtered_chunks[0].get('source', 'curriculum')
    book_name, grade_band, book_type = _get_book_info(first_source)

    all_types = set()
    for c in filtered_chunks:
        _, _, bt = _get_book_info(c.get('source', 'curriculum'))
        all_types.add(bt)
    dominant_type = 'extreme' if 'extreme' in all_types else book_type

    explanation = _extract_explanation(filtered_chunks, topic_hint)
    examples = []
    formulas = []
    worked_examples = []

    for chunk in filtered_chunks:
        text = chunk.get('text', '')
        examples.extend(_extract_examples(text))
        formulas.extend(_extract_formulas(text))
        worked_examples.extend(_extract_worked_examples(text))

    seen = set()
    unique_examples = []
    for e in examples:
        if e not in seen:
            seen.add(e)
            unique_examples.append(e)

    seen = set()
    unique_formulas = []
    for f in formulas:
        if f not in seen:
            seen.add(f)
            unique_formulas.append(f)

    seen = set()
    unique_worked = []
    for we in worked_examples:
        if we not in seen:
            seen.add(we)
            unique_worked.append(we)

    steps = _build_step_by_step(
        topic_hint, filtered_chunks, explanation,
        unique_formulas[:5], unique_worked[:3],
    )

    first = filtered_chunks[0]
    source = first.get('source', 'curriculum')
    page = first.get('page', '')
    bn, gb, bt = _get_book_info(source)
    section = ''
    for c in filtered_chunks:
        m = re.search(r'Unit\s+\d+\s*:\s*[^\n]+', c.get('text', ''), re.IGNORECASE)
        if m:
            section = m.group(0).strip()
            break
    citation = f'{bn}, page {page}' if page else bn
    if section:
        citation = f'{citation} — {section}'

    gl = []
    for c in filtered_chunks:
        from rag_service import chunk_grade_levels
        gl.extend(chunk_grade_levels(c))
    source_grade = gl[0] if gl else None

    return {
        'explanation': explanation,
        'examples': unique_examples[:4],
        'formulas': unique_formulas[:5],
        'worked_examples': unique_worked[:3],
        'steps': steps,
        'source_citation': citation,
        'book_type': dominant_type,
        'book_name': bn,
        'grade_band': grade_band,
        'source_file': source,
        'source_page': page,
        'source_grade': source_grade,
        'all_sources': all_sources,
    }
