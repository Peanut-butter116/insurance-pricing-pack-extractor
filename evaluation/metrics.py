import json
import pandas as pd


def ratio(n, d):
    return float(n / d) if d else None


def score(rows):
    total = len(rows)
    present = rows[~rows.truth_missing]
    numeric = present[~present.field.str.startswith('policy_')]
    dates = present[present.field.str.startswith('policy_')]
    missing = rows[rows.truth_missing]
    extracted = rows[~rows.prediction_missing]
    docs = rows.groupby('document_id').correct.all()
    available_docs = present.groupby('document_id').correct.all()
    return {'documents': len(docs), 'evaluated_fields': total,
        'field_accuracy': ratio(rows.correct.sum(), total),
        'present_field_accuracy': ratio(present.correct.sum(), len(present)),
        'numeric_exact_match': ratio(numeric.correct.sum(), len(numeric)),
        'date_accuracy': ratio(dates.correct.sum(), len(dates)),
        'policy_start_accuracy': ratio(present[present.field == 'policy_start'].correct.sum(), len(present[present.field == 'policy_start'])),
        'policy_end_accuracy': ratio(present[present.field == 'policy_end'].correct.sum(), len(present[present.field == 'policy_end'])),
        'missing_fields': len(missing), 'missing_field_accuracy': ratio(missing.correct.sum(), len(missing)),
        'unsupported_field_rate': ratio((~missing.prediction_missing).sum(), len(missing)),
        'provenance_support_rate': ratio(extracted.provenance_supported.sum(), len(extracted)),
        'document_complete_accuracy': float(docs.mean()),
        'available_fields_document_accuracy': float(available_docs.mean()),
        'failure_rate': float(rows.groupby('document_id').failed.any().mean()),
        'non_null_predictions': len(extracted), 'numeric_fields': len(numeric), 'date_fields': len(dates),
        'validation_warnings': int(rows.validation_status.str.startswith(('warning', 'rejected')).sum())}


def aggregate(frame, groups):
    output = []
    for key, rows in frame.groupby(groups, sort=False):
        if not isinstance(key, tuple):
            key = (key,)
        output.append(dict(zip(groups, key)) | score(rows))
    return pd.DataFrame(output)


def save(rows, directory, metadata):
    frame = pd.DataFrame(rows)
    frame.to_csv(directory / 'predictions.csv', index=False)
    overall = aggregate(frame, ['split', 'system'])
    overall.to_csv(directory / 'metrics.csv', index=False)
    aggregate(frame, ['split', 'system', 'format']).to_csv(directory / 'metrics_by_format.csv', index=False)
    aggregate(frame, ['split', 'system', 'layout_group']).to_csv(directory / 'metrics_by_layout.csv', index=False)
    aggregate(frame, ['split', 'system', 'layout']).to_csv(directory / 'metrics_by_layout_family.csv', index=False)
    aggregate(frame, ['split', 'system', 'field']).to_csv(directory / 'metrics_by_field.csv', index=False)
    summary = metadata | {'metrics': json.loads(overall.to_json(orient='records')), 'complete': not bool(frame.failed.any())}
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False))
    return summary
