"""Theme tagging: Claude assigns each line to a codebook theme and copies the
evidence span; code then verifies every span against the source line and
scores agreement with the human-coded gold set."""
from collections import Counter

from .llm import extract_json
from .verify import check, quote_kind

SYSTEM = """You code consulting interview notes against a fixed codebook.
Rules:
1. Return exactly one record for every line ID you are given. Never invent IDs.
2. "code" must be one of the codebook codes. Use NONE when no theme fits; never force a fit.
3. "quote" is the shortest span that carries the evidence, copied character for character from that same line: same words, spelling, punctuation and dashes. Do not paraphrase, fix typos, merge lines or add words. Use the whole line if needed. For NONE, quote is "".
Reply with a JSON array only: [{"id": "...", "code": "...", "quote": "..."}]"""


def codebook_text(codebook):
    rows = []
    for c in codebook['codes']:
        rows.append(f"{c['code']} | {c['name']} | {c['definition']} | include: {c['include']} | exclude: {c['exclude']}")
    return '\n'.join(rows)


def tag_units(units, codebook, llm, gold=None):
    valid = {c['code'] for c in codebook['codes']}
    by_file = {}
    for u in units:
        by_file.setdefault(u['file'], []).append(u)
    records, problems = [], []
    for fname, us in by_file.items():
        if llm.mock:
            raw = [{'id': u['id'], 'code': (gold or {}).get(u['id'], 'NONE'),
                    'quote': u['text'] if (gold or {}).get(u['id'], 'NONE') != 'NONE' else ''} for u in us]
        else:
            user = ('CODEBOOK\n' + codebook_text(codebook) + f"\n\nLINES from {fname} ({us[0]['speaker']})\n" +
                    '\n'.join(f"{u['id']} | {u['section']} | {u['text']}" for u in us))
            raw = extract_json(llm.complete(SYSTEM, user, max_tokens=12000))
        ids = {u['id']: u for u in us}
        seen = set()
        for r in raw:
            rid = str(r.get('id', ''))
            if rid not in ids:
                problems.append(f'{fname}: model returned unknown ID {rid!r} (discarded)')
                continue
            if rid in seen:
                problems.append(f'{rid}: duplicate record (first kept)')
                continue
            seen.add(rid)
            code = str(r.get('code', 'NONE')).strip()
            if code not in valid:
                problems.append(f'{rid}: invalid code {code!r} treated as NONE')
                code = 'NONE'
            records.append(_record(ids[rid], code, str(r.get('quote', '') or '')))
        for rid, u in ids.items():
            if rid not in seen:
                problems.append(f'{rid}: no record returned (treated as NONE)')
                records.append(_record(u, 'NONE', ''))
    order = {u['id']: k for k, u in enumerate(units)}
    records.sort(key=lambda r: order[r['id']])
    return records, problems


def _record(u, code, quote):
    rec = dict(id=u['id'], code=code, quote=quote, speaker=u['speaker'], file=u['file'], line=u['line'],
               section=u['section'], line_text=u['text'], injected=False)
    if code == 'NONE':
        rec.update(verification='n/a', kind='')
    else:
        rec['verification'] = check(quote, u['text'])
        rec['kind'] = quote_kind(quote, u['text']) if rec['verification'] == 'exact' else u.get('type', '')
    return rec


def inject_fake(records):
    """Add one fabricated quote so the verifier can be seen catching it."""
    base = next((r for r in records if r['code'] != 'NONE'), records[0])
    fake = dict(base)
    fake.update(code=base['code'] if base['code'] != 'NONE' else 'X1',
                quote='Grantees tell us we are the fastest funder they work with', injected=True)
    fake['verification'] = check(fake['quote'], base['line_text'])
    fake['kind'] = ''
    records.append(fake)
    return fake


def verification_summary(records):
    q = [r for r in records if r['code'] != 'NONE']
    c = Counter(r['verification'] for r in q)
    return dict(extracted=len(q), exact=c['exact'], normalized=c['normalized'], failed=c['failed'],
                failures=[r for r in q if r['verification'] == 'failed'])


def agreement(records, gold):
    pairs = [(r['code'], gold[r['id']]) for r in records if not r['injected'] and r['id'] in gold]
    if not pairs:
        return None
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0
    dis = [dict(id=r['id'], model=r['code'], human=gold[r['id']], text=r['line_text'])
           for r in records if not r['injected'] and r['id'] in gold and r['code'] != gold[r['id']]]
    return dict(n=n, agree=round(po * 100, 1), kappa=round(kappa, 2), disagreements=dis)
