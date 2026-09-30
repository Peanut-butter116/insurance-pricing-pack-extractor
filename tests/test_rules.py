from extraction.rules_baseline import extract


def test_zero_missing_and_synonyms():
    doc = {'segments': [{'location': 'page 1', 'text': 'GWP: £2.45m\nReported claims: 0\nInception: 01/02/2025'}]}
    result = extract(doc)
    assert result['gross_premium_gbp']['value'] == 2450000
    assert result['claim_count']['value'] == 0
    assert result['policy_start']['value'] == '2025-02-01'
    assert result['rate_change_pct']['value'] is None
