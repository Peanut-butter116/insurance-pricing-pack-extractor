from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = 20260930
FIELDS = ('policy_start', 'policy_end', 'gross_premium_gbp', 'claim_count',
          'incurred_claims_gbp', 'rate_change_pct', 'aggregate_limit_gbp', 'occurrence_limit_gbp')
LABELS = ('Policy Start', 'Policy End', 'Gross Premium', 'Claim Count',
          'Incurred Claims', 'Rate Change', 'Aggregate Limit', 'Occurrence Limit')
