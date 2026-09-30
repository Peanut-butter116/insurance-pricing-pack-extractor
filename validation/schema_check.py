from extraction.schemas import Extraction, Pricing
from validation.dates import date
from validation.numeric import number


def normalize(field, value):
    if value is None:
        return None
    result = date(value) if field.startswith('policy_') else number(value)
    if field == 'claim_count':
        if int(result) != result:
            raise ValueError('claim_count must be an integer')
        result = int(result)
    return result


def check_values(values):
    Pricing.model_validate(values)
    for field, value in values.items():
        if value is not None and field.startswith('policy_') and date(value) != value:
            raise ValueError('dates must use ISO format')
    return values
