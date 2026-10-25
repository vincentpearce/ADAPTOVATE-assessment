# GNP evidence pipeline (confidential)

**Run:** `pip install -r requirements.txt`, set `ANTHROPIC_API_KEY`, then `streamlit run app.py` (or `python run_pipeline.py` for the command line).

## What it does
1. **Parses** every interview `.txt` file into numbered line units (`I2-L37` = interview 2, line 37), keeping speaker, section and the exact text.
2. **Tags** each line with Claude against a human-built codebook (`config/codebook.json`), returning a theme code and an evidence span copied from that line. `NONE` is allowed, so lines are never forced into a theme.
3. **Verifies** every span against its source line in code: `exact`, `normalized` (curly quotes, dashes, whitespace only; reported separately) or `failed`.
4. **Scores agreement** with the human coding in `config/gold.csv` (percent and Cohen's kappa) and lists every disagreement. Human labels only apply where the line ID and text match, so new files are never scored against the wrong label.
5. **Answers questions** only from the lines, with cited quotes that are verified in code. No verified citation means the answer is exactly `Not in the interviews.`

## Outputs (`out/`)
`evidence_matrix.html` (self-contained dashboard), `verification_report.txt`, `evidence.csv`, `results.json`.

## Commands
```
python run_pipeline.py                         # interviews/ -> out/
python run_pipeline.py --input new_folder      # any folder of interview .txt files
python run_pipeline.py --inject-fake           # adds one fabricated quote; report shows 1 failure
python ask.py "Why do grants take so long?"
streamlit run app.py                           # upload files, run, view matrix, ask questions
```
`GNP_MOCK=1` runs an offline test mode (no model called, clearly labelled) used during development. `GNP_MODEL` overrides the model.

## Assumptions and limits
- Interview files follow the same format: a header line ending `| <Speaker>`, section headings, bullets starting `- `.
- Quotation marks are shown only where the source line has them. Everything else is an interviewer note, not the speaker's own words.
- Five executive interviews only: no grantees or frontline staff. Fact pack figures are not used by the pipeline.
- The codebook is GNP-specific. On unrelated material most lines will come back `NONE`, which is the intended behaviour.
- Never commit an API key. Use an environment variable or `.streamlit/secrets.toml` (git-ignored).
