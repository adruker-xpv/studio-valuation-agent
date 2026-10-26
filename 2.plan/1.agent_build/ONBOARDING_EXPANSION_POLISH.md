# Valuation Automation - Onboarding Expansion / Polish Phase

## Purpose

This phase is **not a redesign of onboarding**. The current extractor architecture is sufficiently functional to proceed toward quarterly workbook generation once a clean regression passes. The purpose of this phase is to reduce operational friction, redundant analyst questions, unnecessarily deep tracing, and harness-specific noise while preserving the controls that prevent bad facts from reaching company memory.

All examples below are deliberately anonymized. Do not encode company-specific filenames, sheet names, cells, workbook counts, or valuation facts into reusable logic.

## Current baseline to preserve

The current build already has the right core shape:

- discover the supplied workbook roles rather than relying on filenames;
- construct and verify the material valuation chain;
- identify upstream evidence and downstream reporting relationships;
- preserve material discrepancies for analyst review rather than guessing;
- generate proposed changes and company-memory candidates;
- fingerprint the source set and identify the run;
- checkpoint the extraction so it can resume;
- deterministically verify material relationships;
- require human confirmation before reviewed facts become authoritative memory.

Expansion work must preserve that behavior. Do not trade guardrails for convenience.

---

# P0 - Required before calling onboarding polished

## 1. Active-run context and attachment reuse

### Problem

During a multi-turn onboarding run, the agent can still behave as if each message is a new request: re-deriving Company/Period, considering re-fetching files, or asking for/reasoning about inputs that were already attached and remain available in the active conversation/run.

This is unnecessary analyst friction and exposes harness/logistics details.

### Required behavior

Create an explicit **active-run context** after successful initialization containing at minimum:

- `run_id`
- `company`
- `period`
- run folder
- exact source-set fingerprints
- mapping from source ID to the available attached/local workbook
- current completed stage
- memory path when supplied

For subsequent commands in the **same active conversation**, reuse that context when it remains available and source fingerprints still agree.

Examples:

- `ONBOARDING RESUME` should not require Company, Period or the same workbooks again when the active run already identifies them and the inputs remain available.
- `ONBOARDING REVIEW` should reuse the active run identity and source set; the user should only need to provide genuinely new input, such as a completed review workbook or a memory path that has not already been established.
- If required files are no longer available in the execution environment, ask only for the missing files. Do not ask for every source again.

### Safety boundary

Convenience must never override identity:

- If no unambiguous active run exists, require Company + Period or an explicit run reference.
- If a workbook differs from the active run's fingerprint, invoke the existing source-replacement behavior rather than silently substituting it.
- Never infer a company/period from filenames when two plausible interpretations exist.

### Test

Start extraction with five sources. In the same conversation send only `ONBOARDING RESUME`.

**Pass:** no unnecessary request to re-upload/restate existing inputs; the same source identities are used.

---

## 2. Separate user-facing workflow from harness mechanics

### Problem

Traces expose implementation details such as guessed SharePoint paths, staging directories, shell/script experimentation, checkpoint upload races, file ownership, connector quirks and retry mechanics. These are useful debugging details but poor analyst UX.

### Required behavior

Treat all of the following as internal implementation detail unless an unrecoverable error requires the user's action:

- SharePoint enumeration and path resolution;
- staging files for upload;
- `/app/...` or sandbox/local locations;
- checkpoint filenames/revisions;
- shell quoting/workarounds;
- upload races/retries;
- temporary files;
- individual verification-command experimentation.

The normal user-visible completion response should contain only:

1. **Status:** completed / stopped / needs review.
2. **Material result:** short description of what was established.
3. **User decisions genuinely required:** deduplicated list only.
4. **Next action:** one clear command/action.
5. **Resources:** durable locations or links for the run, review, grading and/or memory artifacts that matter.

Do not return internal checkpoints as user deliverables unless explicitly requested for debugging.

### Test

Run a full extraction that requires internal retries/checkpoint revisions.

**Pass:** the final analyst response does not expose implementation chatter; durable resources and the next action are obvious.

---

## 3. Deduplicate human questions by semantic decision

### Problem

A single underlying valuation disagreement can generate several superficially different questions, for example:

- which valuation multiple is approved;
- which resulting company value is approved;
- whether a downstream report should align;
- which side of a reported-value discrepancy is correct.

These are often consequences of one semantic decision. Asking them separately adds analyst work and can produce internally inconsistent answers.

### Required behavior

Before building the review workbook, perform a **question-consolidation pass**.

Group questions when they share the same underlying unresolved concept and one answer necessarily resolves the others.

Each consolidated question should retain:

- one primary question;
- the competing values/options where available;
- all affected concepts/cells;
- all supporting sources;
- downstream consequences;
- IDs of the raw questions/discrepancies it supersedes.

Do **not** merge merely because questions share a keyword or nearby cells. If semantic equivalence is uncertain, keep them separate or produce an identity question.

### Example

Instead of four questions about a multiple discrepancy and its resulting values, ask one question similar to:

> Which valuation basis was approved for this period? Selecting an option will resolve the applied multiple, company carrying value, and the corresponding reported-value reconciliation listed below.

The exact wording may be generated naturally from the evidence. The implementation should not contain this example as a hard-coded template for one company.

### Test

Provide a synthetic case where one driver difference causes multiple downstream differences.

**Pass:** one analyst decision represents the underlying judgment while downstream effects remain traceable.

---

## 4. Materiality-bounded tracing

### Problem

The extractor can continue tracing hidden source tabs, historical schedules, corroborating copies, return calculations, or error-heavy downstream sheets after the material valuation chain is already sufficiently established.

That increases run complexity without necessarily improving a valuation decision or the quarterly-generation instructions.

### Required behavior

Introduce a generic **material-chain sufficiency rule**.

Tracing is sufficient when the extractor has evidence for the applicable chain components:

1. period / valuation date;
2. valuation method;
3. valuation metric and period/window;
4. selected multiple/rate/assumption;
5. enterprise or asset value calculation;
6. bridge items required to reach equity/value;
7. ownership/waterfall required to reach the fund's value;
8. fund-reported value or downstream reporting relationship, when supplied;
9. source locations needed to update material inputs next quarter;
10. any material discrepancy that prevents a unique interpretation.

After these are sufficiently supported and deterministic checks pass, additional tracing should occur only when it can:

- resolve an open material contradiction;
- identify the source for a material next-quarter update;
- explain a material unexplained value;
- establish required source precedence;
- affect a human decision or memory candidate.

Otherwise record the area as **deferred / non-material to current chain** and stop tracing it.

### Important

Do not use a fixed workbook-size, sheet-count or row-count threshold. Materiality and evidence sufficiency should govern stopping.

### Test

Include large historical/supporting tabs unrelated to the active valuation chain.

**Pass:** the material chain is verified without unnecessary full lineage of unrelated data.

---

## 5. Run/path resolution must be deterministic, not guessed

### Problem

Connector calls can fail when the agent invents an expected SharePoint file path and probes it before the folder/path has been resolved through the available listing/discovery mechanism.

### Required behavior

Keep path/resource resolution separate from valuation reasoning:

1. resolve the relevant parent location using the connector's supported discovery/listing mechanism;
2. determine existing run identities from discovered state;
3. allocate the next run identity in code;
4. create/resolve the durable run folder;
5. use paths returned/resolved by that process for later reads and writes.

Do not probe guessed manifest/checkpoint paths to discover whether a run exists.

This requirement is infrastructure-generic: the valuation model should receive a resolved run context rather than reason about connector path syntax.

### Test

Create existing base and revision runs, then start another run.

**Pass:** the next revision is allocated correctly without 404 probes against invented paths.

---

# P1 - Strong improvements, but do not block generation if P0 + regression pass

## 6. Collapse checkpoint revision noise

Checkpoint revisions are useful for recovery/debugging but should not become first-class user artifacts.

### Required behavior

- Keep revision history internally when useful.
- `run_manifest` points to the current canonical checkpoint for each stage.
- Normal responses/resources show only the canonical final artifacts.
- Debug mode may expose revision history.

Do not remove checkpointing itself.

---

## 7. Make review questions decision-oriented, not forensic

The review workbook should ask analysts for decisions they are qualified to make, not make them interpret the extractor's debugging process.

Good review questions should provide:

- what decision is needed;
- the best evidence/options found;
- affected outputs;
- a suggested answer only when evidence supports one;
- an explicit pending/unknown path.

Avoid questions whose main purpose is to make the analyst confirm that the extractor traced a technical detail correctly when deterministic validation can establish it.

---

## 8. Distinguish source facts, analyst judgments and operational observations

Company memory should retain durable information useful in future quarters. Not every observation from onboarding deserves persistence.

Continue distinguishing at least:

- **mapping/source fact:** where a recurring valuation concept is found;
- **source precedence:** which supplied source should control a recurring concept;
- **method/judgment:** human-approved valuation treatment or assumption;
- **period fact:** historical value for a specific period;
- **operational observation:** temporary error/authentication/draft state seen in one source package.

Operational observations should generally remain run evidence unless the analyst explicitly decides they represent a reusable rule.

---

## 9. Carry source provenance into generation without hard-coding locations

Memory should help generation locate concepts, but generation cannot assume future workbooks have identical coordinates.

Persist both:

- last confirmed location/role/label evidence; and
- semantic concept/relationship.

Generation should first attempt the stored mapping, validate it against labels/role/period/formula context, and fall back to semantic discovery when the location moved.

A location match without semantic validation must not be sufficient to overwrite a workbook.

---

# Do not change

The expansion phase should **not** introduce the following:

- company-specific `if company == ...` logic;
- fixed source workbook counts;
- required source filenames;
- fixed sheet names/cell locations across companies;
- arbitrary workbook-KB limits;
- deterministic rules that replace AI interpretation of ambiguous financial meaning;
- automatic resolution of material discrepancies;
- silent conversion of unknowns into facts;
- removal of source fingerprints, contradiction gates, checkpoints, review or verification;
- changes to a frozen test bench merely to make extractor results pass.

If the frozen test bench needs a legacy filename, provide a narrow compatibility alias/adapter rather than changing grading logic.

---

# Recommended user interaction after polish

## New onboarding

User supplies source workbooks and a short command containing Company + Period.

The agent handles run allocation, source discovery, checkpointing, verification and persistence logistics internally.

At the end it returns approximately:

- extraction status;
- material valuation-chain summary;
- deduplicated analyst decisions;
- next action (`GRADE`, `BUILD REVIEW`, etc.);
- durable resource locations.

## Resume in the same conversation

User should normally be able to say:

`ONBOARDING RESUME`

No repeated attachments or identity fields when the active run is unambiguous and its inputs remain available.

## Review

User supplies only the new completed review file if the active run/source set are still available. Re-attachment is required only when the execution environment no longer contains required originals or identity/fingerprint validation requires it.

---

# Regression suite for this expansion phase

The builder should add generic tests covering:

1. **conversation reuse:** resume uses unchanged active inputs without needless re-upload;
2. **missing-session input:** only unavailable required sources are requested;
3. **source replacement:** changed contents trigger the source lock;
4. **semantic question deduplication:** one driver conflict does not produce several equivalent analyst decisions;
5. **non-equivalent questions:** superficially similar but distinct concepts remain separate;
6. **materiality stop:** irrelevant deep tabs are deferred once the material chain is sufficient;
7. **materiality override:** tracing continues when needed to resolve a material unexplained value;
8. **run allocation:** revision folders are resolved/created without guessed-path probes;
9. **artifact UX:** final response lists canonical durable outputs, not staging/checkpoint clutter;
10. **memory portability:** moved cell/layout is rediscovered semantically rather than blindly overwritten;
11. **backward compatibility:** legacy run/artifact naming remains readable where required;
12. **guardrail regression:** contradictions and unresolved judgments cannot become confirmed memory.

---

# Exit criteria

Do not keep iterating on onboarding after these conditions are met:

1. A clean historical package extracts and grades against the frozen corrected Gold with no wrong/false confirmed core answer.
2. Fresh review writes a coherent new company-memory file with no contradictory confirmed state for a concept.
3. A separate new run demonstrates that confirmed memory is genuinely reused and pending decisions remain pending.
4. Analyst questions are reasonably deduplicated rather than multiplied by downstream consequences.
5. A normal run can complete without exposing harness/path/staging mechanics to the analyst.
6. Source replacement still stops unsafe reuse.

Once these pass, freeze onboarding except for defects discovered by broader-company regression testing and begin the quarterly workbook-generation phase.

---

# Future enhancements to log, not block generation

- quality metrics for analyst-question count/reduction across memory-enabled runs;
- richer semantic concept IDs across structurally different companies;
- confidence/coverage reporting for source-role discovery;
- automatic comparison of generation outputs against analyst-final workbooks;
- UI links/cards for run, review, grading and memory resources;
- larger multi-company regression corpus;
- performance telemetry for workbook evidence volume, timeouts and truncation;
- optional debug trace that exposes the checkpoint/provenance details hidden from normal analyst UX.
