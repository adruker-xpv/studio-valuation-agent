---
name: file-register
description: |-
  Registers incoming portfolio-company files, detects duplicates and versions, invokes File Profiler for new files, compares normalized workbook structure, verifies filing status, and maintains the persistent company file register.

  Use for every newly received valuation-related file or when filing status must be rechecked.

  It records file identity and structural observations. It does not interpret valuation methodology, determine schema compatibility, create or maintain valuation schemas, calculate confidence, calculate valuations, or modify source files.
---
# File Register, Difference Check, and Filing Check

## Purpose

Maintain the immutable file history for each portfolio company.

Register:

`/Valuation Agent MVP/03 Valuation Runs/{Company}/file-index.md`

Company source folder:

`/Valuation Agent MVP/02 Company Sources/{Company}/`

The JSON in `file-index.md` is the system record. The Markdown table is the human-readable view.

## Procedure

### 1. Identify the company

Use, in order:

1. Company explicitly stated by the user.
2. Company name observed inside the file.
3. Existing register match.

Do not identify a company solely from a similar filename.

If company identity cannot be established, return an open question and stop processing that file.

### 2. Read the existing register

Read the company's `file-index.md`.

If none exists, initialize a new register.

Never delete existing entries or history.

### 3. Identify each incoming file

For each attachment, use code to calculate:

- SHA-256;
- file size;
- observed filename;
- normalized filename;
- received timestamp.

Normalize filenames only for matching.

Always preserve the observed filename.

### 4. Detect duplicates

If SHA-256 matches an existing entry:

- classify the file as `duplicate`;
- link it to the existing entry;
- do not profile it again.

Otherwise classify it as `new` and invoke File Profiler.

### 5. Detect versions

For each new profiled file, compare it with registered files having:

- the same file family; and
- the same non-null period end.

Do not supersede files across different or unresolved periods.

Determine precedence using:

1. approved/final status over draft;
2. higher explicit version over lower version;
3. later received timestamp when neither rule resolves precedence.

If status is conflicting or precedence cannot be established, do not supersede automatically. Record the ambiguity as an open question.

Preserve superseded files and their history.

### 6. Compare structure

For each sheet store:

- observed sheet name;
- normalized sheet-name pattern where supported;
- sheet type;
- visibility.

Compare the normalized sheet signature with the latest applicable member of the same file family.

Return:

- added patterns;
- removed patterns;
- sheet-type changes;
- visibility changes;
- unresolved comparisons.

Normal period progression matching the same normalized pattern is not structural change.

A change in raw sheet count, row number, column number, worksheet name, or physical position is an observation only. It does not by itself establish incompatible structure or valuation-methodology change.

### 7. Check filing

For every incoming file, including duplicates:

1. Inspect the applicable company source folder.
2. Match normalized filenames.
3. Compare file size where available.
4. If no filename matches, identify same-size candidates as possible matches.

Assign one:

- `filed`
- `filed_size_differs`
- `possible_match`
- `not_filed`

Record:

- filing status;
- filed path when known;
- checked timestamp.

Do not upload, move, rename, overwrite, or delete source files.

### 8. Update the register

Append new evidence and status changes.

Never:

- delete entries;
- overwrite prior hashes;
- remove supersession history;
- discard previous filing checks;
- replace observed filenames with normalized versions.

## Output

Return a concise summary table containing:

- file;
- result;
- family;
- role;
- status;
- period end;
- actuals through;
- supersession;
- structural observations;
- filing status.

Then return open questions.

Write `file-index.md` using this structure:

# File Register: {Company}

Last updated: {timestamp}

| File | Result | Family | Role | Status | Period End | Actuals Through | Superseded By | Structure Changed | Filed |
|---|---|---|---|---|---|---|---|---|---|

The machine-readable portion must contain:

{
  "company": "",
  "last_updated": "",
  "files": [
    {
      "file_id": "",
      "file_name": "",
      "normalized_name": "",
      "sha256": "",
      "size": 0,
      "received_at": "",
      "received_from": null,
      "result": "",
      "family": "",
      "file_role": "",
      "status": "",
      "status_evidence": [],
      "period_end": null,
      "actuals_through": null,
      "entities": [],
      "superseded_by": null,
      "sheet_signature": [
        {
          "observed_name": "",
          "normalized_pattern": null,
          "type": "",
          "visibility": ""
        }
      ],
      "structure_changed": false,
      "structure_diff": {
        "added": [],
        "removed": [],
        "type_changed": [],
        "visibility_changed": [],
        "unresolved": []
      },
      "filed_status": "",
      "filed_path": null,
      "filed_checked_at": "",
      "open_questions": [],
      "extracted": false,
      "profile": {}
    }
  ]
}

## Restrictions

Do not:

- determine schema compatibility;
- interpret valuation methodology;
- create or maintain valuation schemas;
- determine whether a treatment is generic or company-specific;
- calculate evidence confidence;
- calculate or approve valuations;
- modify source files;
- delete file history;
- infer file contents from filenames when the actual file cannot be inspected.
``