import re
from validation.schema_check import normalize


def compact(text):
    return ' '.join((text or '').split()).casefold()


def supported(evidence, document):
    quote, location = evidence.get('source_text'), evidence.get('source_location')
    if not quote or not location:
        return False
    return any(location == s['location'] and compact(quote) in compact(s['text'])
               for s in document['segments'])


def value_supported(field, value, quote):
    """Value presence, not semantic entailment. Date precision is never inferred."""
    if value is None:
        return True
    if field.startswith('policy_'):
        candidates = re.findall(r'\b(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2} [A-Za-z]+ \d{4})\b', quote or '')
    else:
        candidates = re.findall(r'(?:£|GBP\s*)?[+-]?\d[\d,]*(?:\.\d+)?\s*(?:million|thousand|m\b|k\b)?\s*(?:GBP|%|percent|per cent)?|seven and a half percent', quote or '', flags=re.I)
    for candidate in candidates:
        try:
            if normalize(field, candidate.strip()) == value:
                return True
        except ValueError:
            pass
    return False
