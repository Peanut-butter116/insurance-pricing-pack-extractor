from extraction.schemas import empty
from extraction.validated_extractor import validate
from validation.provenance import supported
from validation.consistency import warnings
from config import FIELDS


def test_fabricated_quote_and_wrong_value():
    doc = {'segments': [{'location': 'page 1', 'text': 'Gross premium: £2.5m'}]}
    raw = empty()
    raw['gross_premium_gbp'] = {'value': 9000000, 'source_text': 'Gross premium: £2.5m', 'source_location': 'page 1'}
    assert supported(raw['gross_premium_gbp'], doc)
    output, changes = validate(raw, doc)
    assert output['gross_premium_gbp']['value'] is None
    assert changes[0]['before'] == 9000000
    raw['gross_premium_gbp']['value'] = '£2.5m'
    assert validate(raw, doc)[0]['gross_premium_gbp']['value'] == 2500000
    raw['gross_premium_gbp']['source_location'] = 'page 2'
    assert validate(raw, doc)[0]['gross_premium_gbp']['value'] is None


def test_month_year_does_not_justify_exact_day():
    raw = empty()
    raw['policy_start'] = {'value': '2025-01-01', 'source_text': 'Inception: Jan 2025', 'source_location': 'page 1'}
    doc = {'segments': [{'location': 'page 1', 'text': 'Inception: Jan 2025'}]}
    assert validate(raw, doc)[0]['policy_start']['value'] is None


def test_relationships_flagged_not_corrected():
    values = dict.fromkeys(FIELDS)
    values.update(policy_start='2025-02-01', policy_end='2025-01-01', aggregate_limit_gbp=100, occurrence_limit_gbp=200, claim_count=-1)
    assert set(warnings(values)) == {'policy_end', 'occurrence_limit_gbp', 'claim_count'}


def test_missing_is_not_zero():
    output, changes = validate(empty(), {'segments': []})
    assert all(x['value'] is None for x in output.values())
    assert not changes


def test_validation_does_not_mutate_comparison_output():
    from copy import deepcopy
    raw = empty()
    raw['gross_premium_gbp'] = {'value': '£2m', 'source_text': 'missing quote', 'source_location': 'page 1'}
    original = deepcopy(raw)
    validate(raw, {'segments': []})
    assert raw == original
