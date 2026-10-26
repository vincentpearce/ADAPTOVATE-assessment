"""Split interview note files into numbered line units.

Each bullet line becomes one unit with a stable ID (I<n>-L<line>), the speaker
from the header, the section heading above it, and the exact text. Bullets may
start with "- ", "• ", "* " or a number ("1." / "1)"). Nothing is rewritten:
the text is the source line minus the bullet marker.

Files that do not match the expected format are never passed silently:
parse_warnings() names every file that yields no lines or has no speaker header.
"""
import os
import re

QUOTED = re.compile(r'"[^"]+"')
BULLET = re.compile(r'^(?:[-•*]|\d{1,3}[.)])\s+')


def _interview_number(filename, fallback):
    m = re.search(r'interview_(\d+)', filename)
    return int(m.group(1)) if m else fallback


def _has_header(first_line):
    """A header is a non-bullet first line such as 'GNP ... | Speaker'."""
    s = first_line.strip()
    return bool(s) and not BULLET.match(s)


def _speaker(header, filename):
    if '|' in header:
        return header.split('|', 1)[1].strip()
    return os.path.splitext(filename)[0]


def line_type(text):
    """Direct quote = whole bullet in quotation marks; mixed = note containing a quoted part."""
    if not QUOTED.search(text):
        return 'Interviewer note'
    if text.startswith('"') and text.endswith('"'):
        return 'Direct quote'
    return 'Note with quoted words'


def parse_text(filename, text, fallback_number=1):
    lines = text.split('\n')
    n = _interview_number(filename, fallback_number)
    header = lines[0] if lines and _has_header(lines[0]) else ''
    speaker = _speaker(header, filename)
    section, units = '', []
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        if (i == 1 and header) or not s:
            continue
        m = BULLET.match(s)
        if m:
            body = s[m.end():]
            units.append(dict(id=f'I{n}-L{i:02d}', file=filename, speaker=speaker, line=i,
                              section=section, type=line_type(body), text=body))
        else:
            section = s
    return units


def parse_texts(files):
    """files: dict of filename -> text. Returns all units in file order."""
    units = []
    for k, name in enumerate(sorted(files), 1):
        units += parse_text(name, files[name], k)
    return units


def parse_warnings(files, units):
    """Plain-language warnings for files the parser could not read as expected."""
    counts = {name: 0 for name in files}
    for u in units:
        counts[u['file']] += 1
    warnings = []
    for name in sorted(files):
        first = files[name].split('\n', 1)[0]
        if counts[name] == 0:
            warnings.append(f'{name}: no bullet lines found, so nothing was read from this file. '
                            'Expected lines starting with "- ", "• ", "* " or "1."')
        if '|' not in first:
            warnings.append(f'{name}: no "| Speaker" header on line 1, so quotes are attributed to the file name')
    return counts, warnings


def parse_folder(folder):
    files = {}
    for name in sorted(os.listdir(folder)):
        if name.endswith('.txt'):
            with open(os.path.join(folder, name), encoding='utf-8') as f:
                files[name] = f.read()
    return files, parse_texts(files)
