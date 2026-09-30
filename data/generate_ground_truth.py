import json
import random
from datetime import date, timedelta
from config import ROOT, SEED, FIELDS


def generate():
    rng = random.Random(SEED)
    records = []
    # Per format: 10 development A-C, 5 seen test A-C, 5 unseen D test.
    for format_, ext in [('pdf', 'pdf'), ('excel', 'xlsx'), ('powerpoint', 'pptx')]:
        for i in range(20):
            layout = 'ABC'[i % 3] if i < 15 else 'D'
            start = date(rng.randint(2023, 2026), rng.randint(1, 12), rng.choice([1, 8, 15]))
            agg = rng.randint(1, 100) * 1000000
            values = dict(zip(FIELDS, [start.isoformat(), (start + timedelta(days=364)).isoformat(),
                rng.randint(10, 1000) * 10000, rng.randint(0, 200), rng.randint(0, 1500) * 10000,
                rng.randint(-40, 80) / 2, agg, rng.randint(1, max(1, agg // 1000000)) * 1000000]))
            if i % 7 == 0:
                values['claim_count'] = 0
                values['incurred_claims_gbp'] = 0
            if i % 9 == 0:
                values['rate_change_pct'] = 7.5
            omissions = rng.sample(list(FIELDS), k=0 if i % 4 == 0 else 1 if i % 4 < 3 else 2)
            for field in omissions:
                values[field] = None
            partial = {}
            if i % 8 == 3 and values['policy_start']:
                partial['policy_start'] = start.strftime('%b %Y')
                values['policy_start'] = None
            doc_id = f'pricing_pack_{len(records) + 1:03d}'
            records.append({'document_id': doc_id, 'format': format_, 'layout': layout,
                            'split': 'development' if i < 10 else 'test', 'variant': i,
                            'path': f'data/documents/{format_}/{doc_id}.{ext}',
                            'values': values, 'partial_dates': partial})
    return records


def ensure():
    path = ROOT / 'data/ground_truth/records.json'
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(generate(), indent=2))
    return json.loads(path.read_text())


if __name__ == '__main__':
    print(f'{len(ensure())} records ready')
