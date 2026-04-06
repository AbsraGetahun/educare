"""
Part 2: Curriculum Content Extractor
Extracts explanations, examples, and formulas from FAISS search result chunks.
"""
import re


def extract_content(chunks: list) -> dict:
    """
    Takes a list of FAISS result chunks (each with 'text', 'source', 'page')
    and extracts structured content.

    Returns:
        {
          'explanation': str,
          'examples': list[str],
          'formulas': list[str],
          'source_citation': str
        }
    """
    if not chunks:
        return {
            'explanation': '',
            'examples': [],
            'formulas': [],
            'source_citation': ''
        }

    explanation = _extract_explanation(chunks[0].get('text', ''))
    examples = []
    formulas = []

    for chunk in chunks:
        text = chunk.get('text', '')
        examples.extend(_extract_examples(text))
        formulas.extend(_extract_formulas(text))

    # Deduplicate while preserving order
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

    # Build citation from first chunk
    first = chunks[0]
    source = first.get('source', 'curriculum')
    page = first.get('page', '')
    citation = f"{source}, page {page}" if page else source

    return {
        'explanation': explanation,
        'examples': unique_examples[:4],
        'formulas': unique_formulas[:5],
        'source_citation': citation
    }


def _extract_explanation(text: str) -> str:
    """Return first 2-3 meaningful sentences from the chunk."""
    if not text:
        return ''
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    # Filter out very short or noisy lines
    good = [s.strip() for s in sentences if len(s.strip()) > 20]
    return ' '.join(good[:3])


def _extract_examples(text: str) -> list:
    """Find lines that look like examples (contain 'Example', numbers, or equations)."""
    examples = []
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line or len(line) < 10:
            continue
        # Lines with 'example' keyword
        if re.search(r'\bexample\b', line, re.IGNORECASE):
            examples.append(line[:200])
        # Lines that look like math expressions (contain =, numbers, operators)
        elif re.search(r'\d+\s*[=+\-*/^]\s*\d+', line):
            examples.append(line[:200])
    return examples[:4]


def _extract_formulas(text: str) -> list:
    """Find lines that look like formulas (contain = and math symbols)."""
    formulas = []
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        # Lines with = sign and math-like content
        if '=' in line and re.search(r'[a-zA-Z\d]', line):
            # Avoid very long prose sentences
            if len(line) < 150 and line.count(' ') < 20:
                formulas.append(line[:150])
    return formulas[:5]
