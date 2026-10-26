"""Write the outputs: evidence_matrix.html (self-contained dashboard), evidence.csv,
verification_report.txt and results.json."""
import csv
import html
import json
import os

LEVEL_ORDER = ['Outcome', 'Cause', 'Strength', 'Context']


def theme_order(codebook):
    lead, outcome = codebook.get('lead', []), codebook.get('outcome', [])
    rest = [c['code'] for c in codebook['codes'] if c['code'] not in lead + outcome and c['code'] != 'NONE']
    rest.sort(key=lambda k: LEVEL_ORDER.index(next(c['level'] for c in codebook['codes'] if c['code'] == k))
              if next(c['level'] for c in codebook['codes'] if c['code'] == k) in LEVEL_ORDER else 9)
    return outcome, lead, rest


def summary_line(v):
    return (f"{v['extracted']} quotes extracted · {v['exact']} verified word-for-word · "
            f"{v['normalized']} matched after normalisation · {v['failed']} failure{'' if v['failed'] == 1 else 's'}")


def show(quote, kind):
    """Display text: quotation marks only for the speaker's own words, never doubled."""
    q = quote.strip()
    if kind == 'Direct quote':
        if len(q) > 1 and q[0] == '"' and q[-1] == '"':
            q = q[1:-1]
        return '“' + q + '”'
    return q


def write_outputs(res, out):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, 'results.json'), 'w', encoding='utf-8') as f:
        json.dump({k: v for k, v in res.items() if k != 'codebook'}, f, indent=1, ensure_ascii=False)
    with open(os.path.join(out, 'evidence.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        names = {c['code']: c.get('short', c['name']) for c in res['codebook']['codes']}
        w.writerow(['theme', 'theme_code', 'quote', 'speaker', 'file', 'line', 'id', 'quote_type', 'verification', 'injected_test'])
        for r in res['records']:
            if r['code'] != 'NONE':
                w.writerow([names.get(r['code'], r['code']), r['code'], r['quote'], r['speaker'], r['file'], r['line'], r['id'], r['kind'],
                            r['verification'], 'yes' if r['injected'] else ''])
    with open(os.path.join(out, 'verification_report.txt'), 'w', encoding='utf-8') as f:
        f.write(verification_text(res))
    with open(os.path.join(out, 'evidence_matrix.html'), 'w', encoding='utf-8') as f:
        f.write(dashboard(res))


def verification_text(res):
    v, m = res['verification'], res['meta']
    lines = ['GNP evidence pipeline: verification report', f"Run {m['run_at']} · model {m['model']}",
             f"Files: {', '.join(m['files'])} ({m['lines']} lines)"]
    counts = res.get('file_counts', {})
    if counts:
        lines += ['Lines read per file: ' + ', '.join(f"{k} {n}" for k, n in counts.items())]
    if res.get('warnings'):
        lines += ['', 'WARNINGS (check these files before trusting the results):'] + ['  ' + w for w in res['warnings']]
    lines += ['', summary_line(v), '']
    for r in v['failures']:
        lines.append(f"FAILED {r['id']} ({r['file']} line {r['line']}){' [injected test quote]' if r['injected'] else ''}")
        lines.append(f"  quote : {r['quote']}")
        lines.append(f"  source: {r['line_text']}")
    for r in res['records']:
        if r['verification'] == 'normalized':
            lines.append(f"NORMALISED {r['id']}: {r['quote']}")
    if res['problems']:
        lines += ['', 'Model output problems (handled):'] + ['  ' + p for p in res['problems']]
    a = res['agreement']
    if a:
        lines += ['', f"Agreement with reference coding: {a['agree']}% of {a['n']} lines (Cohen's kappa {a['kappa']})",
                  'Reference labels were drafted with AI and only partly reviewed by a person (see config/reference_note.txt),',
                  'so this measures consistency, not agreement with independent human coding.']
    return '\n'.join(lines) + '\n'


def e(s):
    return html.escape(str(s), quote=True)


CSS = """
:root{--bg:#f7f6f2;--card:#fff;--ink:#1d2430;--muted:#5f6b7a;--line:#e3e1da;--accent:#1f3a5f;--lead:#9c2b00;
--ok:#1e7a46;--warn:#a86b00;--bad:#b42318;--chip:#eef1f5}
@media (prefers-color-scheme:dark){:root{--bg:#14171c;--card:#1c2027;--ink:#e8eaee;--muted:#9aa4b2;--line:#2c323b;
--accent:#8fb3e0;--lead:#f08a5d;--ok:#4cc27e;--warn:#e0a83a;--bad:#f0685b;--chip:#262c35}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:28px 16px 60px}
h1{font-size:24px;margin:0 0 4px}h2{font-size:17px;margin:32px 0 10px;color:var(--accent)}
.sub{color:var(--muted);font-size:13px}.banner{background:var(--warn);color:#fff;padding:8px 12px;border-radius:6px;margin:12px 0;font-weight:600}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-top:18px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px}
.stat b{display:block;font-size:26px}.stat span{color:var(--muted);font-size:12px}
.vline{margin-top:12px;font-weight:600}.ok{color:var(--ok)}.bad{color:var(--bad)}.warn{color:var(--warn)}
.theme{background:var(--card);border:1px solid var(--line);border-radius:8px;margin:10px 0;overflow:hidden}
.theme>summary{list-style:none;cursor:pointer;padding:12px 14px;display:flex;gap:12px;align-items:baseline;flex-wrap:wrap}
.theme>summary::-webkit-details-marker{display:none}
.code{font-weight:700;color:var(--accent);min-width:28px}.lead .code{color:var(--lead)}
.tname{font-weight:600;flex:1 1 320px}.meta{color:var(--muted);font-size:13px}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:10px;background:var(--chip);color:var(--muted);margin-left:6px}
.tag.lead{background:var(--lead);color:#fff}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:7px 10px;border-top:1px solid var(--line);vertical-align:top}
th{font-size:12px;color:var(--muted);font-weight:600}
.q{max-width:560px}.direct{font-weight:600}.kind{font-size:11px;color:var(--muted);display:block}
.wrap{overflow-x:auto}.dots{letter-spacing:2px}
.qa{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:10px 0}
.qa .ques{font-weight:600}.qa .ans{margin:6px 0}
ul.cites{margin:6px 0 0;padding-left:18px;font-size:14px}
.note{color:var(--muted);font-size:13px}
.num{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:var(--accent);color:var(--card);font-size:13px;font-weight:700;margin-right:8px}
.claim{color:var(--muted);font-size:13px;display:block;font-weight:400;margin-top:2px}
.lede{font-size:16px;max-width:760px;margin:10px 0 0}
"""


def _name(cb, code):
    c = next((x for x in cb['codes'] if x['code'] == code), None)
    return c.get('short', c['name']) if c else code


def _theme_block(code, cb, recs, speakers, number=None, opened=False):
    c = next(x for x in cb['codes'] if x['code'] == code)
    rs = [r for r in recs if r['code'] == code]
    spk = {r['speaker'] for r in rs}
    direct = sum(1 for r in rs if r['kind'] == 'Direct quote')
    rows = ''.join(
        f"<tr><td class='q'><span class='{'direct' if r['kind'] == 'Direct quote' else ''}'>{e(show(r['quote'], r['kind']))}</span>"
        f"<span class='kind'>{ {'Direct quote': 'Interviewee’s own words', 'Note with quoted words': 'Interviewer note with a quoted phrase'}.get(r['kind'], 'Interviewer note')}</span></td>"
        f"<td>{e(r['speaker'])}</td><td>{e(r['file'])}<br><span class='kind'>line {r['line']}</span></td>"
        f"<td class='{ {'exact': 'ok', 'normalized': 'warn'}.get(r['verification'], 'bad')}'>"
        f"{ {'exact': 'Matches source', 'normalized': 'Matches (formatting only)'}.get(r['verification'], 'Not in source')}</td></tr>"
        for r in rs)
    num = f"<span class='num'>{number}</span>" if number else ''
    claim = ''
    return (f"<details class='theme{' lead' if number else ''}'{' open' if opened else ''}><summary>"
            f"<span class='tname'>{num}{e(c.get('short', c['name']))}{claim}</span>"
            f"<span class='meta'>{len(spk)} of {len(speakers)} interviewees · {len(rs)} lines · {direct} in their own words</span></summary>"
            f"<div class='wrap'><table><tr><th>Evidence, exactly as written in the notes</th><th>Who</th><th>Source</th><th>Check</th></tr>"
            f"{rows}</table></div></details>")


def dashboard(res):
    cb, recs, v, m, a = res['codebook'], [r for r in res['records'] if not r['injected']], res['verification'], res['meta'], res['agreement']
    speakers = []
    for u in res['units']:
        if u['speaker'] not in speakers:
            speakers.append(u['speaker'])
    shown = {c['code'] for c in cb['codes'] if c.get('show', True) and c['code'] != 'NONE'}
    has = lambda code: code in shown and any(r['code'] == code for r in recs)
    outcome = [c for c in cb.get('outcome', []) if has(c)]
    lead = [c for c in cb.get('lead', []) if has(c)]
    support = [c for c in cb.get('supporting', []) if has(c)]
    fails = v['failures']
    p = ["<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
         f"<title>GNP Interview Evidence</title><style>{CSS}</style></head><body><main>",
         "<h1>GNP interview evidence</h1>",
         f"<p class='lede'>What the five executive interviews say, grouped by theme. Every quote below has been checked by code against the original interview notes.</p>",
         f"<div class='sub'>{len(m['files'])} interview files · {m['lines']} lines · run {e(m['run_at'])} · Confidential</div>"]
    if m['mock']:
        p.append("<div class='banner'>TEST MODE: no AI model was called. Themes come from the reference coding.</div>")
    for w in res.get('warnings', []):
        p.append(f"<div class='banner'>WARNING: {e(w)}</div>")
    p.append("<div class='stats'>"
             f"<div class='stat'><b>{v['extracted']}</b><span>quotes pulled from the interviews</span></div>"
             f"<div class='stat'><b class='{'bad' if fails else 'ok'}'>{v['exact']}</b><span>match the source word for word</span></div>"
             f"<div class='stat'><b class='{'bad' if fails else 'ok'}'>{len(fails)}</b><span>{'quote' if len(fails) == 1 else 'quotes'} not found in the source</span></div>"
             + (f"<div class='stat'><b>{a['agree']}%</b><span>of lines match the reference coding (AI-drafted labels, partly reviewed by me)</span></div>" if a else '')
             + "</div>")
    if fails:
        p.append("<h2>Quotes that failed the check</h2><div class='wrap'><table><tr><th>Quote returned</th><th>What the source actually says</th></tr>" +
                 ''.join(f"<tr><td class='bad'>{e(r['quote'])}{' <span class=tag>deliberate test</span>' if r['injected'] else ''}</td><td>{e(r['line_text'])}</td></tr>" for r in fails) +
                 "</table></div>")
    if outcome:
        p.append("<h2>What grantees experience</h2>")
        p += [_theme_block(c, cb, recs, speakers, None, True) for c in outcome]
    if lead:
        p.append("<h2>The three causes</h2>")
        p += [_theme_block(c, cb, recs, speakers, i + 1, True) for i, c in enumerate(lead)]
    if support:
        p.append("<h2>Other findings</h2>")
        p += [_theme_block(c, cb, recs, speakers, None, False) for c in support]
    found = [q for q in res['qa'] if q['found']]
    if found:
        p.append("<h2>Questions answered from the interviews</h2>")
        for q in found:
            cites = ''.join(f"<li>{e(show(c['quote'], c['kind']))} <span class='kind'>{e(c['speaker'])} · {e(c['file'])} line {c['line']}</span></li>"
                            for c in q['citations'])
            p.append(f"<div class='qa'><div class='ques'>{e(q['question'])}</div><div class='ans'>{e(q['answer'])}</div><ul class='cites'>{cites}</ul></div>")
    if a and a['disagreements']:
        rows = [d for d in a['disagreements'] if d['model'] in shown or d['human'] in shown]
        if rows:
            p.append(f"<details class='theme'><summary><span class='tname'>Where the AI and the reference coding differ ({len(rows)})</span></summary>"
                     "<div class='wrap'><table><tr><th>Line</th><th>AI put it under</th><th>Reference coding put it under</th></tr>" +
                     ''.join(f"<tr><td>{e(d['text'])}</td><td>{e(_name(cb, d['model']) if d['model'] in shown else 'Not a theme')}</td>"
                             f"<td>{e(_name(cb, d['human']) if d['human'] in shown else 'Not a theme')}</td></tr>" for d in rows) +
                     "</table></div></details>")
    note = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'reference_note.txt')
    ref = ''
    if a and os.path.exists(note):
        with open(note, encoding='utf-8') as f:
            ref = ' ' + f.read().strip()
    p.append("<h2>How this was built</h2><p class='note'>Each bullet in the interview notes is one line. An AI model assigns each line to a theme "
             "and copies the words that support it; code then checks every copied quote against the original line. Bold quotes in curly marks are the "
             "interviewee’s own words; everything else is the interviewer’s note. Only executives were interviewed: no grantees or frontline staff."
             f"{e(ref)}</p>")
    p.append("</main></body></html>")
    return ''.join(p)
