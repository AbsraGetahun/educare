"""Quick tests for learning-note math formatting."""
from math_format import (
    normalize_latex_escapes,
    truncate_at_sentence,
    is_complete_sentence,
    is_valid_formula_line,
    format_note_html,
)
from curriculum_extractor import extract_content


def test_latex_escapes():
    raw = r'$$\\frac{a}{b}$$'
    out = normalize_latex_escapes(raw)
    assert '\\frac' in out
    assert '\\\\frac' not in out or out.count('\\\\') == 0


def test_truncate_complete():
    text = 'First sentence is complete. Second sentence is also complete. Third one'
    out = truncate_at_sentence(text, 70)
    assert out.endswith('.') or out.endswith('…')
    assert not out.endswith(' Third')


def test_invalid_formula():
    assert not is_valid_formula_line('4 b Plot the points with coordinates')
    assert is_valid_formula_line('y = ax^2 + bx + c')


def test_format_note_html_math():
    html = format_note_html('The formula $x^2 + 1 = y$ applies here.')
    assert 'math-latex' in html
    assert 'x^2' in html


def test_extract_has_steps():
    chunks = [{
        'text': (
            'Unit 3: Quadratic Equations\n'
            'A quadratic equation is an equation of the form ax^2 + bx + c = 0. '
            'There are three methods: factorization method, completing the square, '
            'and the quadratic formula method.\n'
            'Example 1: Solve x^2 - 5x + 6 = 0.\n'
            'Solution: Factor to get (x-2)(x-3)=0 so x=2 or x=3.'
        ),
        'source': 'grade10_math.pdf',
        'page': 45,
    }]
    ext = extract_content(chunks, topic_hint='quadratic equations')
    assert ext['explanation']
    assert is_complete_sentence(ext['explanation']) or len(ext['explanation']) > 80
    assert len(ext['steps']) >= 2


if __name__ == '__main__':
    test_latex_escapes()
    test_truncate_complete()
    test_invalid_formula()
    test_format_note_html_math()
    test_extract_has_steps()
    print('All math_format tests passed.')
