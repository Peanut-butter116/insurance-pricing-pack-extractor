from copy import deepcopy
from config import FIELDS
from extraction.schemas import Extraction
from validation.schema_check import normalize, check_values
from validation.provenance import supported, value_supported
from validation.consistency import warnings


def validate(raw, document):
    Extraction.model_validate(raw)
    output, changes = deepcopy(raw), []
    for field in FIELDS:
        evidence = output[field]
        original = evidence['value']
        status = 'missing' if original is None else 'supported'
        try:
            value = normalize(field, original)
            if value is not None and not supported(evidence, document):
                raise ValueError('evidence or location not found')
            if value is not None and not value_supported(field, value, evidence['source_text']):
                raise ValueError('value not present in cited evidence')
            evidence['value'] = value
            if type(value) != type(original) or value != original:
                changes.append({'field': field, 'before': original, 'after': value, 'reason': 'deterministic normalisation'})
        except ValueError as exc:
            evidence['value'], status = None, 'rejected: ' + str(exc)
            changes.append({'field': field, 'before': original, 'after': None, 'reason': str(exc)})
        evidence['validation_status'] = status
        evidence['provenance_supported'] = supported(evidence, document) if original is not None else None
    values = check_values({f: output[f]['value'] for f in FIELDS})
    for field, message in warnings(values).items():
        output[field]['validation_status'] = 'warning: ' + message
        changes.append({'field': field, 'before': values[field], 'after': values[field], 'reason': message})
    return output, changes
