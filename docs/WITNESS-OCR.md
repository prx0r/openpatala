# WITNESS-OCR — manuscript pages to openpatala spans (autonomous-agent pipeline)

*2026-11-06. For free-tier agents (beam/CF) + one assessor. The witness
column is empty everywhere; this is the machine that fills it without
fabricating it. Nothing here marks anything canonical — OCR output is a
candidate until reviewed, and WITNESS stays UNKNOWN until manuscript
attestation exists. Companion: box trika-x `WITNESS-PIPELINE` notes.*

## 0. Cast

- **Drafters (beam-free/CF free-tier, $0).** Run OCR, tile spans, assemble
  receipts. Stateless per page, no judgment, no canon.
- **Assessor (smart agent).** Owns source selection, review order, span
  approval, record promotion. Reviews high-risk pages first + random audit
  of high-confidence pages (false-negative watch).
- **Scholar channel (human).** NGMPP/microfilm access, attestation, rights
  confirmation. No agent substitutes.

## 1. Source (rights first, pixels second)

- eGangotri pages are CC-0 (public domain declared). NGMPP microfilms need
  the scholar channel. Record per-page: archive, shelfmark, license, page
  sha256 BEFORE any OCR. No sha, no pipeline.
- One test page first, always. Scale only measured paths.

## 2. OCR (calibrated engines, free tier)

- **Manuscripts:** MIDF pipeline (`tadad/midf-sanskrit-ocr`: Kraken BLLA
  segmenter + PP-OCRv6 recognizer, CPU-runnable, ~3.5% CER on tested panel
  with review-risk triage scores). Run per page; keep JSON (boundaries,
  confidences, risk scores, reasons).
- **Print editions:** Xiaomi-OCR-0 trial (SOTA docs, unproven on
  manuscripts — benchmark both on one page before trusting either).
- Review order: risk_score DESC for humans; random high-confidence sample
  for false negatives. Preserve component signals for recalibration.

## 3. Transcription candidates (never canonical)

- OCR text + per-line confidence + risk = candidate, stored beside the
  page (never over source bytes). Scholarly transcriptions, where they
  exist (e.g. eGangotri print editions), are the calibration gold:
  measure CER before scaling to unattested pages.
- Failure rules: null/empty output = ERROR rerun (never silent); CER
  unmeasured = unscaled; single-manuscript tuning never claimed as
  general (MIDF's own limit, keep it).

## 4. Span mapping (bytes to verses)

- Align candidate text to edition verse markers → byte spans per verse
  (passage_id convention of the target work) → volume manifest via the
  translation-work `record_volume` mechanics (byte-equality enforced,
  gaps/overlaps explicit).
- Gaps are data (damage, margins, illumination), never smoothed.
- Manifests are machine-proposed until assessor-approved.

## 5. Records + ingest (identity spine)

- `build_source_records.py` picks up manifests → record flips
  NO-SOURCE-RECORD to RECORDED (bytes pinned, edition candidate).
- `openpatala_ingest.py` (Mode B for new sources) loads works/editions/
  etexts/passages into the box DB; R2 mirror + migrations stay the
  restore path.
- WITNESS column: rows appear only with manuscript attestation
  (shelfmark + holding + folio). OCR never creates witnesses.

## 6. Calibration (prove it before scaling it)

1. One page with a scholarly transcription → CER + line-count accuracy.
2. Record verdict (engine, weights rev, pipeline.json pin, CER, panel).
3. Scale only CER-measured paths; re-measure per new hand/script.
4. Learnings compound here (dated addenda, never edits).

## Free-tier law

CPU-only engines; no paid APIs in the loop (paid OCR is an assessor tool
for spot checks, never the pipeline); neurons logged; disk-checked
(weights + pages measured before download — box is small).
