"""Grounded Q&A over the interview lines.

The model must cite line IDs with verbatim quotes. Citations are checked in
code; any that fail are dropped. If the model says the answer is not there, or
no citation survives, the tool answers exactly: Not in the interviews.
"""
import re

from .llm import extract_json
from .verify import check, quote_kind

NOT_FOUND = 'Not in the interviews.'

SYSTEM = """You answer questions using ONLY the interview note lines provided. No outside knowledge, no inference beyond what the lines say, no numbers that are not in the lines.
Reply with JSON only:
{"found": true or false, "answer": "...", "citations": [{"id": "...", "quote": "..."}]}
- "answer": at most three plain sentences, in your own words, with no quotation marks.
- Each citation "quote" is copied character for character from the cited line.
- If the lines do not contain the answer, reply {"found": false, "answer": "", "citations": []}.
- Something one interviewee perceives or reports about others is not a fact about the organisation; say whose view it is."""

_STOP = set('a an the of to in on and or for is are was were be what why how who which do does did we our their it this that with by at as from about any all can could would should there they them its'.split())


def _words(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in _STOP and len(w) > 2}


def ask(question, units, llm):
    by_id = {u['id']: u for u in units}
    if llm.mock:
        q = _words(question)
        scored = sorted(((len(q & _words(u['text'])), u) for u in units), key=lambda t: -t[0])
        top = [u for s, u in scored[:3] if s >= 2]
        raw = {'found': bool(top), 'answer': 'TEST MODE: no model called; best keyword matches shown.' if top else '',
               'citations': [{'id': u['id'], 'quote': u['text']} for u in top]}
    else:
        corpus = '\n'.join(f"{u['id']} | {u['speaker']} | {u['text']}" for u in units)
        raw = extract_json(llm.complete(SYSTEM, f'LINES\n{corpus}\n\nQUESTION\n{question}', max_tokens=2000))
    cites, dropped = [], []
    for c in raw.get('citations', []) or []:
        u = by_id.get(str(c.get('id', '')))
        quote = str(c.get('quote', ''))
        status = check(quote, u['text']) if u else 'failed'
        if status in ('exact', 'normalized'):
            cites.append(dict(id=u['id'], speaker=u['speaker'], file=u['file'], line=u['line'], quote=quote,
                              verification=status, kind=quote_kind(quote, u['text'])))
        else:
            dropped.append(dict(id=c.get('id'), quote=quote))
    answer = (raw.get('answer') or '').strip()
    if not raw.get('found') or not cites:
        return dict(question=question, found=False, answer=NOT_FOUND, citations=[], dropped=dropped)
    if '"' in answer:
        answer = answer.replace('"', '')
    return dict(question=question, found=True, answer=answer, citations=cites, dropped=dropped)
