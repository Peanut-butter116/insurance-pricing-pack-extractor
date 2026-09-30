import io
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
import streamlit as st
from config import ROOT, FIELDS, LABELS
from parsers.common import parse
from extraction.rules_baseline import extract as rules
from extraction.slm_extractor import extract as slm
from extraction.validated_extractor import validate
from template.populate_template import populate

st.set_page_config(page_title='Pricing Pack Assistant', page_icon='📄', layout='wide')
st.title('SLM Pricing Pack Extraction Assistant')
st.caption('Synthetic feasibility study • Structured extraction • Analyst review required')
st.info('This assistant prepares source information for review. It does not make pricing decisions.')


@st.cache_resource
def model():
    from extraction.slm_backend import SLMBackend
    return SLMBackend()


records_path = ROOT / 'data/ground_truth/records.json'
if not records_path.exists():
    st.warning('Run python -m data.generate_documents first.')
    st.stop()
records = json.loads(records_path.read_text())
options = {r['document_id']: r for r in records}
with st.sidebar:
    st.header('Pricing pack')
    selected = st.selectbox('Benchmark document', list(options))
    upload = st.file_uploader('Or upload PDF, Excel or PowerPoint', type=['pdf', 'xlsx', 'pptx'])
    system = st.selectbox('Extraction system', ['Rules baseline', 'SLM', 'SLM + validation'])
    mode = st.radio('SLM execution', ['Use saved pilot response', 'Run local model'])
record = options[selected]
st.write(f'**Document:** {upload.name if upload else Path(record["path"]).name}')
if not upload:
    st.caption(f'{record["format"].upper()} · Layout {record["layout"]} · {record["split"]} set')
    st.download_button('Download source document', (ROOT / record['path']).read_bytes(), Path(record['path']).name)

identity = (selected, upload.name if upload else None, upload.getvalue() if upload else None, system, mode)
if st.session_state.get('identity') != identity:
    st.session_state.pop('result', None)
    st.session_state['identity'] = identity

if st.button('Run extraction', type='primary'):
    try:
        if upload:
            with tempfile.TemporaryDirectory() as td:
                path = Path(td) / ('upload' + Path(upload.name).suffix.lower())
                path.write_bytes(upload.getvalue())
                document = parse(path)
        else:
            document = parse(ROOT / record['path'])
        error, changes = None, []
        if system == 'Rules baseline':
            raw = rules(document)
        elif mode == 'Use saved pilot response' and not upload:
            from evaluation.benchmark import sha
            manifest = json.loads((ROOT / 'data/frozen_benchmark/manifest.json').read_text())
            if sha(ROOT / record['path']) != manifest['sha256'][record['path']]:
                raise ValueError('Source document changed since the frozen pilot. Saved-response replay is unavailable.')
            audit_path = ROOT / 'results/audit.jsonl'
            if not audit_path.exists():
                raise ValueError('No saved pilot response. Run the benchmark or select Run local model.')
            logs = [json.loads(line) for line in audit_path.read_text().splitlines()]
            log = next((x for x in logs if x['document_id'] == selected), None)
            if not log or not log['attempts']:
                raise ValueError('No model response for this document.')
            raw, error = log['raw_extraction'], log['slm_error']
            st.caption('Replaying an actual saved inference response; no new model call.')
        else:
            with st.spinner('Loading open model and extracting locally…'):
                raw, attempts, error = slm(document, model())
        if error:
            raise ValueError(error)
        validated, changes = validate(raw, document)
        output = validated if system == 'SLM + validation' else raw
        st.session_state['result'] = (output, validated, changes, document)
    except Exception as exc:
        st.error(f'Extraction failed: {exc}')

if 'result' in st.session_state:
    output, validated, changes, document = st.session_state['result']
    st.subheader('Extracted pricing fields')
    st.dataframe(pd.DataFrame([{'Field': label, 'Value': 'Not found' if output[f]['value'] is None else str(output[f]['value']),
                               'Validation': validated[f]['validation_status']} for f, label in zip(FIELDS, LABELS)]), hide_index=True, width='stretch')
    with st.expander('Source evidence and parsed document', expanded=True):
        st.dataframe(pd.DataFrame([{'Field': f, 'Quote': output[f]['source_text'], 'Location': output[f]['source_location']} for f in FIELDS]), hide_index=True, width='stretch')
        st.json(document)
    with st.expander('Validation audit'):
        st.json(changes)
    st.caption('Excel export always uses the validated values displayed by the validation audit. Rejected values remain blank.')
    if st.button('Populate pricing template'):
        try:
            stream = io.BytesIO()
            populate(validated, stream, upload.name if upload else Path(record['path']).name)
            st.download_button('Download populated Excel template', stream.getvalue(), f'{selected}_review.xlsx',
                               'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', on_click='ignore')
        except Exception as exc:
            st.error(f'Template population failed: {exc}')

st.divider()
st.subheader('Saved pilot results')
summary_path = ROOT / 'results/summary.json'
if summary_path.exists():
    summary = json.loads(summary_path.read_text())
    if not summary.get('run_finished'):
        st.warning(f'Pilot still running: {summary.get("processed_documents", 0)} documents processed.')
    if not summary.get('complete'):
        st.warning('The pilot contains extraction failures. They count as incorrect, including missing-field cases.')
    metrics = pd.read_csv(ROOT / 'results/metrics.csv')
    compact = metrics[metrics.split == 'test'][['system', 'field_accuracy', 'numeric_exact_match',
        'missing_field_accuracy', 'unsupported_field_rate', 'provenance_support_rate', 'failure_rate']].copy()
    for column in compact.columns[1:]:
        compact[column] = compact[column].map(lambda value: f'{value:.1%}' if pd.notna(value) else 'N/A')
    st.dataframe(compact, hide_index=True, width='stretch')
    left, right = st.columns(2)
    for column, name in [(left, 'comparison.png'), (right, 'layout_comparison.png')]:
        if (ROOT / 'results' / name).exists():
            column.image(str(ROOT / 'results' / name))
else:
    st.write('Run python -m evaluation.run_pilot to produce measured results.')
