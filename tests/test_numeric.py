import pytest
from validation.numeric import number
from validation.dates import date


@pytest.mark.parametrize('text,expected', [('£2.45m',2450000), ('£750k',750000), ('GBP 10 million',10000000),
    ('2.45 million GBP',2450000), ('7.5%',7.5), ('+7.5 per cent',7.5), ('seven and a half percent',7.5), ('0',0), ('-20%',-20)])
def test_numbers(text, expected):
    assert number(text) == expected


@pytest.mark.parametrize('text', [True, 'NaN', float('inf'), '£2.4usd', '12,34', '2 to 4', 'about 2m'])
def test_reject_numbers(text):
    with pytest.raises(ValueError): number(text)


@pytest.mark.parametrize('text', ['01/02/2025', '1 February 2025', '2025-02-01'])
def test_dates(text):
    assert date(text) == '2025-02-01'


@pytest.mark.parametrize('text', ['Jan 2025', '2025', '31/02/2025', '02/13/2025'])
def test_ambiguous_dates(text):
    with pytest.raises(ValueError): date(text)
