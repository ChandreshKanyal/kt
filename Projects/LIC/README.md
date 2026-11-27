# LIC — Handwritten Proposal Form Data Extraction (RFP response)

> Handover README. Anything marked **Unknown – ask Chandresh** is not stated in the files.

## 1. What this is

Material for responding to **Life Insurance Corporation of India (LIC)**'s RFP:

- **Title:** "AI / ML-Enabled Automation of Customer Onboarding through Handwritten Proposal Data Extraction and Proposal Form Re-Engineering"
- **Ref:** LIC/CO/ITDT/RISE/2526/AI-006/HPDE, issued 29 Jan 2026 by LIC IT/Digital Transformation (IT Research Section), Central Office, Mumbai.
- **Bid portal:** tenderwizard.com/LIC.

**The problem:** LIC agents/branches fill printed proposal forms by hand (e.g. Form 300, "Proposal for insurance on own life",
bilingual Marathi/Hindi/English, ~28 pages). Today staff type them in manually (DEQC = Data Entry & Quality Control). LIC wants
a solution that scans the form on a phone, extracts every handwritten field into JSON with confidence scores, lets a reviewer
correct low-confidence fields, and pushes the result into LIC's systems.

**Status:** this folder has the RFP, the scope, a character dataset, page images and sample forms. **There is no extraction code here.**
Whether the bid was submitted, the Techathon result and the current stage: Unknown – ask Chandresh.

## 2. Key RFP facts

| Item | Detail |
|---|---|
| Timeline (per RFP) | Queries by 08 Feb 2026 · pre-bid meeting 09 Feb 2026 15:00 · bid submission 20 Feb 2026 15:00 · opening 20 Feb 15:15 · demos 23–27 Feb 2026 |
| Evaluation | Stage 1 pre-qualification → Stage 2 technical proposal + live demo / **Techathon** + references → Stage 3 commercial. Award to **L1 (lowest price)** among technically qualified bidders. |
| Pass mark (pass/fail) | **≥95% field-level accuracy** and **≥97% character accuracy**, **≤5% auto-rejected forms**, **≤10% forms needing manual correction**, confidence score on **100%** of fields. One wrong digit in DOB/PAN = whole field wrong. Measured on LIC's samples. |
| Hosting | Bidder-provided, in India, on a **MeitY-empanelled cloud**; no data leaving India; GPU recommended. |
| Must not | Template locking / coordinate-only extraction; "generic OCR without domain fine-tuning is non-compliant". |
| Compliance | IRDAI cyber guidelines, DPDP Act 2023, data localisation; encryption at rest/in transit; PII masking in logs; no retention beyond processing (configurable). |

## 3. Scope of work (summary of `Scope Of Work.docx`)

1. **Form re-engineering:** redesign the form for machine readability (boxed fields, anchors, spacing) without losing regulatory content; print-ready + digital templates.
2. **Mobile + web app / SDK (Android, iOS, web)** to plug into LIC's existing agent app: guided capture (green rectangle, auto-capture, quality check), multi-page scan, crop/deskew/enhance, combined searchable PDF, offline capture with later sync, role-based login, OTP validation.
3. **Image pipeline (mandatory):** deskew/orientation, denoise (median/bilateral), contrast, binarisation, shadow removal, adaptive threshold, stroke enhancement, field cropping, page detection/order, auto-reject (blur, cut fields, exposure, missing page edge).
4. **AI extraction:** Vision-LLM / multimodal models + OCR; field-level JSON with confidence; regional-language support preferred (output in English); photo + signature extraction; annexure processing. Example output: `{"Proposer_Name": {"value": "RAJESH KUMAR", "confidence": 0.96}}`.
5. **Validation rules:** DOB format + age rules, PAN regex + checksum, 10-digit mobile, amount ranges, mandatory fields, cross-field checks (age vs DOB).
6. **Human-in-the-loop UI:** split screen (image left, data right, scroll-linked), bounding-box highlights, editable/non-editable fields by config, confidence flags, supervisor approval, audit trail of edits.
7. **Integration:** multipart upload API (PDF/image + metadata); output JSON via sync REST or callback; original file to object storage.
8. **Deliverables:** re-engineered templates, mobile app (APK/IPA + source), extraction engine with trained models, image pipeline, REST adapters, confidence scoring, accuracy/throughput dashboards, documentation, SOPs, KT.

## 4. Folder contents

| Item | What it is | Notes |
|---|---|---|
| `LIC- RFP.pdf` | The RFP (71 pages) | A duplicate copy was removed during cleanup. |
| `Scope Of Work.docx` | Scope + KPI examples from the RFP | Read this first. |
| `trial.pdf` | 4-page sample of LIC Form 300 (Rev. 2023) | |
| `Character Dataset/character_dataset_2…4/` (+ `.zip` copies) | Handwritten character images, 65 classes: `0–9`, `A–Z`, `A2–Z2` (second variant per letter — meaning not documented), `at`, `comma`, `dot` | Likely for training a character recogniser. How it was made: Unknown – ask Chandresh. `LIC/character_dataset_2.zip` and `Character Dataset/character_dataset_2.zip` are **different** files. |
| `Character Dataset/images/` | 201 page images split from scanned forms ("LIC 1_merged", "LIC Policy_compressed", "Scan 1–6") | Likely the pages of `Projects/Proposal Forms Scan/`. **May contain customer data.** |
| `data-…-batch-0000.zip` | An AI-chat account data export (users.json, conversations.json) | Not opened. Likely personal — confirm and remove. |
| `sslvpn-hcsteam-client-config.ovpn` | OpenVPN client profile ("hcsteam") with embedded certificate and private key; asks for username/password | **Secret.** Do not share; request your own VPN profile. Whether it is for LIC or the internal HCS team network: Unknown – ask Chandresh. |

**Moved out during cleanup (not LIC work):** an auto-glass pricing model (`model*.joblib/.pkl`, `convert_model.py`) →
`Projects/Archive/Unsorted/car-glass-model/`; a UPSRTC pipeline zip (`scrippts.zip`) → `Projects/Archive/UPSRTC/scripts_later_version.zip`;
a duplicate of the Video Analytics `guard_model.pt` was deleted.

## 5. How to "turn it on"

There is nothing to run in this folder: no extraction pipeline, no training scripts for the character dataset, no app code.
If work continues, the RFP implies building:

```
mobile/web capture (SDK) -> image quality gate + pre-processing -> layout / field localisation
  -> Vision-LLM or HTR model per field -> validation rules -> JSON + confidence
  -> HITL review UI -> REST callback + object storage
```

Where any existing extraction code or experiments live: Unknown – ask Chandresh.

## 6. Next steps (if the opportunity is still open)

1. Confirm bid status and whether LIC shared Techathon samples.
2. Build an accuracy harness first: hand-label ~100 forms × 20 fields and compute field accuracy, character accuracy, rejection and manual-correction rates exactly as the RFP defines them (Scope of Work, KPI example).
3. Baseline with a Vision-LLM that can be hosted in India (data cannot leave India), then add field-level validation (PAN checksum, DOB/age).
4. Decide whether the character dataset is still useful (character-level recognisers are unlikely to reach 95% field accuracy alone on cursive handwriting).

## 7. Questions for Chandresh

- Was the bid submitted? Techathon held? Result? Is LIC still active?
- Where is any extraction/training code? What are the `A2–Z2` classes?
- Are the page images and scanned forms real customer data? Can they be shared?
- Who issued the `.ovpn` profile and for which network?
