"""End-to-end run: files -> line units -> tagged evidence -> verification -> agreement -> Q&A."""
import csv
import datetime
import json
import os

from .ask import ask
from .llm import LLM, MODEL
from .parse import parse_texts
from .tag import agreement, inject_fake, tag_units, verification_summary

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_codebook(path=None):
    with open(path or os.path.join(ROOT, 'config', 'codebook.json'), encoding='utf-8') as f:
        return json.load(f)


def load_gold(path=None):
    path = path or os.path.join(ROOT, 'config', 'gold.csv')
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        return {r['id']: (r['code'], r['text']) for r in csv.DictReader(f)}


def load_questions(path=None):
    path = path or os.path.join(ROOT, 'config', 'questions.txt')
    if not os.path.exists(path):
        return []
    with open(path, encoding='utf-8') as f:
        return [q.strip() for q in f if q.strip() and not q.startswith('#')]


def run(files, codebook=None, gold=None, inject=False, questions=None, llm=None):
    codebook = codebook or load_codebook()
    gold = load_gold() if gold is None else gold
    llm = llm or LLM()
    units = parse_texts(files)
    # human labels only apply to lines whose ID and exact text match the coded GNP set,
    # so new or edited files are never scored against the wrong label
    gold = {u['id']: gold[u['id']][0] for u in units if u['id'] in gold and gold[u['id']][1] == u['text']}
    records, problems = tag_units(units, codebook, llm, gold)
    fake = inject_fake(records) if inject else None
    ver = verification_summary(records)
    agr = agreement(records, gold) if gold else None
    gold_n = len(gold)
    qa = [ask(q, units, llm) for q in (questions or [])]
    return dict(units=units, records=records, problems=problems, verification=ver, agreement=agr, qa=qa,
                injected=fake, codebook=codebook,
                meta=dict(files=sorted(files), lines=len(units), model='TEST MODE (no model called)' if llm.mock else MODEL,
                          mock=llm.mock, calls=llm.calls, gold_lines=gold_n,
                          run_at=datetime.datetime.now().strftime('%Y-%m-%d %H:%M')))
