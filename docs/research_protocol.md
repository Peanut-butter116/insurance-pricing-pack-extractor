# Frozen pilot protocol

The protocol, rules and zero-shot prompt were implemented before the full benchmark run. One development PDF (001) was used to check model operation. No test results are used to change the prompt, rules, documents or validator. This is an initial feasibility experiment, not a claim that Layout D was unknown to the engineer who implemented its generator.

## Dataset

Seed 20260930. Sixty independently sampled records, twenty per format. Within each format, records 1–10 are development layouts A–C; 11–15 are seen-layout test; 16–20 are unseen-layout D test. Thus development n=30; test n=30, with 15 seen and 15 unseen. All four layouts exist in every format. There are no duplicate records rendered into multiple formats across splits.

A is a simple label/value table. B is narrative. C distributes information across sections (and Excel sheets). D changes information order, uses value-first PDF rows, reversed Excel columns and PowerPoint callouts. Its terminology uses natural insurance synonyms. D is reserved for test and has no prompt examples. The prompt has no few-shot examples at all.

Each record has eight target fields. Values are generated before rendering. Deliberate omissions are absent from the document. Some policy starts have only month/year evidence, with null exact-date truth. These are counted as missing/insufficient information. Zero claims and zero losses are explicit zeros. Loss amounts and premiums are not inferred from each other.

## Leakage controls

Only format and parsed text segments reach the SLM. No filename, record identifier, layout, split, ground truth, omission list or generator metadata reaches it. Rules and validation receive parsed segments, never labels. Ground truth is loaded by the evaluator solely for scoring. SHA-256 hashes cover every document and the ground-truth file. Any mismatch on subsequent runs aborts. Extractor and evaluator code hashes and the prompt hash are recorded in summary.json.

## Systems

Rules: a fixed keyword/nearby-number/date baseline with ordinary synonyms. It searches labels before values and normalises supported expressions. It does not use a layout label or bespoke D-specific logic.

SLM: Qwen2.5-1.5B-Instruct by default, pinned revision, greedy decoding, no fine-tuning, at most two attempts. A strict outer and evidence schema rejects missing/extra keys, booleans and non-finite numbers. Unit-bearing strings are accepted in the raw schema so deterministic normalisation can be evaluated. Invalid JSON is retried once. Both raw responses and errors are recorded.

SLM + validation: consumes the **identical raw SLM output**, not an independent inference. Normalises units/dates, rejects unsupported quotations/locations or a value absent from its quote, flags inconsistent relationships, and preserves a before/after audit. Rejected values become null. Logical warnings preserve the extracted value for analyst review. No component retrieves ground truth to repair output.

## Scoring

- Field accuracy: correct normalised values across all eight fields, including null truth.
- Numeric exact match: six numeric fields with non-null truth; valid deterministic normalisation is applied to each system equally before scoring.
- Date accuracy: non-null exact dates, with start and end also reported separately.
- Missing-field accuracy: correctly returned null / null-truth fields. Failed extractions do not count as correct nulls.
- Unsupported-field rate: non-null predictions / null-truth fields. This narrow missing-field proxy does **not** measure all possible hallucinations, wrong-field assignments or incorrect numbers when truth is present.
- Provenance support: matching quote at the exact cited parsed location / non-null predictions. Whitespace and case are normalised. This is not semantic entailment.
- Document complete accuracy: all eight fields correct, including nulls. A separate available-fields document metric covers only non-null truth.
- Failures: every field of a failed extraction is incorrect. Null placeholders are retained for accounting and visibly labelled failed. Their unsupported-field rate can be deceptively low; interpret it alongside missing accuracy and failure rate.

Report development and test separately. Headline charts use the test set. Report format and seen/unseen layout subgroups, as well as exact layout family and field tables. Denominator-zero metrics are unavailable, never manufactured zeros.

## Interpretation limits

Only five test documents per format/layout grouping and 15 unseen-layout documents. Fields within documents are correlated, so 240 test decisions are not 240 independent examples. The synthetic generator has limited language variety, no OCR and no noisy broker artefacts. Parser reading order can affect results. Provenance matching verifies text presence, not whether an amount belongs to the requested concept. No production or statistical superiority claim is justified by this pilot alone.
