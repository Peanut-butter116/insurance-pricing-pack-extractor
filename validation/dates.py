from datetime import datetime


def date(value):
    if not isinstance(value, str):
        raise ValueError('date must be text')
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d %B %Y', '%d %b %Y'):
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    raise ValueError('full unambiguous UK date required; month/year is insufficient')
