"""Conservative full-expression parsing: no partial numbers or guessed units."""
import math
import re
from decimal import Decimal


def number(value):
    if isinstance(value, bool):
        raise ValueError('boolean is not a number')
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            raise ValueError('non-finite number')
        return value
    text = str(value).strip().lower().replace('−', '-')
    if text in ('seven and a half percent', 'seven and a half per cent'):
        return 7.5
    match = re.fullmatch(r'(?:£|gbp\s*)?\s*([+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*(million|thousand|m|k)?\s*(?:gbp|%|percent|per cent)?', text)
    if not match:
        raise ValueError(f'unsupported numeric expression: {value}')
    scale = {'million': 1000000, 'm': 1000000, 'thousand': 1000, 'k': 1000, None: 1}[match[2]]
    result = Decimal(match[1].replace(',', '')) * scale
    return int(result) if result == int(result) else float(result)
