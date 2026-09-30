"""One command research loop. SLM + validation consumes the identical raw SLM output."""
import argparse
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from config import ROOT, FIELDS
from evaluation.benchmark import frozen, sha
from evaluation.metrics import save
from evaluation.make_plots import make
from extraction.rules_baseline import extract as rules
from extraction.slm_extractor import extract as slm
from extraction.validated_extractor import validate
from extraction.schemas import empty
from extraction.prompts import SYSTEM
from parsers.common import parse
from validation.provenance import supported
from validation.schema_check import normalize


def run(args):
    records, manifest = frozen()
    chosen = [r for r in records if args.split == 'all' or r['split'] == args.split]
    if args.limit:
        chosen = chosen[:args.limit]
    directory = ROOT / args.output
    directory.mkdir(parents=True, exist_ok=True)
    systems = ['rules', 'slm', 'validated'] if args.system == 'all' else [args.system]
    backend, backend_error = None, None
    if any(s != 'rules' for s in systems):
        try:
            from extraction.slm_backend import SLMBackend
            backend = SLMBackend()
        except Exception as exc:
            backend_error = f'{type(exc).__name__}: {exc}'
            print('MODEL LOAD FAILURE:', backend_error, flush=True)
    rows = []
    audit_path = directory / 'audit.jsonl'
    source_hashes = {str(p.relative_to(ROOT)): sha(p) for folder in ['parsers', 'extraction', 'validation', 'evaluation'] for p in (ROOT / folder).glob('*.py')}
    metadata = {'started_utc': datetime.now(timezone.utc).isoformat(), 'platform': platform.platform(),
                'model': backend.metadata if backend else {'error': backend_error, 'not_requested': args.system == 'rules'},
                'benchmark_manifest_sha256': sha(ROOT / 'data/frozen_benchmark/manifest.json'),
                'prompt_sha256': hashlib.sha256(SYSTEM.encode()).hexdigest(), 'source_sha256': source_hashes,
                'split': args.split, 'systems': systems, 'documents': len(chosen), 'benchmark_documents': len(records),
                'field_decisions_per_system': len(chosen) * 8, 'missing_fields': sum(v is None for r in chosen for v in r['values'].values()),
                'metric_policy': 'Failed extractions score every field incorrect, including null truth. Numeric/date metrics exclude null truth. Unsupported rate is non-null over null-truth fields. Provenance is quote+location matching, not semantic proof.'}
    with audit_path.open('w') as audit:
        for n, record in enumerate(chosen, 1):
            print(f'[{n}/{len(chosen)}] {record["document_id"]} {record["format"]}', flush=True)
            start = time.perf_counter()
            parse_error = None
            try:
                document = parse(ROOT / record['path'])
            except Exception as exc:
                parse_error = f'{type(exc).__name__}: {exc}'
                document = {'format': record['format'], 'segments': []}
            raw, attempts, slm_error = empty(), [], backend_error or parse_error
            if backend and not parse_error:
                raw, attempts, slm_error = slm(document, backend)
            log = {'document_id': record['document_id'], 'parse_error': parse_error, 'slm_error': slm_error,
                   'attempts': attempts, 'raw_extraction': raw, 'validation_changes': []}
            for system in systems:
                failed = parse_error if system == 'rules' else slm_error
                output = empty()
                if not failed:
                    try:
                        if system == 'rules':
                            output = rules(document)
                        elif system == 'slm':
                            output = raw
                        else:
                            output, log['validation_changes'] = validate(raw, document)
                    except Exception as exc:
                        failed = f'{type(exc).__name__}: {exc}'
                        log[system + '_error'] = failed
                for field in FIELDS:
                    evidence = output[field]
                    prediction, truth = evidence['value'], record['values'][field]
                    try:
                        canonical = normalize(field, prediction)
                        correct = canonical == truth and not failed
                    except (ValueError, TypeError):
                        canonical, correct = prediction, False
                    rows.append({'document_id': record['document_id'], 'format': record['format'], 'layout': record['layout'],
                        'layout_group': 'unseen D' if record['layout'] == 'D' else 'seen A-C', 'split': record['split'],
                        'system': system, 'field': field, 'ground_truth': json.dumps(truth), 'predicted_value': json.dumps(prediction),
                        'normalised_prediction': json.dumps(canonical), 'correct': bool(correct), 'truth_missing': truth is None,
                        'prediction_missing': prediction is None, 'source_text': evidence.get('source_text'),
                        'source_location': evidence.get('source_location'), 'provenance_supported': bool(prediction is not None and supported(evidence, document)),
                        'validation_status': ('failed: ' + str(failed)) if failed else evidence.get('validation_status', 'not validated'), 'failed': bool(failed)})
            log['seconds'] = time.perf_counter() - start
            audit.write(json.dumps(log, ensure_ascii=False) + '\n')
            audit.flush()
            # Checkpoints preserve progress and make partial runs explicitly identifiable.
            save(rows, directory, metadata | {'processed_documents': n, 'run_finished': False})
    summary = save(rows, directory, metadata | {'processed_documents': len(chosen), 'run_finished': True})
    make(directory)
    from template.populate_template import create_template
    create_template()
    print(json.dumps(summary['metrics'], indent=2), flush=True)
    if not summary['complete']:
        raise SystemExit('Pilot contains recorded failures. See audit.jsonl; no success was fabricated.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--system', choices=['all', 'rules', 'slm', 'validated'], default='all')
    parser.add_argument('--split', choices=['all', 'development', 'test'], default='all')
    parser.add_argument('--limit', type=int)
    parser.add_argument('--output', default='results')
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error('--limit must be positive')
    run(args)
