"""Streamlit front end: run the pipeline on the bundled or uploaded interview
files, view the evidence matrix and verification report, and ask questions.

    streamlit run app.py
"""
import io
import os
import tempfile
import zipfile

import streamlit as st
import streamlit.components.v1 as components

from gnp.ask import ask
from gnp.llm import LLM
from gnp.parse import parse_folder
from gnp.pipeline import load_questions, run
from gnp.report import dashboard, show, summary_line, verification_text, write_outputs

st.set_page_config(page_title='GNP Evidence Pipeline', layout='wide')

if not os.environ.get('ANTHROPIC_API_KEY') and os.environ.get('GNP_MOCK') != '1':
    try:
        os.environ['ANTHROPIC_API_KEY'] = st.secrets['ANTHROPIC_API_KEY']
    except Exception:
        st.error('No API key found. Set ANTHROPIC_API_KEY in your environment (never in this app or the repo).')
        st.stop()

st.title('GNP interview evidence pipeline')
st.caption('Confidential. Every quote is checked against its source line in code.')

with st.sidebar:
    src = st.radio('Interview files', ['Bundled GNP interviews', 'Upload .txt files'])
    uploads = st.file_uploader('Interview .txt files', type='txt', accept_multiple_files=True) if src.startswith('Upload') else None
    inject = st.checkbox('Inject one fabricated quote (proves the check works)')
    go = st.button('Run pipeline', type='primary')

if go:
    if src.startswith('Bundled'):
        files, _ = parse_folder(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'interviews'))
        questions = load_questions()
    else:
        if not uploads:
            st.warning('Upload at least one .txt file.')
            st.stop()
        files = {u.name: u.getvalue().decode('utf-8') for u in uploads}
        questions = []
    with st.spinner('Tagging every line and verifying quotes...'):
        st.session_state.res = run(files, inject=inject, questions=questions)

def outputs_zip(res):
    """The four files run_pipeline.py writes to out/, zipped for download."""
    with tempfile.TemporaryDirectory() as d:
        write_outputs(res, d)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
            for name in sorted(os.listdir(d)):
                z.write(os.path.join(d, name), name)
        return buf.getvalue()


res = st.session_state.get('res')
if not res:
    st.info('Choose the interview files and press Run pipeline.')
    st.stop()

for w in res.get('warnings', []):
    st.warning(w)
st.subheader(summary_line(res['verification']))
tab1, tab2, tab3 = st.tabs(['Evidence matrix', 'Ask the interviews', 'Verification report'])
with tab1:
    html = dashboard(res)
    st.download_button('Download dashboard (HTML)', html, file_name='evidence_matrix.html', mime='text/html')
    st.download_button('Download all outputs (zip)', outputs_zip(res), file_name='gnp_outputs.zip', mime='application/zip',
                       help='evidence_matrix.html, verification_report.txt, evidence.csv and results.json, the same files the command line writes to out/')
    components.html(html, height=1400, scrolling=True)
with tab2:
    q = st.text_input('Question')
    if st.button('Ask') and q.strip():
        with st.spinner('Searching the interviews...'):
            r = ask(q, res['units'], LLM())
        if r['found']:
            st.write(r['answer'])
            for c in r['citations']:
                st.markdown(f"> {show(c['quote'], c['kind'])}\n\n{c['speaker']} · {c['file']} line {c['line']} · "
                            f"{c['kind']} · **{c['verification']}**")
        else:
            st.error(r['answer'])
        if r['dropped']:
            st.caption(f"{len(r['dropped'])} citation(s) failed verification and were dropped.")
with tab3:
    st.code(verification_text(res), language=None)
