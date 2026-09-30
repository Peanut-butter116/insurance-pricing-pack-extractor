"""Render an honest report from saved finished results; never manufacture measurements."""
import json
from pathlib import Path
import pandas as pd
from config import ROOT


def table(frame, columns):
    lines = ['| ' + ' | '.join(columns) + ' |', '| ' + ' | '.join('---' for _ in columns) + ' |']
    for _, row in frame.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if pd.isna(value):
                text = 'N/A'
            elif column.endswith(('accuracy', 'rate', 'match')):
                text = f'{value * 100:.1f}%'
            else:
                text = str(value)
            values.append(text.replace('|', '/').replace('\n', ' '))
        lines.append('| ' + ' | '.join(values) + ' |')
    return '\n'.join(lines)


def write(directory=ROOT / 'results'):
    summary = json.loads((directory / 'summary.json').read_text())
    if not summary.get('run_finished'):
        raise ValueError('Refusing to write final report from an unfinished run')
    metrics = pd.read_csv(directory / 'metrics.csv')
    formats = pd.read_csv(directory / 'metrics_by_format.csv')
    layouts = pd.read_csv(directory / 'metrics_by_layout.csv')
    preds = pd.read_csv(directory / 'predictions.csv', keep_default_na=False)
    test = metrics[metrics.split == 'test']
    records = json.loads((ROOT / 'data/ground_truth/records.json').read_text())
    audit = [json.loads(line) for line in (directory / 'audit.jsonl').read_text().splitlines()]
    total_missing = sum(v is None for r in records for v in r['values'].values())
    missing_docs = sum(any(v is None for v in r['values'].values()) for r in records)
    partial_dates = sum(len(r['partial_dates']) for r in records)
    overview = table(test, ['system', 'documents', 'evaluated_fields', 'field_accuracy', 'numeric_exact_match',
                            'date_accuracy', 'missing_field_accuracy', 'unsupported_field_rate',
                            'provenance_support_rate', 'document_complete_accuracy', 'failure_rate'])
    failures = [a for a in audit if a.get('slm_error')]
    attempts = [attempt for a in audit for attempt in a['attempts']]
    durations = [sum(a.get('seconds', 0) for a in log['attempts']) for log in audit if log['attempts']]
    model = summary['model']
    hardware = summary.get('hardware', {})
    conclusion = 'Interpret the measured table above alongside its coverage and failure rates; do not transfer conclusions from another run.'
    if set(test.system) == {'rules', 'slm', 'validated'}:
        t = test.set_index('system')
        unseen = layouts[(layouts.split == 'test') & (layouts.layout_group == 'unseen D')].set_index('system')
        conclusion = (
            f'On the held-out test set, rules achieved {t.loc["rules", "field_accuracy"]:.1%} field accuracy against '
            f'{t.loc["slm", "field_accuracy"]:.1%} for the SLM. Date accuracy was '
            f'{t.loc["slm", "date_accuracy"]:.1%} for the SLM and {t.loc["rules", "date_accuracy"]:.1%} for rules. '
            f'Validation changed unsupported predictions on missing fields from {t.loc["slm", "unsupported_field_rate"]:.1%} '
            f'to {t.loc["validated", "unsupported_field_rate"]:.1%}, while changing retained non-null values from '
            f'{int(t.loc["slm", "non_null_predictions"])} to {int(t.loc["validated", "non_null_predictions"])} '
            f'and overall accuracy to {t.loc["validated", "field_accuracy"]:.1%}. '
            f'The SLM document failure rate was {t.loc["slm", "failure_rate"]:.1%}. '
        )
        if {'slm', 'rules'} <= set(unseen.index):
            conclusion += (f'On unseen D, the SLM achieved {unseen.loc["slm", "field_accuracy"]:.1%} against '
                           f'{unseen.loc["rules", "field_accuracy"]:.1%} for rules. Consider both this relative comparison '
                           'and the absolute accuracy before drawing a generalisation claim.')
    sections = [
        '# Pilot report: SLM Pricing Pack Extraction Assistant',
        '## Scope and status',
        f'This is an executed synthetic feasibility study, not a simulated result. The run processed {summary["processed_documents"]} documents. '
        f'{len(failures)} SLM document(s) failed both permitted attempts. Those failures remain in the results and count as incorrect. '
        'No production performance or superiority claim follows from this pilot.',
        '## Model and hardware',
        f'- Model: `{model.get("model_id")}`; revision `{model.get("revision")}`.\n'
        f'- Parameters: {model.get("parameters", 0):,}; dtype `{model.get("dtype")}`; device `{model.get("device")}`.\n'
        f'- Hardware: {hardware.get("cpu", model.get("processor", "not recorded"))}, memory {hardware.get("memory_gb", "not recorded")} GB; `{summary["platform"]}`.\n'
        f'- Python {hardware.get("python", "not recorded")}; PyTorch `{model.get("torch")}`. Exact installed versions are in `requirements-lock.txt`.\n'
        '- Greedy decoding, seed 20260930, maximum 1,200 generated tokens, two attempts maximum, no fine-tuning.\n'
        f'- Run began: {summary["started_utc"]}. Benchmark SHA-256: `{summary["benchmark_manifest_sha256"]}`.\n'
        f'- Total attempts: {len(attempts)}; schema-valid attempts: {sum(bool(a.get("success")) for a in attempts)}.\n'
        f'- Mean model generation time per document, including retries and excluding initial model load: {sum(durations)/len(durations):.2f} seconds. '
        f'Total generation: {sum(durations)/60:.1f} minutes. Token counts and per-attempt latency are in the audit.',
        '## Dataset',
        f'60 unique records and 60 documents: 20 PDF, 20 Excel, 20 PowerPoint; four layout families. '
        f'Eight fields give 480 decisions per system, 1,440 across the three systems. '
        f'{total_missing} null field labels across {missing_docs} documents include {partial_dates} month/year-only policy starts. '
        '30 development and 30 test documents; test has 15 seen A–C and 15 unseen D. Each format has ten test documents. '
        'Labels are known by construction, and hidden from every extraction system.',
        '## Headline test results', overview,
        'Accuracy denominators: all 240 test fields for field accuracy; only non-null numeric/date truth for their exact-match metrics. '
        'Missing accuracy and unsupported rate use null-truth fields. Failed null placeholders earn no accuracy credit. '
        'Provenance rate is conditional on non-null predictions, so a stricter validator can increase it by rejecting correct values. '
        'See the CSV denominator columns before comparing rates.',
        '## Results by format (test)',
        table(formats[formats.split == 'test'], ['system', 'format', 'documents', 'field_accuracy', 'numeric_exact_match', 'missing_field_accuracy', 'unsupported_field_rate', 'failure_rate']),
        '## Seen versus unseen layouts (test)',
        table(layouts[layouts.split == 'test'], ['system', 'layout_group', 'documents', 'field_accuracy', 'missing_field_accuracy', 'provenance_support_rate']),
        'Layout D was excluded from development and examples. It changes both information order and presentation. '
        'Its generator was necessarily known to the engineer; it is not a blind external insurer test. '
        'No prompts, extraction rules or validation rules were tuned after inspecting holdout results.',
        '## Development results (not headline test performance)',
        table(metrics[metrics.split == 'development'], ['system', 'field_accuracy', 'numeric_exact_match', 'missing_field_accuracy', 'unsupported_field_rate', 'failure_rate']),
        '## Concrete extraction examples',
    ]
    good = preds[(preds.split == 'test') & (preds.system == 'slm') & (preds.correct == True) & (preds.truth_missing == False)]
    sections.append('Successful SLM field examples:\n\n' + table(good.head(4), ['document_id', 'field', 'ground_truth', 'predicted_value', 'source_text', 'source_location']))
    bad = preds[(preds.split == 'test') & (preds.system == 'slm') & (preds.correct == False) & (preds.failed == False)]
    sections.append('Incorrect SLM field examples (including unsupported values where present):\n\n' + table(bad.head(6), ['document_id', 'field', 'ground_truth', 'predicted_value', 'source_text', 'source_location']))
    joined = preds[preds.system == 'slm'].merge(preds[preds.system == 'validated'], on=['document_id','field'], suffixes=('_raw','_validated'))
    rejected_correct = joined[(joined.correct_raw == True) & (joined.correct_validated == False)]
    fixes = joined[(joined.correct_raw == False) & (joined.correct_validated == True)]
    sections += ['## Validation tradeoff and unsupported extraction',
        f'Across development plus test, validation converted **{len(fixes)} incorrect decisions to correct decisions**, '
        f'and converted **{len(rejected_correct)} correct decisions to incorrect decisions**. '
        'These counts include null decisions and describe the observed validator, not an assumed benefit.',
        'Examples where validation rejected a correct raw value:\n\n' + table(rejected_correct.head(4), ['document_id','field','predicted_value_raw','source_text_raw','source_location_raw','validation_status_validated']),
        'Examples where validation improved correctness:\n\n' + table(fixes.head(4), ['document_id','field','predicted_value_raw','predicted_value_validated','validation_status_validated']),
        'A non-null prediction on null truth is the specified unsupported-field proxy. Wrong numbers on present fields and wrong concept assignments are separate errors; this proxy does not capture them. '
        'Quote matching is only a first check. It cannot certify the semantic relationship between a quote and the requested field. '
        'Rejecting paraphrases and imprecise locations can remove correct values, while a copied real value for the wrong concept can pass.',
        '## Explicit failures',
        '\n'.join(f'- `{a["document_id"]}`: {a["slm_error"]}. Last attempt: ' + a['attempts'][-1].get('error','').split('\n')[0] for a in failures) or 'No document-level SLM failures recorded.',
        'Invalid first attempts and successful retries are also retained in the audit. The evaluator finishes all documents before returning a non-zero exit status if failures occurred.',
        '## Research interpretation',
        conclusion,
        'The appropriate conclusion is the measured balance between extraction accuracy, source support and analyst review effort. '
        'Simple label/value extraction remains a useful baseline. A small model can interpret narrative and reordered content, but its actual reliability must include JSON failures and unsupported or imprecise evidence. '
        'The validator demonstrates traceable abstention, not a guarantee of improved overall accuracy. Its support rate is conditioned on values it retained. '
        'Compare the seen/unseen table directly; a model that still performs poorly on both is not evidence of successful generalisation. '
        'This small, correlated benchmark does not support claims of statistical significance or production readiness.',
        '## What worked',
        'The complete document-to-template workflow runs locally, preserves missing values and real zeros, expands supported units, retains source locations, produces real paired model/validator results, and exposes failures. '
        'The Streamlit interface can replay saved real outputs for a fast mentor demonstration, or run live inference. '
        'The template export preserves typed dates, percentages and amounts with source and validation columns.',
        '## Limitations',
        '- Synthetic wording, repeated sentence structures and simple tables underrepresent real broker packs.\n'
        '- Sixty documents, only thirty held out and fifteen unseen-layout examples; field decisions within a document are correlated.\n'
        '- Eight fields, one 1.5B model, one hardware configuration and no fine-tuning comparison.\n'
        '- No real pricing analyst evaluation, OCR, complex spreadsheet formulas, image-text slides or authorised insurer data.\n'
        '- Reading order, text segmentation and number-format reconstruction can affect extraction.\n'
        '- Provenance matching is lexical, not semantic; conservative checks can reduce coverage.\n'
        '- The rules baseline uses label-before-value patterns and has limited narrative grammar. A stronger rules baseline is an important next comparison.\n'
        '- Greedy decoding and pinned weights improve reproducibility but device/library differences can still change output.\n'
        '- Render checks covered representative files for every format/layout; this does not prove compatibility with all Office versions.',
        '## Suggested 12-week research plan',
        '1. Weeks 1–2: analyst workflow interviews, authorised data access, schema and review criteria.\n'
        '2. Weeks 3–4: larger realistic benchmark with insurer/template-separated splits; freeze an external test set.\n'
        '3. Weeks 5–6: stronger rules, constrained output and 1.5B/3B/7B model comparison.\n'
        '4. Weeks 7–8: evidence grounding, OCR/multimodal parsing if failures justify it; QLoRA only for a demonstrated persistent gap.\n'
        '5. Weeks 9–10: blinded analyst review study, review-time savings, error severity and latency/cost measurement.\n'
        '6. Weeks 11–12: final frozen evaluation, uncertainty analysis and operational recommendations.',
        '## Reproduction and key files',
        '`python -m evaluation.run_pilot` executes the experiment; `python -m evaluation.write_report` refreshes this report from finished saved results. '
        '`streamlit run app/streamlit_app.py` starts the demo. See README for installation and alternate models.\n\n'
        '- `results/predictions.csv`: every field decision, truth, output, evidence and failure status.\n'
        '- `results/metrics.csv`, `metrics_by_format.csv`, `metrics_by_layout.csv`: split-specific measured metrics.\n'
        '- `results/metrics_by_field.csv`, `metrics_by_layout_family.csv`: additional diagnostic breakdowns.\n'
        '- `results/comparison.png`, `layout_comparison.png`: test results charts.\n'
        '- `results/audit.jsonl`: raw model outputs, retries, errors and validator changes.\n'
        '- `results/summary.json`: model, hashes, environment and run status.\n'
        '- `template/pricing_template.xlsx`: blank analyst review workbook.\n'
        '- `results/example_pricing_review.xlsx`: populated example from a saved actual model response.\n'
        '- `docs/research_protocol.md`: design and metric definitions.',
    ]
    (ROOT / 'docs/pilot_report.md').write_text('\n\n'.join(sections) + '\n')
    readme = ROOT / 'README.md'
    text = readme.read_text()
    start, end = '<!-- RESULTS_START -->', '<!-- RESULTS_END -->'
    compact = table(test, ['system','field_accuracy','numeric_exact_match','missing_field_accuracy','unsupported_field_rate','provenance_support_rate','document_complete_accuracy'])
    result = f'Actual held-out test results: 30 documents, 240 fields per system. Full dataset: {total_missing} null field labels across {missing_docs} documents.\n\n' + compact + f'\n\nAcross the full 60-document run, {len(failures)} SLM documents failed both attempts. Failed fields count as incorrect; see failure-rate columns and the report. Validation improved {len(fixes)} field decisions and worsened {len(rejected_correct)} across development plus test. No result was replaced with a fabricated success.'
    readme.write_text(text.split(start)[0] + start + '\n' + result + '\n' + end + text.split(end)[1])


if __name__ == '__main__':
    write()
