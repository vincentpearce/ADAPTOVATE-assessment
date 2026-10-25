"""Check every extracted quote against the source text, character for character.

exact       the quote appears in the cited line exactly as written
normalized  it appears only after the rules below (reported separately, never counted as exact)
failed      it does not appear in the cited line
Normalisation rules: curly quotes to straight, en/em dash to hyphen, runs of
whitespace collapsed, enclosing quotation marks added by the model removed.
"""
import re

_MAP = str.maketrans({'“': '"', '”': '"', '‘': "'", '’': "'",
                      '—': '-', '–': '-'})


def normalize(s):
    s = re.sub(r'\s+', ' ', s.translate(_MAP)).strip()
    if len(s) > 1 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1].strip()
    return s


def check(quote, line_text):
    if not quote or not quote.strip():
        return 'failed'
    if quote in line_text:
        return 'exact'
    if normalize(quote) and normalize(quote) in normalize(line_text):
        return 'normalized'
    return 'failed'


def quote_kind(quote, line_text):
    """Is the span the interviewee's own words (inside quotation marks in the source)?"""
    pos = line_text.find(quote)
    if pos < 0:
        return 'unknown'
    end = pos + len(quote)
    for m in re.finditer(r'"[^"]+"', line_text):
        if m.start() <= pos and end <= m.end():
            return 'Direct quote'
    for m in re.finditer(r'"[^"]+"', line_text):
        if pos < m.end() and end > m.start():
            return 'Note with quoted words'
    return 'Interviewer note'
