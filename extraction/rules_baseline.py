"""Fixed keyword baseline, written before holdout generation/evaluation."""
import re
from config import FIELDS
from extraction.schemas import empty
from validation.schema_check import normalize

ALIASES = {
    'policy_start': ['policy start', 'inception', 'cover begins'],
    'policy_end': ['policy end', 'expiry', 'cover ends'],
    'gross_premium_gbp': ['gross written premium', 'gross premium', 'gwp', 'premium'],
    'claim_count': ['claim count', 'reported claims', 'claims count', 'claims'],
    'incurred_claims_gbp': ['total incurred losses', 'incurred claims', 'claims incurred', 'total incurred', 'incurred'],
    'rate_change_pct': ['rate change', 'rate movement', 'renewal increase'],
    'aggregate_limit_gbp': ['aggregate programme limit', 'aggregate limit', 'annual aggregate', 'programme limit'],
    'occurrence_limit_gbp': ['occurrence limit', 'per occurrence', 'per loss limit', 'each and every loss', 'per loss'],
}
VALUE = r'(?:£|GBP\s*)?[+-]?\d[\d,]*(?:\.\d+)?\s*(?:million|thousand|m\b|k\b)?\s*(?:GBP|%|percent|per cent)?|seven and a half percent'
DATE = r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2} [A-Za-z]+ \d{4}'


def extract(document):
    output = empty()
    for field in FIELDS:
        for segment in document['segments']:
            # PDF table labels and values may be on adjacent lines; normalized whitespace preserves order.
            text = ' '.join(segment['text'].split())
            for alias in ALIASES[field]:
                pattern = r'\b' + re.escape(alias) + r'\b\s*(?:[:|]|of|was|is|at)?\s*(' + (DATE if field.startswith('policy_') else VALUE) + ')'
                match = re.search(pattern, text, re.I)
                if match:
                    try:
                        value = normalize(field, match[1].strip())
                        output[field] = {'value': value, 'source_text': match[0], 'source_location': segment['location']}
                        break
                    except ValueError:
                        pass
            if output[field]['value'] is not None:
                break
    return output
