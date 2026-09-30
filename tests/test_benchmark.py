from data.generate_ground_truth import generate


def test_fixed_split_and_no_cross_format_copies():
    records = generate()
    assert records == generate()
    assert len(records) == 60
    assert sum(r['split'] == 'test' for r in records) == 30
    assert sum(r['layout'] == 'D' for r in records) == 15
    assert all(r['split'] == 'test' for r in records if r['layout'] == 'D')
    assert len({tuple(r['values'].values()) for r in records}) == 60


def test_frozen_data_tampering_aborts(tmp_path, monkeypatch):
    import json
    import pytest
    import evaluation.benchmark as benchmark
    truth = tmp_path / 'data/ground_truth/records.json'
    truth.parent.mkdir(parents=True)
    records = [{'document_id': 'one', 'split': 'test', 'path': 'one.pdf'}]
    truth.write_text(json.dumps(records))
    document = tmp_path / 'one.pdf'
    document.write_bytes(b'original bytes')
    monkeypatch.setattr(benchmark, 'ROOT', tmp_path)
    monkeypatch.setattr(benchmark, 'generate', lambda: records)
    benchmark.frozen()
    assert benchmark.frozen()[0] == records
    document.write_bytes(b'changed bytes')
    with pytest.raises(RuntimeError, match='hash mismatch'):
        benchmark.frozen()
