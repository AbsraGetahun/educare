"""
Normalize math text from PDF extraction for learning notes and assistant answers.
Fixes broken LaTeX escapes, PDF artifacts, and incomplete sentence truncation.
"""
import html
import re

# Control / odd Unicode from PDF OCR
_CTRL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\ufeff]')
_SPACED_LETTERS_RE = re.compile(
    r'\b([A-Z])\s+([A-Z])\s+([A-Z])(?:\s+[A-Z])*\s+([A-Z])\b'
)
_EXERCISE_PREFIX_RE = re.compile(
    r'^\s*(?:\d+\s*[.)]?\s*)?(?:[a-e]\s*[.)]?\s*)?(?:Exercise|ACTIVITY|Group\s+work)\b',
    re.IGNORECASE,
)
_INCOMPLETE_END_RE = re.compile(
    r'(?:=\s*|\+\s*|\-\s*|/\s*|,\s*|:\s*|\\frac\s*\{?\s*|\\sqrt\s*\{?\s*|\(\s*)$'
)


def normalize_unicode_math_letters(text: str) -> str:
    """Map mathematical italic letters (PDF extraction) to ASCII for KaTeX."""
    out = []
    for ch in text:
        o = ord(ch)
        if 0x1D434 <= o <= 0x1D44D:
            out.append(chr(o - 0x1D434 + ord('A')))
        elif 0x1D44E <= o <= 0x1D467:
            out.append(chr(o - 0x1D44E + ord('a')))
        elif 0x1D7CE <= o <= 0x1D7D7:
            out.append(chr(o - 0x1D7CE + ord('0')))
        else:
            out.append(ch)
    return ''.join(out)


def clean_pdf_text(text: str) -> str:
    """Remove PDF junk and normalize whitespace."""
    if not text:
        return ''
    t = normalize_unicode_math_letters(text)
    t = _CTRL_RE.sub('', t)
    t = t.replace('\r\n', '\n').replace('\r', '\n')
    # Collapse letter-spaced headers like "G r o u p  W o r k"
    t = re.sub(r'(?<=\s)([A-Za-z])\s+(?=[A-Za-z]\s)', '', t)
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()


def normalize_latex_escapes(text: str) -> str:
    """Fix double-escaped LaTeX (e.g. \\\\frac -> \\frac) and standardize delimiters."""
    if not text:
        return ''
    t = text
    # JSON / Python string double-escapes
    while '\\\\' in t and re.search(r'\\\\(?:frac|sqrt|sum|int|lim|left|right|text)', t):
        t = t.replace('\\\\', '\\')
    # Bare \frac without delimiters -> wrap for KaTeX
    if re.search(r'\\frac\{', t) and '$' not in t:
        t = re.sub(
            r'(\\frac\{[^}]+\}\{[^}]+\})',
            r'$\1$',
            t,
        )
    return t


def _unicode_math_substitutions(text: str) -> str:
    """Lightweight readable math without a renderer (fallback)."""
    replacements = [
        (r'\^2\b', '²'),
        (r'\^3\b', '³'),
        (r'\*\*2\b', '²'),
        (r'->', '→'),
        (r'<=\s*', '≤ '),
        (r'>=\s*', '≥ '),
        (r'\\infty', '∞'),
        (r'\\pi', 'π'),
        (r'\\theta', 'θ'),
        (r'\\leq', '≤'),
        (r'\\geq', '≥'),
        (r'\\neq', '≠'),
        (r'\\times', '×'),
        (r'\\div', '÷'),
        (r'\\sqrt\{([^}]+)\}', r'√(\1)'),
    ]
    t = text
    for pat, repl in replacements:
        t = re.sub(pat, repl, t)
    return t


def format_math_for_display(text: str, use_latex_delimiters: bool = True) -> str:
    """
    Clean text for display. When use_latex_delimiters=True, preserves/fixes $...$ for KaTeX.
    """
    t = clean_pdf_text(text)
    t = normalize_latex_escapes(t)
    if not use_latex_delimiters:
        t = _unicode_math_substitutions(t)
    return t


def truncate_at_sentence(text: str, max_len: int = 600) -> str:
    """Truncate at last complete sentence before max_len."""
    t = (text or '').strip()
    if len(t) <= max_len:
        return t
    chunk = t[:max_len]
    # Prefer sentence boundary
    for sep in ('. ', '.\n', '? ', '!\n'):
        idx = chunk.rfind(sep)
        if idx > max_len // 3:
            return chunk[: idx + 1].strip()
    # Word boundary
    sp = chunk.rfind(' ')
    if sp > max_len // 3:
        return chunk[:sp].strip() + '…'
    return chunk.strip() + '…'


def is_complete_sentence(text: str) -> bool:
    t = (text or '').strip()
    if len(t) < 20:
        return False
    if _INCOMPLETE_END_RE.search(t):
        return False
    if t.endswith(('...', '…', '-', '—', ',')):
        return False
    return bool(re.search(r'[.!?]["\']?\s*$', t)) or len(t) > 120


def is_valid_formula_line(line: str) -> bool:
    """Reject exercise labels and incomplete formula fragments."""
    t = (line or '').strip()
    if len(t) < 6 or len(t) > 200:
        return False
    if _EXERCISE_PREFIX_RE.match(t):
        return False
    # Numbered list items from exercises (e.g. "1. (x+3)(x-2)=0")
    if re.match(r'^\s*\d+\s*[.)]\s+', t):
        return False
    # PDF font corruption (Ethiopic syllables used as pseudo-parentheses)
    if re.search(r'[\u1200-\u1380]', t):
        return False
    if not re.search(r'[=≈≤≥<>]', t):
        return False
    if _INCOMPLETE_END_RE.search(t):
        return False
    if re.search(
        r'\bis a\s*$|\bare\s*$|\bwhere\s+[a-z]\s*,|\b(Activity|Graphs of|Make a table)\b',
        t,
        re.IGNORECASE,
    ):
        return False
    if re.match(r'^[a-d]\.\s*[=+]', t, re.IGNORECASE):
        return False
    if re.search(r'\bfunction defined by\b', t, re.IGNORECASE) and t.count('=') < 1:
        return False
    if re.match(r'^\d+\s+[a-z]\s+', t, re.IGNORECASE):
        return False
    words = t.split()
    if len(words) > 22:
        return False
    # Must contain at least one Latin variable or common math token
    if not re.search(r'[a-zA-Z]|\\frac|√|π|²|³|\^', t):
        return False
    return True


def escape_html_text(text: str) -> str:
    return html.escape(text or '', quote=False)


def format_note_html(text: str) -> str:
    """Escape HTML but preserve $...$ math segments for KaTeX rendering."""
    t = format_math_for_display(text)
    if not t:
        return ''

    def _escape_segment(seg: str) -> str:
        parts = re.split(r'(\$[^$]+\$)', seg)
        out = []
        for p in parts:
            if p.startswith('$') and p.endswith('$') and len(p) > 2:
                inner = html.escape(p[1:-1], quote=False)
                out.append(f'<span class="math-latex">{inner}</span>')
            else:
                out.append(html.escape(p, quote=False))
        return ''.join(out)

    blocks = re.split(r'\n\s*\n', t)
    html_parts = []
    for block in blocks:
        block = block.strip()
        if block:
            html_parts.append(f'<p>{_escape_segment(block)}</p>')
    return '\n'.join(html_parts)


def text_to_html_paragraphs(text: str) -> str:
    return format_note_html(text)


def format_note_html_inline(text: str) -> str:
    """Single-line HTML for use inside <code> or list items."""
    html = format_note_html(text)
    return re.sub(r'</?p>', '', html).strip()


def steps_to_html(steps: list) -> str:
    if not steps:
        return ''
    items = []
    for i, step in enumerate(steps, 1):
        body = format_math_for_display(step)
        if not body:
            continue
        items.append(
            f'<li class="rag-step-item">'
            f'<strong>Step {i}:</strong> {format_note_html_inline(body)}'
            f'</li>'
        )
    if not items:
        return ''
    return (
        '<div class="rag-steps"><h3>Step-by-Step Guide</h3>'
        f'<ol class="rag-step-list">{"".join(items)}</ol></div>'
    )
