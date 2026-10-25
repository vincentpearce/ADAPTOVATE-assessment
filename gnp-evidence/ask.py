"""Ask the interviews a question.

    python ask.py "Why do grants take so long?"
    python ask.py --input other_folder "question"
"""
import argparse

from gnp.ask import ask
from gnp.llm import LLM
from gnp.parse import parse_folder
from gnp.report import show

ap = argparse.ArgumentParser()
ap.add_argument('question')
ap.add_argument('--input', default='interviews')
args = ap.parse_args()

_, units = parse_folder(args.input)
r = ask(args.question, units, LLM())
print(r['answer'])
for c in r['citations']:
    q = show(c['quote'], c['kind'])
    print(f"  - {q}\n    {c['speaker']} · {c['file']} line {c['line']} · {c['kind']} · {c['verification']}")
if r['dropped']:
    print(f"  ({len(r['dropped'])} citation(s) failed verification and were dropped)")
