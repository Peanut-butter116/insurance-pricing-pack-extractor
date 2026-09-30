"""Raw schema permits unit-bearing text; final schema enforces canonical types."""
from pydantic import BaseModel, ConfigDict, StrictInt, StrictFloat, StrictStr, create_model, field_validator
from config import FIELDS


class Evidence(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)
    value: StrictInt | StrictFloat | StrictStr | None
    source_text: StrictStr | None
    source_location: StrictStr | None


class StrictBase(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


Extraction = create_model('Extraction', __base__=StrictBase, **{f: (Evidence, ...) for f in FIELDS})
Pricing = create_model('Pricing', __base__=StrictBase, **{
    f: ((StrictStr | None) if f.startswith('policy_') else
        (StrictInt | None) if f == 'claim_count' else (StrictInt | StrictFloat | None), ...)
    for f in FIELDS})


def empty():
    return {f: {'value': None, 'source_text': None, 'source_location': None} for f in FIELDS}
