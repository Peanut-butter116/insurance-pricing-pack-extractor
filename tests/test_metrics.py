import pandas as pd
from evaluation.metrics import score


def test_failed_nulls_do_not_earn_missing_accuracy():
    rows = pd.DataFrame([dict(document_id='bad', field='rate_change_pct', truth_missing=True,
        prediction_missing=True, correct=False, provenance_supported=False, validation_status='failed', failed=True)])
    result = score(rows)
    assert result['missing_field_accuracy'] == 0
    assert result['unsupported_field_rate'] == 0
    assert result['failure_rate'] == 1
    assert result['numeric_exact_match'] is None


def test_numeric_excludes_missing_and_document_requires_all():
    rows = pd.DataFrame([
        dict(document_id='one', field='gross_premium_gbp', truth_missing=False, prediction_missing=False,
             correct=True, provenance_supported=True, validation_status='supported', failed=False),
        dict(document_id='one', field='rate_change_pct', truth_missing=True, prediction_missing=False,
             correct=False, provenance_supported=False, validation_status='not validated', failed=False)])
    result = score(rows)
    assert result['field_accuracy'] == .5
    assert result['numeric_exact_match'] == 1
    assert result['unsupported_field_rate'] == 1
    assert result['document_complete_accuracy'] == 0
