import hashlib
import json
from config import ROOT, SEED
from data.generate_documents import generate


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen():
    manifest_path = ROOT / 'data/frozen_benchmark/manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        for relative, digest in manifest['sha256'].items():
            if not (ROOT / relative).exists() or sha(ROOT / relative) != digest:
                raise RuntimeError(f'Frozen benchmark hash mismatch: {relative}. Restore original; do not silently regenerate.')
        return json.loads((ROOT / 'data/ground_truth/records.json').read_text()), manifest
    records = generate()
    files = ['data/ground_truth/records.json'] + [r['path'] for r in records]
    manifest = {'seed': SEED, 'development': [r['document_id'] for r in records if r['split'] == 'development'],
                'test': [r['document_id'] for r in records if r['split'] == 'test'],
                'holdout_layout': 'D', 'sha256': {p: sha(ROOT / p) for p in files}}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    return records, manifest
