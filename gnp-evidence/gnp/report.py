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
        w.writerow(['theme', 'quote', 'speaker', 'file', 'line', 'id', 'quote_type', 'verification', 'injected_test'])
        for r in res['records']:
            if r['code'] != 'NONE':
                w.writerow([r['code'], r['quote'], r['speaker'], r['file'], r['line'], r['id'], r['kind'],
                            r['verification'], 'yes' if r['injected'] else ''])
    with open(os.path.join(out, 'verification_report.txt'), 'w', encoding='utf-8') as f:
        f.write(verification_text(res))
    with open(os.path.join(out, 'evidence_matrix.html'), 'w', encoding='utf-8') as f:
        f.write(dashboard(res))


def verification_text(res):
    v, m = res['verification'], res['meta']
    lines = ['GNP evidence pipeline: verification report', f"Run {m['run_at']} · model {m['model']}",
             f"Files: {', '.join(m['files'])} ({m['lines']} lines)", '', summary_line(v), '']
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
        lines += ['', f"Agreement with human coding: {a['agree']}% of {a['n']} lines (Cohen's kappa {a['kappa']})"]
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
"""


def _theme_block(code, cb, recs, speakers, lead, opened):
    c = next(x for x in cb['codes'] if x['code'] == code)
    rs = [r for r in recs if r['code'] == code]
    spk = {r['speaker'] for r in rs}
    dots = ''.join('●' if s in spk else '○' for s in speakers)
    direct = sum(1 for r in rs if r['kind'] == 'Direct quote')
    rows = ''.join(
        f"<tr><td class='q'><span class='{'direct' if r['kind'] == 'Direct quote' else ''}'>"
        f"{e(show(r['quote'], r['kind']))}</span>"
        f"<span class='kind'>{e(r['kind'])}</span></td><td>{e(r['speaker'])}</td>"
        f"<td>{e(r['file'])}<br><span class='kind'>line {r['line']} · {e(r['id'])}</span></td>"
        f"<td class='{ {'exact': 'ok', 'normalized': 'warn'}.get(r['verification'], 'bad')}'>{e(r['verification'])}</td></tr>"
        for r in rs)
    tag = "<span class='tag lead'>lead theme</span>" if lead else f"<span class='tag'>{e(c['level'])}</span>"
    return (f"<details class='theme{' lead' if lead else ''}'{' open' if opened else ''}><summary>"
            f"<span class='code'>{e(code)}</span><span class='tname'>{e(c['name'])}{tag}</span>"
            f"<span class='meta'><span class='dots' title='speakers'>{dots}</span> {len(spk)} of {len(speakers)} speakers · "
            f"{len(rs)} lines · {direct} direct quotes</span></summary>"
            f"<div class='wrap'><table><tr><th>Evidence (verbatim)</th><th>Speaker</th><th>Source</th><th>Check</th></tr>"
            f"{rows or '<tr><td colspan=4>No lines</td></tr>'}</table></div></details>")


def dashboard(res):
    cb, recs, v, m, a = res['codebook'], [r for r in res['records'] if not r['injected']], res['verification'], res['meta'], res['agreement']
    speakers = []
    for u in res['units']:
        if u['speaker'] not in speakers:
            speakers.append(u['speaker'])
    outcome, lead, rest = theme_order(cb)
    none_n = sum(1 for r in recs if r['code'] == 'NONE')
    p = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
         f"<title>GNP Evidence Matrix</title><style>{CSS}</style></head><body><main>",
         "<h1>GNP interview evidence matrix</h1>",
         f"<div class='sub'>{len(m['files'])} interview files · {m['lines']} lines · model: {e(m['model'])} · run {e(m['run_at'])}. Confidential.</div>"]
    if m['mock']:
        p.append("<div class='banner'>TEST MODE: no model was called. Tags come from the human-coded set, so agreement is 100% by construction.</div>")
    p.append("<div class='stats'>"
             f"<div class='stat'><b>{v['extracted']}</b><span>quotes extracted</span></div>"
             f"<div class='stat'><b class='ok'>{v['exact']}</b><span>verified word-for-word</span></div>"
             f"<div class='stat'><b class='warn'>{v['normalized']}</b><span>matched after normalisation</span></div>"
             f"<div class='stat'><b class='{'bad' if v['failed'] else 'ok'}'>{v['failed']}</b><span>failures</span></div>"
             + (f"<div class='stat'><b>{a['agree']}%</b><span>agreement with human coding (κ {a['kappa']}, {a['n']} lines)</span></div>" if a else '')
             + "</div>")
    p.append(f"<div class='vline'>{e(summary_line(v))}</div>")
    if v['failures']:
        p.append("<h2>Failed checks</h2><div class='wrap'><table><tr><th>ID</th><th>Quote returned</th><th>Source line</th></tr>" +
                 ''.join(f"<tr><td>{e(r['id'])}{' <span class=tag>injected test</span>' if r['injected'] else ''}</td><td class='bad'>{e(r['quote'])}</td><td>{e(r['line_text'])}</td></tr>" for r in v['failures']) +
                 "</table></div>")
    p.append("<h2>Outcome</h2>")
    p += [_theme_block(c, cb, recs, speakers, False, True) for c in outcome]
    p.append("<h2>Lead themes</h2>")
    p += [_theme_block(c, cb, recs, speakers, True, True) for c in lead]
    p.append("<h2>Supporting themes and context</h2>")
    p += [_theme_block(c, cb, recs, speakers, False, False) for c in rest]
    p.append(f"<p class='note'>{none_n} lines fit no theme.</p>")
    if res['qa']:
        p.append("<h2>Questions answered from the interviews</h2>")
        for q in res['qa']:
            cites = ''.join(f"<li>{e(show(c['quote'], c['kind']))} "
                            f"<span class='kind'>{e(c['speaker'])} · {e(c['file'])} line {c['line']} · {e(c['kind'])} · {e(c['verification'])}</span></li>"
                            for c in q['citations'])
            p.append(f"<div class='qa'><div class='ques'>{e(q['question'])}</div><div class='ans{'' if q['found'] else ' bad'}'>{e(q['answer'])}</div>"
                     f"{'<ul class=cites>' + cites + '</ul>' if cites else ''}"
                     f"{'<div class=note>' + str(len(q['dropped'])) + ' citation(s) failed verification and were dropped.</div>' if q['dropped'] else ''}</div>")
    if a and a['disagreements']:
        p.append(f"<h2>Where the model and the human coder disagree ({len(a['disagreements'])})</h2>"
                 "<details class='theme'><summary><span class='tname'>Show disagreements</span></summary><div class='wrap'><table>"
                 "<tr><th>ID</th><th>Model</th><th>Human</th><th>Line</th></tr>" +
                 ''.join(f"<tr><td>{e(d['id'])}</td><td>{e(d['model'])}</td><td>{e(d['human'])}</td><td>{e(d['text'])}</td></tr>" for d in a['disagreements']) +
                 "</table></div></details>")
    p.append("<h2>Method and limits</h2><p class='note'>Each bullet in the interview files is one line unit with a fixed ID. "
             "The model assigns a theme from a human-built codebook and copies the evidence span; code then checks every span "
             "against its source line. Exact matches count as verified; normalised matches (curly quotes, dashes, whitespace) are shown "
             "separately; anything else fails. Quotation marks are shown only where the source line has them: everything else is an "
             "interviewer note, not the speaker's own words. Notes are executive interviews only: no grantees or frontline staff were "
             "interviewed. Q&amp;A answers only from these lines and replies 'Not in the interviews.' when no verified citation exists.</p>")
    p.append("</main></body></html>")
    return ''.join(p)
