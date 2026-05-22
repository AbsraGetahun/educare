"""
Part 2: Curriculum Content Extractor
Extracts explanations, examples, and formulas from FAISS search result chunks.
Improves content quality by filtering out metadata and focusing on math content.
Now supports all 6 curriculum textbooks with book-type detection.
"""
import re

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
    'simplify', 'evaluate', 'substitute', 'proof', 'theorem', 'lemma'
]

EXCLUDE_PAGES = list(range(1, 10))

# ── Source-Name Mapping ────────────────────────────────────────────────────────
# Maps every known PDF filename → human-readable book name + grade band
BOOK_INFO = {
    'extreme mathematics grade 9&10.pdf':          ('Extreme Mathematics: Grade 9 & 10',  '9_10', 'extreme'),
    'extreme mathematics grade 11&12.pdf':         ('Extreme Mathematics: Grade 11 & 12', '11_12', 'extreme'),
    'grade9_math.pdf':                              ('Ethiopian Grade 9 Mathematics Textbook',  '9',  'grade'),
    'grade10_math.pdf':                             ('Ethiopian Grade 10 Mathematics Textbook', '10', 'grade'),
    'grade11_math.pdf':                             ('Ethiopian Grade 11 Mathematics Textbook', '11', 'grade'),
    'grade12_math.pdf':                             ('Ethiopian Grade 12 Mathematics Textbook', '12', 'grade'),
}


def _get_book_info(source: str):
    """Return (book_name, grade_band, book_type) for a given source filename."""
    key = source.lower().strip()
    if key in BOOK_INFO:
        return BOOK_INFO[key]
    # Try partial match for filenames with path prefixes
    for k, v in BOOK_INFO.items():
        if k in key or key in k:
            return v
    # Return generic
    return (source.replace('.pdf', '').replace('_', ' ').title(), 'unknown', 'unknown')


def _is_metadata_chunk(text: str, page: int) -> bool:
    """Check if chunk contains metadata or front matter."""
    if page in EXCLUDE_PAGES:
        return True
    text_lower = text.lower()
    for pattern in METADATA_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _contains_math_content(text: str) -> bool:
    """Check if text contains mathematical content."""
    text_lower = text.lower()
    math_term_count = sum(1 for term in MATH_TERMS if term in text_lower)
    has_math_symbols = bool(re.search(r'[=+\-*/^√∫∏∑∞≤≥]', text))
    has_numbers = bool(re.search(r'\d+', text))
    return math_term_count >= 1 or (has_math_symbols and has_numbers)


def _is_likely_prose(text: str) -> bool:
    """Check if text is mostly narrative prose (skip it)."""
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


def _extract_worked_examples(text: str) -> list:
    """Find worked example patterns like 'Example 1:', 'Solve:', 'Example 3' blocks."""
    examples = []
    lines = text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Matches: "Example 1:", "Example 3", "Example", "Worked Example"
        if re.search(r'\b(Example|Worked Example|Solved Example|Sample)\b', line, re.IGNORECASE):
            example_lines = [line]
            j = i + 1
            while j < len(lines) and len(lines[j].strip()) > 0:
                example_lines.append(lines[j].strip())
                j += 1
                if len(example_lines) >= 8:
                    break
            full = ' '.join(example_lines)
            if len(full) > 40:
                examples.append(full[:500])
            i = j
            continue
        i += 1
    return examples


def _extract_explanation(text: str) -> str:
    """Return first 2-3 meaningful sentences containing math content."""
    if not text:
        return ''
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    good = []
    for s in sentences:
        s = s.strip()
        if len(s) < 30:
            continue
        if _is_likely_prose(s):
            continue
        if _contains_math_content(s) or len(s) > 50:
            good.append(s)
    if len(good) < 2:
        good = [s.strip() for s in sentences if len(s.strip()) > 40][:3]
    return ' '.join(good[:3])


def _extract_examples(text: str) -> list:
    """Find lines that look like examples (contain 'Example', numbers, or equations)."""
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
                if len(example_lines) >= 5:
                    break
            full_example = ' '.join(example_lines)
            if len(full_example) > 30:
                examples.append(full_example[:300])
            i = j
            continue
        if re.search(r'\d+\s*[=+\-*/^]\s*\d+', line) or re.search(r'(Solve|Evaluate|Find|Calculate)', line, re.IGNORECASE):
            if len(line) > 20:
                examples.append(line[:250])
        i += 1
    return examples[:4]


def _extract_formulas(text: str) -> list:
    """Find lines that look like formulas (contain = and math symbols)."""
    formulas = []
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        has_equals = '=' in line
        has_math_vars = bool(re.search(r'[a-zA-Z]{2,}', line))
        has_operators = bool(re.search(r'[+\-*/^∫∏∑]', line))
        if has_equals and (has_math_vars or has_operators):
            if len(line) < 180 and line.count(' ') < 25:
                clean_line = line
                if len(clean_line) > 150:
                    clean_line = clean_line[:150] + '...'
                formulas.append(clean_line)
    return formulas[:5]


def extract_content(chunks: list) -> dict:
    """
    Takes a list of FAISS result chunks (each with 'text', 'source', 'page')
    and extracts structured content with improved filtering. Supports ALL 6 textbooks.

    Returns:
        {
          'explanation': str,
          'examples': list[str],
          'formulas': list[str],
          'source_citation': str,
          'book_type': str,         # 'extreme' | 'grade' | 'unknown'
          'book_name': str,         # Human-readable book name
          'grade_band': str,
          'source_file': str,
          'source_page': int|str,
          'source_grade': int|None,
          'worked_examples': list[str],
          'all_sources': list[str],  # all source filenames used
        }
    """
    if not chunks:
        return {
            'explanation': '', 'examples': [], 'formulas': [],
            'source_citation': '', 'book_type': 'unknown',
            'book_name': '', 'grade_band': 'unknown',
            'source_file': '', 'source_page': '', 'source_grade': None,
            'worked_examples': [], 'all_sources': [],
        }

    filtered_chunks = []
    seen_pages = set()
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
        filtered_chunks = chunks

    # Detect book from first chunk
    first_source = filtered_chunks[0].get('source', 'curriculum')
    book_name, grade_band, book_type = _get_book_info(first_source)

    # Detect book type across ALL sources
    all_types = set()
    for c in filtered_chunks:
        _, _, bt = _get_book_info(c.get('source', 'curriculum'))
        all_types.add(bt)
    dominant_type = 'extreme' if 'extreme' in all_types else book_type

    explanation = _extract_explanation(filtered_chunks[0].get('text', ''))
    examples = []
    formulas = []
    worked_examples = []

    for chunk in filtered_chunks:
        text = chunk.get('text', '')
        examples.extend(_extract_examples(text))
        formulas.extend(_extract_formulas(text))
        worked_examples.extend(_extract_worked_examples(text))

    # Deduplicate
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

    first = filtered_chunks[0] if filtered_chunks else chunks[0]
    source = first.get('source', 'curriculum')
    page = first.get('page', '')
    # Build readable citation: book name + page + section
    bn, gb, bt = _get_book_info(source)
    section = ''
    for c in filtered_chunks:
        import re as _re
        m = _re.search(r'Unit\s+\d+\s*:\s*[^\n]+', c.get('text', ''), _re.IGNORECASE)
        if m:
            section = m.group(0).strip()
            break
    if page:
        citation = f'{bn}, page {page}'
    else:
        citation = bn
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
        'source_citation': citation,
        'book_type': dominant_type,
        'book_name': bn,
        'grade_band': grade_band,
        'source_file': source,
        'source_page': page,
        'source_grade': source_grade,
        'all_sources': all_sources,
    }
