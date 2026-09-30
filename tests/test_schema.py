import pytest
from pydantic import ValidationError
from extraction.schemas import Extraction, empty
from validation.schema_check import check_values
from config import FIELDS


def test_strict_schema():
    raw = empty()
    assert Extraction.model_validate(raw)
    raw['surprise'] = None
    with pytest.raises(ValidationError): Extraction.model_validate(raw)
    del raw['surprise']
    del raw['claim_count']
    with pytest.raises(ValidationError): Extraction.model_validate(raw)


def test_no_boolean_or_fractional_count():
    raw = empty()
    raw['claim_count']['value'] = True
    with pytest.raises(ValidationError): Extraction.model_validate(raw)
    values = dict.fromkeys(FIELDS)
    values['claim_count'] = 1.5
    with pytest.raises(ValidationError): check_values(values)
