"""Run the evidence pipeline end to end.

    python run_pipeline.py                       # interviews/ -> out/
    python run_pipeline.py --input other_folder  # any folder of interview .txt files
    python run_pipeline.py --inject-fake         # add one fabricated quote to prove the check works
"""
import argparse

from gnp.parse import parse_folder
from gnp.pipeline import load_questions, run
from gnp.report import summary_line, write_outputs

ap = argparse.ArgumentParser()
ap.add_argument('--input', default='interviews')
ap.add_argument('--out', default='out')
ap.add_argument('--inject-fake', action='store_true')
ap.add_argument('--no-questions', action='store_true')
args = ap.parse_args()

files, _ = parse_folder(args.input)
res = run(files, inject=args.inject_fake, questions=[] if args.no_questions else load_questions())
write_outputs(res, args.out)
print(summary_line(res['verification']))
if res['agreement']:
    print(f"Agreement with human coding: {res['agreement']['agree']}% (kappa {res['agreement']['kappa']})")
for p in res['problems']:
    print('note:', p)
print(f"Wrote {args.out}/evidence_matrix.html, evidence.csv, verification_report.txt, results.json")
