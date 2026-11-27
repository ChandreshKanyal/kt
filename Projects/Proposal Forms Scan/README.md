# Proposal Forms Scan

> Handover README. Anything marked **Unknown – ask Chandresh** is not stated in the files.

**What it is:** scanned LIC insurance proposal forms, the input/test data for the LIC handwritten-extraction work
(see `Projects/LIC/README.md`). There is no code here.

**Format:** every file is an image-only PDF (no text layer), so text cannot be copied out; it must go through OCR / a vision model.

| File | Pages | Notes |
|---|---|---|
| `1.pdf` – `11.pdf` | 27–28 each | Scanned proposal forms. |
| `Empty Form.pdf` | 28 | Blank form — use as the layout template. |
| `Sample 3.pdf` | 26 | Sample form. |
| `Real Doc.pdf` | 28 | The name suggests a real customer's filled form. |
| `Need Fix.pdf` | 55 | Known problem file (about twice the normal page count). What needs fixing: Unknown – ask Chandresh. |

Related: `Projects/LIC/Character Dataset/images/` holds 201 page images split from scans named "LIC 1_merged",
"LIC Policy_compressed" and "Scan 1–6" — probably pages of these PDFs.

## How to use
- Open in any PDF viewer. To turn pages into images for a model, use e.g. `pdftoppm -r 300 -png file.pdf out` (poppler) or PyMuPDF.
- For accuracy testing, hand-label the target fields (name, DOB, PAN, address, sum assured, nominee…) and compare model output against the labels using the RFP's KPI definitions.

## Handling
- **Treat as personal data** until confirmed otherwise (names, DOB, PAN, addresses, photos, signatures of policy proposers). Do not upload to external AI services; the RFP requires data to stay in India.
- Whether these are real customer forms, test fills by staff, or forms supplied by LIC: Unknown – ask Chandresh.
