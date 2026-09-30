import json
from extraction.schemas import empty
from extraction.slm_extractor import extract


class Fake:
    def __init__(self, responses):
        self.responses, self.payloads = iter(responses), []
    def generate(self, system, payload):
        self.payloads.append(payload)
        return next(self.responses), {}


def test_retry_and_no_truth_leak():
    backend = Fake(['bad JSON', json.dumps(empty())])
    result, attempts, error = extract({'format': 'pdf', 'segments': [], 'layout': 'D', 'values': {'secret': 123}}, backend)
    assert error is None and len(attempts) == 2
    assert not attempts[0]['success']
    assert 'secret' not in backend.payloads[0] and 'layout' not in backend.payloads[0]


def test_failure_never_success():
    result, attempts, error = extract({'format': 'pdf', 'segments': []}, Fake(['bad', '{}']))
    assert error and len(attempts) == 2
