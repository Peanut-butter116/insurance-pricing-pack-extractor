# Pilot report: SLM Pricing Pack Extraction Assistant

## Scope and status

This is an executed synthetic feasibility study, not a simulated result. The run processed 60 documents. 9 SLM document(s) failed both permitted attempts. Those failures remain in the results and count as incorrect. No production performance or superiority claim follows from this pilot.

## Model and hardware

- Model: `Qwen/Qwen2.5-1.5B-Instruct`; revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`.
- Parameters: 1,543,714,304; dtype `torch.float16`; device `mps`.
- Hardware: Apple M1 Pro, memory 16 GB; `macOS-26.6.2-arm64-arm-64bit-Mach-O`.
- Python 3.14.2; PyTorch `2.14.0`. Exact installed versions are in `requirements-lock.txt`.
- Greedy decoding, seed 20260930, maximum 1,200 generated tokens, two attempts maximum, no fine-tuning.
- Run began: 2026-09-30T14:14:34.594801+00:00. Benchmark SHA-256: `c85c3383dbac251390e6ce0c2cfe0a170cd7f4a9f74df1aa0c8bcc8584fe80d1`.
- Total attempts: 99; schema-valid attempts: 51.
- Mean model generation time per document, including retries and excluding initial model load: 20.64 seconds. Total generation: 20.6 minutes. Token counts and per-attempt latency are in the audit.

## Dataset

60 unique records and 60 documents: 20 PDF, 20 Excel, 20 PowerPoint; four layout families. Eight fields give 480 decisions per system, 1,440 across the three systems. 66 null field labels across 45 documents include 6 month/year-only policy starts. 30 development and 30 test documents; test has 15 seen A–C and 15 unseen D. Each format has ten test documents. Labels are known by construction, and hidden from every extraction system.

## Headline test results

| system | documents | evaluated_fields | field_accuracy | numeric_exact_match | date_accuracy | missing_field_accuracy | unsupported_field_rate | provenance_support_rate | document_complete_accuracy | failure_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rules | 30 | 240 | 58.3% | 52.6% | 44.7% | 100.0% | 0.0% | 100.0% | 30.0% | 0.0% |
| slm | 30 | 240 | 51.2% | 47.4% | 63.8% | 51.4% | 35.1% | 38.1% | 10.0% | 16.7% |
| validated | 30 | 240 | 30.4% | 19.2% | 25.5% | 83.8% | 2.7% | 100.0% | 3.3% | 16.7% |

Accuracy denominators: all 240 test fields for field accuracy; only non-null numeric/date truth for their exact-match metrics. Missing accuracy and unsupported rate use null-truth fields. Failed null placeholders earn no accuracy credit. Provenance rate is conditional on non-null predictions, so a stricter validator can increase it by rejecting correct values. See the CSV denominator columns before comparing rates.

## Results by format (test)

| system | format | documents | field_accuracy | numeric_exact_match | missing_field_accuracy | unsupported_field_rate | failure_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rules | pdf | 10 | 68.8% | 57.7% | 100.0% | 0.0% | 0.0% |
| slm | pdf | 10 | 51.2% | 48.1% | 41.7% | 50.0% | 10.0% |
| validated | pdf | 10 | 27.5% | 19.2% | 83.3% | 8.3% | 10.0% |
| rules | excel | 10 | 53.8% | 50.9% | 100.0% | 0.0% | 0.0% |
| slm | excel | 10 | 47.5% | 47.2% | 41.7% | 33.3% | 30.0% |
| validated | excel | 10 | 22.5% | 15.1% | 75.0% | 0.0% | 30.0% |
| rules | powerpoint | 10 | 52.5% | 49.0% | 100.0% | 0.0% | 0.0% |
| slm | powerpoint | 10 | 55.0% | 47.1% | 69.2% | 23.1% | 10.0% |
| validated | powerpoint | 10 | 41.2% | 23.5% | 92.3% | 0.0% | 10.0% |

## Seen versus unseen layouts (test)

| system | layout_group | documents | field_accuracy | missing_field_accuracy | provenance_support_rate |
| --- | --- | --- | --- | --- | --- |
| rules | seen A-C | 15 | 88.3% | 100.0% | 100.0% |
| slm | seen A-C | 15 | 65.0% | 70.6% | 53.3% |
| validated | seen A-C | 15 | 37.5% | 82.4% | 100.0% |
| rules | unseen D | 15 | 28.3% | 100.0% | 100.0% |
| slm | unseen D | 15 | 37.5% | 35.0% | 22.2% |
| validated | unseen D | 15 | 23.3% | 85.0% | 100.0% |

Layout D was excluded from development and examples. It changes both information order and presentation. Its generator was necessarily known to the engineer; it is not a blind external insurer test. No prompts, extraction rules or validation rules were tuned after inspecting holdout results.

## Development results (not headline test performance)

| system | field_accuracy | numeric_exact_match | missing_field_accuracy | unsupported_field_rate | failure_rate |
| --- | --- | --- | --- | --- | --- |
| rules | 90.0% | 95.7% | 96.6% | 3.4% | 0.0% |
| slm | 71.7% | 68.3% | 69.0% | 6.9% | 13.3% |
| validated | 30.8% | 26.7% | 72.4% | 3.4% | 13.3% |

## Concrete extraction examples

Successful SLM field examples:

| document_id | field | ground_truth | predicted_value | source_text | source_location |
| --- | --- | --- | --- | --- | --- |
| pricing_pack_011 | incurred_claims_gbp | 910000 | "910000" | Total incurred losses were £910k. | page 1 |
| pricing_pack_011 | rate_change_pct | 27.5 | "27.5" | Rate change: 27.5 per cent. | page 1 |
| pricing_pack_011 | aggregate_limit_gbp | 43000000 | "43000000" | The aggregate programme limit is £43m. | page 1 |
| pricing_pack_011 | occurrence_limit_gbp | 14000000 | "14000000" | The per occurrence limit is GBP 14 million. | page 1 |

Incorrect SLM field examples (including unsupported values where present):

| document_id | field | ground_truth | predicted_value | source_text | source_location |
| --- | --- | --- | --- | --- | --- |
| pricing_pack_011 | policy_start | null | "2026-02-14" | Cover ends on 14 February 2026. | page 1 |
| pricing_pack_011 | policy_end | "2026-02-14" | null |  |  |
| pricing_pack_011 | gross_premium_gbp | 3820000 | "3.82" | The gross written premium was GBP 3.82 million. | page 1 |
| pricing_pack_011 | claim_count | 3 | null |  |  |
| pricing_pack_012 | policy_start | null | "Jul 2023" | Inception | page 1 |
| pricing_pack_012 | policy_end | "2024-07-06" | null |  |  |

## Validation tradeoff and unsupported extraction

Across development plus test, validation converted **13 incorrect decisions to correct decisions**, and converted **161 correct decisions to incorrect decisions**. These counts include null decisions and describe the observed validator, not an assumed benefit.

Examples where validation rejected a correct raw value:

| document_id | field | predicted_value_raw | source_text_raw | source_location_raw | validation_status_validated |
| --- | --- | --- | --- | --- | --- |
| pricing_pack_003 | policy_start | "2023-08-01" | Inception                                    2023-08-01 | page 1, line 1 | rejected: evidence or location not found |
| pricing_pack_003 | policy_end | "30/07/2024" | Expiry                                       30/07/2024 | page 1, line 2 | rejected: evidence or location not found |
| pricing_pack_003 | gross_premium_gbp | "\u00a36380k" | Premium and movement  GWP                                     £6380k | page 1, line 3 | rejected: evidence or location not found |
| pricing_pack_003 | claim_count | 136 | Claims experience  Reported claims                           136 | page 1, line 4 | rejected: evidence or location not found |

Examples where validation improved correctness:

| document_id | field | predicted_value_raw | predicted_value_validated | validation_status_validated |
| --- | --- | --- | --- | --- |
| pricing_pack_012 | policy_start | "Jul 2023" | null | rejected: full unambiguous UK date required; month/year is insufficient |
| pricing_pack_015 | aggregate_limit_gbp | "4m" | null | rejected: evidence or location not found |
| pricing_pack_016 | claim_count | "32.5%" | null | rejected: claim_count must be an integer |
| pricing_pack_020 | policy_start | "06/02/2025" | null | rejected: evidence or location not found |

A non-null prediction on null truth is the specified unsupported-field proxy. Wrong numbers on present fields and wrong concept assignments are separate errors; this proxy does not capture them. Quote matching is only a first check. It cannot certify the semantic relationship between a quote and the requested field. Rejecting paraphrases and imprecise locations can remove correct values, while a copied real value for the wrong concept can pass.

## Explicit failures

- `pricing_pack_004`: SLM failed both attempts; nulls are failure placeholders. Last attempt: ValidationError: 2 validation errors for Extraction
- `pricing_pack_018`: SLM failed both attempts; nulls are failure placeholders. Last attempt: ValidationError: 2 validation errors for Extraction
- `pricing_pack_024`: SLM failed both attempts; nulls are failure placeholders. Last attempt: ValidationError: 3 validation errors for Extraction
- `pricing_pack_034`: SLM failed both attempts; nulls are failure placeholders. Last attempt: ValidationError: 1 validation error for Extraction
- `pricing_pack_038`: SLM failed both attempts; nulls are failure placeholders. Last attempt: ValidationError: 3 validation errors for Extraction
- `pricing_pack_039`: SLM failed both attempts; nulls are failure placeholders. Last attempt: ValidationError: 3 validation errors for Extraction
- `pricing_pack_042`: SLM failed both attempts; nulls are failure placeholders. Last attempt: ValidationError: 1 validation error for Extraction
- `pricing_pack_047`: SLM failed both attempts; nulls are failure placeholders. Last attempt: ValidationError: 1 validation error for Extraction
- `pricing_pack_054`: SLM failed both attempts; nulls are failure placeholders. Last attempt: ValidationError: 1 validation error for Extraction

Invalid first attempts and successful retries are also retained in the audit. The evaluator finishes all documents before returning a non-zero exit status if failures occurred.

## Research interpretation

On the held-out test set, rules achieved 58.3% field accuracy against 51.2% for the SLM. Date accuracy was 63.8% for the SLM and 44.7% for rules. Validation changed unsupported predictions on missing fields from 35.1% to 2.7%, while changing retained non-null values from 147 to 45 and overall accuracy to 30.4%. The SLM document failure rate was 16.7%. On unseen D, the SLM achieved 37.5% against 28.3% for rules. Consider both this relative comparison and the absolute accuracy before drawing a generalisation claim.

The appropriate conclusion is the measured balance between extraction accuracy, source support and analyst review effort. Simple label/value extraction remains a useful baseline. A small model can interpret narrative and reordered content, but its actual reliability must include JSON failures and unsupported or imprecise evidence. The validator demonstrates traceable abstention, not a guarantee of improved overall accuracy. Its support rate is conditioned on values it retained. Compare the seen/unseen table directly; a model that still performs poorly on both is not evidence of successful generalisation. This small, correlated benchmark does not support claims of statistical significance or production readiness.

## What worked

The complete document-to-template workflow runs locally, preserves missing values and real zeros, expands supported units, retains source locations, produces real paired model/validator results, and exposes failures. The Streamlit interface can replay saved real outputs for a fast mentor demonstration, or run live inference. The template export preserves typed dates, percentages and amounts with source and validation columns.

## Limitations

- Synthetic wording, repeated sentence structures and simple tables underrepresent real broker packs.
- Sixty documents, only thirty held out and fifteen unseen-layout examples; field decisions within a document are correlated.
- Eight fields, one 1.5B model, one hardware configuration and no fine-tuning comparison.
- No real pricing analyst evaluation, OCR, complex spreadsheet formulas, image-text slides or authorised insurer data.
- Reading order, text segmentation and number-format reconstruction can affect extraction.
- Provenance matching is lexical, not semantic; conservative checks can reduce coverage.
- The rules baseline uses label-before-value patterns and has limited narrative grammar. A stronger rules baseline is an important next comparison.
- Greedy decoding and pinned weights improve reproducibility but device/library differences can still change output.
- Render checks covered representative files for every format/layout; this does not prove compatibility with all Office versions.

## Suggested 12-week research plan

1. Weeks 1–2: analyst workflow interviews, authorised data access, schema and review criteria.
2. Weeks 3–4: larger realistic benchmark with insurer/template-separated splits; freeze an external test set.
3. Weeks 5–6: stronger rules, constrained output and 1.5B/3B/7B model comparison.
4. Weeks 7–8: evidence grounding, OCR/multimodal parsing if failures justify it; QLoRA only for a demonstrated persistent gap.
5. Weeks 9–10: blinded analyst review study, review-time savings, error severity and latency/cost measurement.
6. Weeks 11–12: final frozen evaluation, uncertainty analysis and operational recommendations.

## Reproduction and key files

`python -m evaluation.run_pilot` executes the experiment; `python -m evaluation.write_report` refreshes this report from finished saved results. `streamlit run app/streamlit_app.py` starts the demo. See README for installation and alternate models.

- `results/predictions.csv`: every field decision, truth, output, evidence and failure status.
- `results/metrics.csv`, `metrics_by_format.csv`, `metrics_by_layout.csv`: split-specific measured metrics.
- `results/metrics_by_field.csv`, `metrics_by_layout_family.csv`: additional diagnostic breakdowns.
- `results/comparison.png`, `layout_comparison.png`: test results charts.
- `results/audit.jsonl`: raw model outputs, retries, errors and validator changes.
- `results/summary.json`: model, hashes, environment and run status.
- `template/pricing_template.xlsx`: blank analyst review workbook.
- `results/example_pricing_review.xlsx`: populated example from a saved actual model response.
- `docs/research_protocol.md`: design and metric definitions.
