# XPV AI Valuation Platform
## MVP Architecture Specification and Build Guide

**Document status:** Build-ready working specification  
**Version:** 1.0  
**Primary implementation stack:** Microsoft Copilot Studio, agent flows, SharePoint document libraries, SharePoint Lists, Excel, Office Scripts  
**MVP pilot:** One portfolio company, one historical quarter, followed by one new quarter  
**Primary output:** A company-specific quarterly valuation workbook  
**Downstream output:** The Fund III valuation package  

---

## 1. Executive summary

XPV needs a repeatable way to convert portfolio-company monthly financial statements and balance sheets into a company-specific quarterly valuation workbook, and then use approved company valuations to populate the Fund III valuation package.

The solution must not be a manually maintained Excel template with a large amount of hard-coded logic. It must be an AI-assisted valuation platform that:

1. Reads new monthly financial statements and balance sheets.
2. Reads prior valuation workbooks and prior LP reporting packages when needed.
3. Infers the company’s established valuation methodology from approved historical examples.
4. Applies XPV’s generic valuation and EBITDA-adjustment policies.
5. Applies company-specific historical rules over the generic rules.
6. Applies quarter-specific facts and decisions over company rules.
7. Applies explicit human instructions and overrides over all other layers.
8. Calculates the required valuation outputs.
9. Writes transparent formulas into Excel so reviewers and auditors can trace calculations through cell references.
10. Preserves the source, transformation, policy, confidence, and decision history for every material output.
11. Allows a reviewer to chat with the agent and make targeted changes without rerunning the entire process.
12. Produces an approved company valuation workbook before any Fund III roll-up occurs.

The recommended MVP is one conversational **Company Valuation Agent** in Copilot Studio, supported by deterministic agent flows. The agent handles file intake interpretation, financial extraction, historical-methodology analysis, policy application, exception handling, and conversational changes. Agent flows handle predictable operations such as creating records, copying templates, running validations, writing outputs, routing reviews, and regenerating affected workbook sections.

The system uses SharePoint for MVP storage. Original documents remain in SharePoint libraries. Structured facts, decisions, confidence components, overrides, review items, output values, and audit events are stored in SharePoint Lists.

The design follows this rule hierarchy:

```text
Generic XPV policy
        ↓ overridden by
Company methodology and approved historical decisions
        ↓ overridden by
Quarter-specific facts and decisions
        ↓ overridden by
Explicit human decisions and changes
```

The first production output is always the company’s valuation workbook. The Fund III package is created later from approved company valuation records, not directly from raw monthly statements.

---

## 2. Final design decisions

The following decisions are considered settled for the MVP.

### 2.1 Platform

- Use Microsoft Copilot Studio as the primary agent platform.
- Use Copilot Studio agent flows for deterministic workflow steps that are closely connected to the agent.
- Use Power Automate only where it is more practical for SharePoint triggers, approvals, notifications, document copying, scheduled jobs, or organization-managed connections.
- Use SharePoint document libraries and SharePoint Lists for MVP storage.
- Do not require Python, a local development environment, or a command line for business users.
- Keep implementation artifacts in a Power Platform solution where available so the solution can be exported, versioned, and moved between environments.

### 2.2 Agent structure

Use two top-level agents eventually:

1. **Company Valuation Agent**
   - Produces and maintains company valuation workbooks.
   - Combines intake, extraction, methodology inheritance, adjustment analysis, valuation preparation, review handling, and conversational changes.

2. **Fund III Aggregation Agent**
   - Consumes approved company valuation records.
   - Produces the Fund III valuation package and fund-level calculations.
   - Is out of scope for the first working MVP, except for defining its required company-output contract.

### 2.3 Calculation transparency

- Calculations must be visible in Excel.
- Material results should reference cells or structured Excel tables.
- The agent may calculate values outside Excel to validate or prepare them, but the generated workbook must contain formulas that reproduce the material calculations.
- The workbook must include a calculation sheet, source-lineage sheet, decision sheet, review sheet, and audit sheet.
- Hard-coded calculated outputs are not acceptable unless clearly labeled as approved manual overrides.

### 2.4 AI decisions

- AI may automatically apply high-confidence mappings and adjustment decisions.
- Every AI-applied valuation decision remains visible in the review queue.
- Human reviewers may approve, reject, modify, or override items through the workbook or conversational agent.
- Human instructions take precedence and are recorded as explicit decision events.

### 2.5 Comparables

- For the MVP, carry forward the company’s approved historical comparable set and methodology.
- Mark comparable values, inclusions, exclusions, discounts, outliers, and selected multiples for human review each quarter.
- Do not build PitchBook integration in the MVP.
- Preserve a defined market-data interface so PitchBook can be added later without redesigning the valuation engine.

### 2.6 Source hierarchy

Approved historical valuation workbooks and LP packages may define company-specific methodology, formulas, outputs, and precedents. They do not automatically override generic policy. Where historical treatment conflicts with current generic policy, the agent creates a review item.

---

## 3. Problem statement

Portfolio companies submit financial information in different workbook layouts. Labels, tabs, entities, date formats, currencies, calculation styles, adjustment schedules, and level of detail vary.

At the same time, each company may have an established valuation approach reflected in prior approved valuation workbooks. Examples of company variation include:

- EV/Adjusted EBITDA versus EV/Revenue.
- TTM adjusted EBITDA versus a three-year average adjusted EBITDA.
- Different liquidity discounts.
- Different public-company and M&A comparable sets.
- Different definitions of cash, debt, net debt, debt-like items, and net assets.
- Different cap-table and waterfall mechanics.
- Different ownership measures.
- Different attribution drivers.
- Different treatment of acquisitions, pro forma results, discontinued operations, alternatives, and outliers.

A single static workbook cannot safely cover every company unless it becomes overly complex. A fully custom workbook per company is difficult to maintain and automate.

The platform therefore needs controlled inheritance:

```text
generic rule + company configuration + quarter state + human override
```

The platform also needs AI because manual account mapping, manual historical-model interpretation, and manual adjustment classification would leave too much work with the user and limit scalability.

The design must balance four goals:

1. **Automation:** minimize repetitive analyst work.
2. **Consistency:** preserve XPV policy and established company methodology.
3. **Auditability:** prove where every material number and decision came from.
4. **Reviewability:** keep humans in control of material valuation judgments.

---

## 4. Scope

### 4.1 In scope for the MVP

- SharePoint folder structure and document libraries.
- SharePoint Lists for structured state and audit history.
- One Company Valuation Agent in Copilot Studio.
- Agent flows for extraction, record creation, review routing, calculations, and workbook generation.
- Ingestion of Excel and PDF source documents.
- New-company onboarding from prior valuation workbooks and prior LP reports.
- Existing-company quarterly updates from new monthly financial statements and balance sheets.
- Generic-to-company-to-quarter-to-human rule resolution.
- AI account mapping.
- AI extraction of valuation-required fields.
- AI adjustment classification using XPV’s nine adjustment categories.
- Evidence-based confidence scoring.
- Auto-application of high-confidence decisions with reviewer visibility.
- Company valuation records.
- Company valuation workbook generation.
- Workbook formulas and cell references.
- Source lineage and decision lineage.
- Delta recalculation after chat-based changes.
- Fixed historical comparable set with review flags.
- Pilot evaluation against an approved historical quarter.

### 4.2 Out of scope for the initial MVP

- Direct PitchBook integration.
- Automated market-data retrieval.
- Automated final valuation approval.
- Automated legal interpretation of cap tables or vesting provisions.
- Fully autonomous selection of new comparable companies.
- Fully autonomous acceptance of new treatment that conflicts with policy or historical precedent.
- Fund III workbook generation, except for defining the downstream data contract.
- Dataverse migration.
- Power BI reporting.
- Replacing the official Excel deliverable.
- Rebuilding every formula or every financial schedule that appears in a source workbook.

### 4.3 MVP success condition

The MVP is successful when it can:

1. Reproduce an approved historical company valuation from known source documents within agreed tolerances.
2. Produce a new-quarter company valuation working draft from new monthly statements.
3. Show all sources and decisions for the required LP-report fields.
4. Generate an Excel workbook with traceable formulas.
5. Accept a targeted conversational change and regenerate only the affected records and workbook sections.
6. Produce a review package that clearly separates AI-applied, human-approved, unresolved, and overridden items.

---

## 5. Guiding principles

### 5.1 Company workbook first

The system’s primary output is the approved company valuation workbook. Fund III reporting uses approved company valuation records after company-level review.

### 5.2 Extract only what is needed

Do not extract every line from every workbook by default. Extract fields required to:

- Calculate the approved company valuation methodology.
- Populate the company valuation workbook.
- Populate required LP-report fields.
- Support attribution.
- Support reviews and reconciliations.
- Provide audit evidence.

Additional source data may be extracted when needed to discover adjustment candidates or reconcile totals, but it does not need to become part of the permanent valuation model unless relevant.

### 5.3 Preserve source truth

Never overwrite an original source file. Every extracted fact must retain a reference to its origin.

### 5.4 Distinguish facts, calculations, decisions, and outputs

- **Fact:** extracted directly from a source.
- **Calculation:** created deterministically from facts or other calculations.
- **Decision:** selects treatment, inclusion, method, category, override, or approval.
- **Output:** a value presented in the valuation workbook or LP package.

The system must never store all four as an undifferentiated value.

### 5.5 Historical consistency with controlled challenge

Prior approved workbooks are strong evidence of company-specific methodology. They are not proof that every historical formula or category remains correct.

### 5.6 Human decisions win

Explicit human decisions override generic rules, historical company rules, quarter-level AI decisions, and confidence thresholds. The override must include scope, reasoning, effective period, and user identity.

### 5.7 No hidden AI arithmetic

AI may interpret and classify. Deterministic calculations should occur through defined formulas and be represented in Excel.

### 5.8 Review by exception

Humans should focus on:

- New or changed source labels.
- Low-confidence mappings.
- New adjustment types.
- Policy conflicts.
- Pro forma overlap.
- Unreconciled totals.
- New market inputs.
- Cap-table changes.
- Material changes in outputs.
- AI-applied items selected for sampling.

---

## 6. Target operating model

### 6.1 End-to-end process

```text
Portfolio company uploads monthly financial statements and balance sheets
                                  |
                                  v
SharePoint stores immutable source documents and metadata
                                  |
                                  v
Company Valuation Agent identifies company, period, source type, and required work
                                  |
                                  v
Agent retrieves generic policy, company profile, current quarter state, and historical examples
                                  |
                                  v
Agent extracts only valuation-relevant facts and adjustment candidates
                                  |
                                  v
Agent scores evidence, historical match, policy match, reconciliation, and consistency
                                  |
                                  v
Agent applies decisions or routes exceptions according to thresholds
                                  |
                                  v
Deterministic agent flow creates valuation records and Excel formulas
                                  |
                                  v
Company valuation workbook is generated or incrementally updated
                                  |
                                  v
Human reviews AI-applied and unresolved items, then chats or edits decisions
                                  |
                                  v
Only affected items and workbook sections are recalculated
                                  |
                                  v
Approved company valuation record becomes available to Fund III aggregation
```

### 6.2 Quarterly process status

Each company-quarter uses the following states:

```text
Created
Sources Pending
Sources Received
Extraction Running
Extraction Review
Valuation Draft
Decision Review
Ready for Approval
Approved
Released
Reopened
Superseded
```

A status change must be recorded in the audit log.

### 6.3 Roles

#### Agent maker

- Builds and maintains the Copilot Studio agent and flows.
- Updates prompts, thresholds, and test cases.
- Does not approve final valuations by virtue of being the maker.

#### Valuation operator

- Starts or monitors company-quarter runs.
- Reviews exceptions.
- Resolves source and mapping issues.
- Requests changes through chat.

#### Valuation reviewer

- Reviews AI-applied decisions, material adjustments, methods, market inputs, and workbook outputs.
- Approves, rejects, or overrides decisions.

#### Final approver

- Approves the company valuation for release.

#### SharePoint owner

- Owns access, retention, library configuration, list structure, and permissions.

#### Power Platform administrator

- Owns environments, connections, capacity, data policies, solution deployment, and production publishing.

---

## 7. Solution architecture

### 7.1 Components

#### Copilot Studio

Contains:

- Company Valuation Agent.
- System instructions.
- Knowledge sources.
- Tools and agent flows.
- Conversation topics where deterministic control is needed.
- Test sets and evaluation results.
- Publishing configuration.

#### Agent flows

Contain deterministic operations such as:

- Create company-quarter record.
- Retrieve active rules.
- Retrieve source metadata.
- Write extracted facts.
- Write decisions and confidence components.
- Resolve effective rules.
- Calculate valuation outputs.
- Populate or update workbook tables.
- Add Excel formulas.
- Create review items.
- Apply conversational changes.
- Recalculate dependent outputs.
- Validate release readiness.

#### Power Automate

Use when appropriate for:

- SharePoint file-created triggers.
- Scheduled monitoring.
- Copying templates.
- Standard approval actions.
- Notifications.
- Long-running document orchestration.
- Calling Office Scripts against Excel files.
- Moving released documents.

Do not duplicate the same business logic in both agent flows and Power Automate. Choose one owner for each operation.

#### SharePoint document libraries

Store original documents, templates, working workbooks, approved outputs, and archived evidence.

#### SharePoint Lists

Store structured platform state, facts, decisions, outputs, dependencies, and audit events.

#### Excel

Acts as:

- Calculation display.
- Traceable formula model.
- Reviewer interface.
- Deliverable format.
- Auditor evidence package.

Excel is not the workflow database.

#### Office Scripts

Use for deterministic workbook actions:

- Create or refresh structured tables.
- Write formulas.
- Apply formatting.
- Add source links and IDs.
- Lock or protect calculated areas.
- Validate formulas and reconciliation checks.
- Export final PDF if required.

### 7.2 Why one Company Valuation Agent

The intake, extraction, and methodology-inheritance functions operate on the same company and quarter context. Combining them avoids:

- Repeated retrieval of the same sources.
- Conflicting company identification.
- Redundant prompts.
- Complicated handoffs.
- Loss of context between agents.

The agent should still use separate tools or flows internally. One agent does not mean one unstructured prompt.

### 7.3 Why a separate Fund III Aggregation Agent later

Fund-level aggregation has different responsibilities:

- Confirm only approved company records are consumed.
- Aggregate investment values and proceeds.
- Calculate fund-level MOIC, IRR, DPI, TVPI, and totals.
- Produce fund attribution and projections.
- Reconcile to company-level records.

Keeping it separate avoids mixing raw company-document reasoning with fund-level reporting.

---

## 8. Rule inheritance and state resolution

### 8.1 Effective-rule order

For each decision or calculation parameter, resolve in this order:

1. Find the active generic rule.
2. Apply an active approved company override if one exists.
3. Apply an active approved quarter override if one exists.
4. Apply the latest explicit human decision if one exists and is in scope.
5. Record which layer supplied the effective value.

```text
Effective value = Human override
               else Quarter rule
               else Company rule
               else Generic rule
```

### 8.2 Scope types

- `Generic`: applies to all companies.
- `Company`: applies to one company until superseded.
- `Quarter`: applies to one company-quarter.
- `DecisionOnly`: applies to one specific record or adjustment.

### 8.3 Effective dating

Every rule or override must include:

- Effective from.
- Effective to, if temporary.
- Status.
- Superseded-by reference.
- Source evidence.
- Approver.

### 8.4 Conflict handling

When two active records at the same scope conflict:

- Do not choose silently.
- Create a critical review item.
- Use the last approved value only if policy explicitly permits latest-approved resolution.
- Record the conflict and affected outputs.

### 8.5 Conversational override examples

User request:

> For Company A Q2 2027, reject the ERP adjustment because it is recurring licensing, then regenerate the valuation.

Agent actions:

1. Locate the adjustment record.
2. Explain current category, confidence, source, and inclusion.
3. Confirm scope from the request as `DecisionOnly` for Q2 2027.
4. Create a human rejection decision.
5. Set included amount to zero.
6. Identify dependent calculations.
7. Recalculate adjusted EBITDA, enterprise value, equity value, ownership value, attribution, MOIC, IRR, and affected narratives.
8. Update workbook cells and formulas.
9. Create an audit event.
10. Return a concise summary of changed outputs.

The source extraction is not rerun.

---

## 9. SharePoint information architecture

### 9.1 Site

Create one team-owned SharePoint site:

```text
AI Valuation Platform
```

Do not build the production platform under an individual user’s personal OneDrive.

### 9.2 Document libraries

#### `01 Policies and Templates`

Contains:

- Generic valuation policy.
- EBITDA adjustment policy.
- Company workbook template.
- Fund III output template.
- Agent prompt documentation.
- Calculation specification.
- Data dictionary.

#### `02 Company Sources`

Folder structure:

```text
02 Company Sources/
  [CompanyID]/
    Prior Valuations/
    Prior LP Reports/
    Monthly Financials/
      [YYYY_Q#]/
    Adjustment Support/
      [YYYY_Q#]/
    Cap Table/
    Market Inputs/
    Other Evidence/
```

#### `03 Working Valuations`

```text
03 Working Valuations/
  [CompanyID]/
    [YYYY_Q#]/
      [CompanyID]_[YYYY_Q#]_Valuation_WORKING.xlsx
```

#### `04 Approved Company Valuations`

```text
04 Approved Company Valuations/
  [CompanyID]/
    [YYYY_Q#]/
      [CompanyID]_[YYYY_Q#]_Valuation_APPROVED.xlsx
      [CompanyID]_[YYYY_Q#]_Valuation_APPROVED.pdf
```

#### `05 Fund III Packages`

Contains approved Fund III workbooks and PDFs.

#### `06 Audit Exports`

Contains quarter-level evidence packages exported for auditors.

### 9.3 Required file metadata

Add library columns:

- Company ID.
- Company display name.
- Quarter ID.
- Period end.
- Document type.
- Source status.
- Version classification.
- Is authoritative.
- Superseded by.
- Confidentiality label.
- Ingestion status.
- Ingestion run ID.
- Notes.

### 9.4 Permissions

Use least privilege:

- Source uploaders may add source documents but should not alter approved outputs.
- Operators may edit working records and workbooks.
- Reviewers may update review decisions.
- Final approvers may release valuations.
- Only platform owners may edit policies, templates, agent instructions, and production flows.

---

## 10. SharePoint Lists

Create the following Lists. Use stable IDs and lookup columns where practical. Avoid using display names as keys.

### 10.1 `Companies`

Purpose: master record for portfolio companies.

Columns:

- `CompanyID` text, unique.
- `CompanyName` text.
- `Fund` choice.
- `DefaultCurrency` choice.
- `FiscalYearEnd` text.
- `Active` yes/no.
- `CurrentMethodologyProfileVersion` text.
- `CurrentWorkbookTemplateVersion` text.
- `CompanySourcesFolder` hyperlink.
- `WorkingFolder` hyperlink.
- `ApprovedFolder` hyperlink.
- `Owner` person.
- `ReviewerGroup` person/group.
- `FinalApproverGroup` person/group.

### 10.2 `CompanyQuarters`

Purpose: state of each valuation run.

Columns:

- `CompanyQuarterID` text, unique. Example `COMPANYA-2027-Q2`.
- `CompanyID` lookup.
- `QuarterID` text.
- `ValuationDate` date.
- `Status` choice.
- `PriorCompanyQuarterID` lookup.
- `RunID` text.
- `WorkingWorkbookURL` hyperlink.
- `ApprovedWorkbookURL` hyperlink.
- `StartedAt` date/time.
- `LastCalculatedAt` date/time.
- `ApprovedAt` date/time.
- `ApprovedBy` person.
- `ReleaseCheckStatus` choice.
- `CurrentProfileVersion` text.
- `GenericPolicyVersion` text.

### 10.3 `PolicyRules`

Purpose: generic policies and structured decision criteria.

Columns:

- `RuleID` text, unique.
- `RuleType` choice.
- `Category` choice.
- `RuleName` text.
- `RuleText` multiple lines.
- `StructuredCondition` multiple lines.
- `AllowedDecision` choice.
- `RequiredEvidence` multiple lines.
- `AutoApplyEligible` yes/no.
- `MaterialityRule` multiple lines.
- `EffectiveFrom` date.
- `EffectiveTo` date.
- `Version` text.
- `Status` choice.
- `ApprovedBy` person.
- `ApprovalDate` date.
- `SourceDocumentURL` hyperlink.

### 10.4 `CompanyMethodologyProfiles`

Purpose: approved child configuration derived from historical workbooks and decisions.

Columns:

- `ProfileRecordID` text, unique.
- `CompanyID` lookup.
- `ProfileVersion` text.
- `AttributeName` text.
- `AttributeValue` multiple lines.
- `DataType` choice.
- `SourceDocumentURL` hyperlink.
- `SourceSheet` text.
- `SourceCellOrRange` text.
- `SourceQuarter` text.
- `ConfidenceScore` number.
- `Status` choice.
- `ApprovedBy` person.
- `ApprovalDate` date.
- `EffectiveFrom` date.
- `EffectiveTo` date.
- `SupersededBy` text.
- `Notes` multiple lines.

Example attributes:

- Valuation method.
- Earnings metric.
- Earnings period.
- Comparable set.
- Comparable aggregation method.
- Liquidity discount.
- Equity bridge.
- Cap-table method.
- Attribution drivers.
- Required output fields.
- Narrative pattern.
- Source-label synonym.

### 10.5 `SourceDocuments`

Purpose: structured index of documents.

Columns:

- `SourceDocumentID` text, unique.
- `CompanyID` lookup.
- `CompanyQuarterID` lookup.
- `DocumentType` choice.
- `FileURL` hyperlink.
- `FileName` text.
- `DocumentPeriodEnd` date.
- `Currency` choice.
- `Authoritative` yes/no.
- `FileHashOrVersion` text.
- `IngestionStatus` choice.
- `IngestionRunID` text.
- `CreatedAt` date/time.
- `SupersededBy` text.

### 10.6 `ExtractedFacts`

Purpose: source-grounded numbers and text.

Columns:

- `FactID` text, unique.
- `CompanyID` lookup.
- `CompanyQuarterID` lookup.
- `CanonicalField` text.
- `ValueNumber` number.
- `ValueText` multiple lines.
- `Currency` choice.
- `PeriodStart` date.
- `PeriodEnd` date.
- `Entity` text.
- `Scenario` choice.
- `SourceDocumentID` lookup.
- `SourceSheetOrPage` text.
- `SourceCellOrRange` text.
- `SourceLabel` text.
- `SourceFormula` multiple lines.
- `ExtractionMethod` choice.
- `ExtractionConfidence` number.
- `ReconciliationStatus` choice.
- `Status` choice.
- `SupersededBy` text.

### 10.7 `AdjustmentCandidates`

Purpose: proposed and approved EBITDA adjustments.

Columns:

- `AdjustmentID` text, unique.
- `CompanyID` lookup.
- `CompanyQuarterID` lookup.
- `MonthEnd` date.
- `Entity` text.
- `Description` multiple lines.
- `Amount` currency.
- `ProposedCategory` choice.
- `EffectiveCategory` choice.
- `RecurringAssessment` choice.
- `ProFormaOverlap` choice.
- `PolicyRuleID` lookup.
- `HistoricalExampleIDs` multiple lines.
- `SourceFactIDs` multiple lines.
- `OverallConfidence` number.
- `AutomationDecision` choice.
- `ReviewStatus` choice.
- `IncludedAmount` currency.
- `Reviewer` person.
- `ReviewDate` date/time.
- `ReviewComment` multiple lines.
- `DecisionID` text.

### 10.8 `Decisions`

Purpose: every AI or human decision affecting the valuation.

Columns:

- `DecisionID` text, unique.
- `CompanyID` lookup.
- `CompanyQuarterID` lookup.
- `DecisionType` choice.
- `Scope` choice.
- `TargetRecordType` choice.
- `TargetRecordID` text.
- `PreviousValue` multiple lines.
- `DecisionValue` multiple lines.
- `DecisionReason` multiple lines.
- `DecisionSource` choice.
- `PolicyRuleIDs` multiple lines.
- `HistoricalEvidenceIDs` multiple lines.
- `ConfidenceScore` number.
- `Status` choice.
- `DecisionBy` person or text.
- `DecisionAt` date/time.
- `EffectiveFrom` date.
- `EffectiveTo` date.
- `SupersedesDecisionID` text.

### 10.9 `ConfidenceComponents`

Purpose: explain the confidence score.

Columns:

- `ConfidenceRecordID` text, unique.
- `TargetRecordType` choice.
- `TargetRecordID` text.
- `EvidenceScore` number.
- `HistoricalMatchScore` number.
- `PolicyMatchScore` number.
- `ReconciliationScore` number.
- `CrossSourceConsistencyScore` number.
- `AmbiguityPenalty` number.
- `NoveltyPenalty` number.
- `MaterialityPenalty` number.
- `OverallConfidence` number.
- `ConfidenceVersion` text.
- `Explanation` multiple lines.

### 10.10 `ValuationInputs`

Purpose: effective inputs used in formulas.

Columns:

- `InputID` text, unique.
- `CompanyQuarterID` lookup.
- `InputName` text.
- `InputValue` number.
- `InputText` multiple lines.
- `Unit` text.
- `SourceType` choice.
- `SourceRecordIDs` multiple lines.
- `EffectiveRuleLayer` choice.
- `DecisionID` text.
- `Status` choice.

### 10.11 `ValuationOutputs`

Purpose: company-level results and the contract for Fund III.

Columns:

- `OutputID` text, unique.
- `CompanyQuarterID` lookup.
- `OutputName` text.
- `OutputValue` number.
- `OutputText` multiple lines.
- `Unit` text.
- `ExcelSheet` text.
- `ExcelCell` text.
- `ExcelFormula` multiple lines.
- `DependencyInputIDs` multiple lines.
- `ReconciliationStatus` choice.
- `Status` choice.

### 10.12 `ReviewQueue`

Purpose: reviewer worklist.

Columns:

- `ReviewItemID` text, unique.
- `CompanyQuarterID` lookup.
- `Area` choice.
- `TargetRecordType` choice.
- `TargetRecordID` text.
- `Summary` multiple lines.
- `Severity` choice.
- `ReviewReason` choice.
- `AIRecommendation` multiple lines.
- `ConfidenceScore` number.
- `Status` choice.
- `AssignedTo` person/group.
- `CreatedAt` date/time.
- `ResolvedAt` date/time.
- `ResolvedBy` person.
- `Resolution` multiple lines.

### 10.13 `CalculationDependencies`

Purpose: dependency graph for incremental recalculation.

Columns:

- `DependencyID` text, unique.
- `CompanyQuarterID` lookup.
- `UpstreamType` choice.
- `UpstreamID` text.
- `DownstreamType` choice.
- `DownstreamID` text.
- `CalculationName` text.
- `WorkbookSheet` text.
- `WorkbookCell` text.
- `Active` yes/no.

### 10.14 `AuditEvents`

Purpose: immutable operational and decision history.

Columns:

- `AuditEventID` text, unique.
- `CompanyQuarterID` lookup.
- `EventType` choice.
- `ActorType` choice.
- `Actor` text.
- `TargetRecordType` choice.
- `TargetRecordID` text.
- `BeforeValue` multiple lines.
- `AfterValue` multiple lines.
- `Reason` multiple lines.
- `SourceRunID` text.
- `Timestamp` date/time.
- `CorrelationID` text.

---

## 11. Minimum output contract

### 11.1 Company valuation workbook outputs

The exact required fields may vary by company methodology, but the generic contract should support:

- Company name.
- Valuation date.
- Currency.
- Valuation methodology.
- Current period.
- Prior period.
- Prior year, where required.
- Selected valuation multiple or parameter.
- Reported valuation metric.
- Approved adjustments.
- Adjusted valuation metric.
- Enterprise value.
- Cash.
- Debt.
- Other enterprise-to-equity bridge items.
- Equity value.
- Investment cost.
- Investment value.
- Fully diluted ownership.
- Effective ownership.
- MOIC.
- Gross IRR.
- Proceeds.
- Attribution by required driver.
- Adjustment detail by category and month.
- Comparable summary.
- Comparable descriptions and rationale.
- Methodology narrative.
- Recommendation adjustment.
- Review and approval status.
- Source and decision lineage.

### 11.2 Fund III downstream contract

Every approved company-quarter should expose at least:

- Company ID.
- Valuation date.
- Fully diluted ownership.
- Invested capital.
- Prior valuation.
- Prior proceeds.
- New investments.
- Change in unrealized or realized performance.
- Current valuation.
- Current proceeds.
- MOIC.
- Gross IRR.
- Gross DPI.
- Projection values if approved and applicable.
- Company valuation workbook URL.
- Approval date.
- Output version.

The Fund III agent must consume only approved records.

---

## 12. Company valuation workbook design

The workbook should be generic in structure but populated using company-specific configuration.

### 12.1 Required sheets

1. `00 Control`
2. `01 Source Register`
3. `02 Source Lineage`
4. `03 Monthly Financials`
5. `04 Adjustment Detail`
6. `05 Pro Forma Bridge`
7. `06 Calculation Engine`
8. `07 Comparables`
9. `08 Valuation Summary`
10. `09 Waterfall and Ownership`
11. `10 Attribution`
12. `11 LP Output`
13. `12 Review Queue`
14. `13 Decisions`
15. `14 Audit Log`
16. `15 Checks`

Sheets not needed for a company may be hidden but should not be deleted if downstream formulas depend on the common structure.

### 12.2 Formula rules

- Use Excel Tables and structured references where practical.
- Avoid hidden formula constants.
- Place selected assumptions in named input cells.
- Mark source facts, formulas, AI decisions, and human overrides visually differently.
- Include formula checks beside material outputs.
- Use formulas for totals, TTM periods, adjusted metrics, enterprise value, equity bridge, proceeds, MOIC, IRR, and attribution.
- If the calculation was prepared outside Excel, write an equivalent formula into the workbook and compare the workbook result with the external result.
- Any manual override cell must show the original calculated value, override value, reason, decision ID, and approver.

### 12.3 Lineage display

The `02 Source Lineage` sheet should include:

- Output or input name.
- Value.
- Source document.
- Source sheet/page.
- Source cell/range.
- Original source label.
- Transformation.
- Rule ID.
- Decision ID.
- Confidence score.
- Review status.

### 12.4 Calculation engine

The calculation sheet should include named sections:

- Period selection.
- Monthly-to-quarter aggregation.
- Monthly-to-TTM aggregation.
- Reported EBITDA.
- Adjustment aggregation.
- Pro forma bridge.
- Adjusted EBITDA or alternative metric.
- Comparable aggregation.
- Discount calculation.
- Enterprise value.
- Equity bridge.
- Ownership and waterfall.
- Return calculations.
- Attribution.
- Fund III output contract.

---

## 13. Company methodology onboarding

### 13.1 Inputs

For a new company, provide:

- At least one approved prior valuation workbook.
- Preferably two historical quarters to distinguish stable methodology from quarter-specific values.
- Prior LP valuation report or PDF.
- Relevant adjustment schedules.
- Current generic policy.
- Cap-table or ownership support.

### 13.2 Historical workbook analysis

The agent should identify:

- Which sheets produce deliverable outputs.
- Which formulas generate key values.
- Which cells are hard coded.
- Which source workbooks are linked.
- Which periods are used.
- Which valuation methods are active.
- Which valuation metric is used.
- How adjusted EBITDA is built.
- How pro forma values are incorporated.
- How comparables are aggregated.
- What discount is used.
- How enterprise value becomes equity value.
- How ownership is applied.
- How waterfall proceeds are calculated.
- How MOIC and IRR are calculated.
- Which attribution drivers are used.
- Which LP fields and narratives are produced.

### 13.3 Profile proposal

The agent proposes profile records with:

- Attribute.
- Proposed value.
- Source workbook.
- Sheet and cell/range.
- Historical consistency.
- Generic-policy compatibility.
- Confidence.
- Required review question.

### 13.4 Approval

Profile records may be:

- AI applied and queued for scan.
- Recommended for review.
- Blocked pending human input.
- Rejected.
- Replaced by generic policy.

After approval, the profile is versioned. Future quarters use the profile rather than rereading all historical workbooks unless:

- A methodology change occurs.
- A source layout changes materially.
- A reviewer requests re-analysis.
- A conflict appears.

---

## 14. Financial extraction strategy

### 14.1 Required-first extraction

The agent first retrieves the company methodology profile and LP output contract. It generates a required-field plan before reading the current source documents.

Example:

```text
Required for this company-quarter:
- Monthly reported EBITDA for the active earnings period
- Revenue for LP reporting
- Cash at quarter end
- Debt at quarter end
- Adjustment candidates and support
- Ownership and cap-table changes
- Current historical comparable set and values
```

### 14.2 Source parsing

For each source workbook:

- Identify candidate income-statement sheets.
- Identify candidate balance-sheet sheets.
- Identify monthly columns and dates.
- Identify entity and consolidation level.
- Detect formulas versus hard-coded values.
- Detect subtotals and grand totals.
- Detect hidden sheets and external links when accessible.
- Preserve source locations.

### 14.3 AI mapping

The agent maps source labels to canonical fields using:

1. Exact prior approved company mapping.
2. Semantic similarity to prior company mappings.
3. Generic financial synonyms.
4. Formula and subtotal context.
5. Position within the statement.
6. Cross-source consistency.
7. Reconciliation with reported totals.

Manual mapping is not the standard workflow. Unresolved mappings enter review.

### 14.4 Missing adjustments

When a company does not provide a listed adjustment schedule:

- Do not assume every unusual expense is an adjustment.
- Search the detailed income statement and supporting schedules for candidates.
- Propose adjustment candidates only when evidence exists.
- Apply policy and historical examples.
- Mark them as AI applied, recommended, or needs input according to confidence.
- Preserve reported EBITDA even if there are no approved adjustments.

### 14.5 Reconciliation

Required reconciliations include:

- Monthly totals to reported quarter totals where available.
- TTM total to sum of twelve months.
- Balance-sheet cash and debt to quarter-end source.
- Adjustment detail to adjustment total.
- Pro forma bridge to approved pro forma metric.
- Valuation formula to workbook output.
- Waterfall total to equity value.
- Attribution total to change in investment value.

---

## 15. Confidence methodology

### 15.1 Principle

Do not use the model’s self-reported confidence as the primary score. Confidence must be calculated from observable evidence.

### 15.2 Score components

Use a 100-point score.

#### Evidence quality: 0 to 25

- 25: direct authoritative source, exact period, exact entity, exact location.
- 20: authoritative source with minor labeling ambiguity.
- 15: secondary approved source or derived from clear source formula.
- 10: indirect support.
- 0: no sufficient evidence.

#### Historical company match: 0 to 20

- 20: exact mapping or treatment repeatedly approved for the company.
- 15: exact mapping or treatment approved once.
- 10: close company-specific precedent.
- 5: generic precedent only.
- 0: new treatment.

#### Policy match: 0 to 20

- 20: explicit direct policy match with no exclusion.
- 15: strong policy match requiring limited interpretation.
- 10: partial match or competing categories.
- 5: exceptional category requiring discretion.
- 0: conflicts with policy or no applicable rule.

#### Reconciliation: 0 to 20

- 20: fully reconciles with no difference.
- 15: reconciles within approved tolerance.
- 10: partial reconciliation with explainable difference.
- 5: unexplained but immaterial difference.
- 0: material unresolved difference.

#### Cross-source consistency: 0 to 15

- 15: confirmed by two or more authoritative sources.
- 10: one authoritative source with no contradiction.
- 5: sources differ but one clearly supersedes the other.
- 0: unresolved conflict.

### 15.3 Penalties

Apply deductions after the component score:

- Ambiguous entity or period: minus 10.
- New source layout: minus 5.
- New adjustment type: minus 10.
- Potential pro forma overlap: minus 20.
- Material amount above configured threshold: minus 10.
- Conflicting human decisions: minus 25.
- Missing required evidence: cap final score at 59.
- Unreconciled material difference: cap final score at 59.

### 15.4 Formula

```text
Raw score = Evidence + Historical Match + Policy Match + Reconciliation + Cross-Source Consistency
Overall confidence = max(0, min(100, Raw score - Penalties))
```

### 15.5 Decision thresholds

#### 95 to 100: AI applied

- Apply automatically.
- Add to review queue as `AI Applied - Scan Required`.
- Include rationale and evidence.
- Do not auto-release final valuation.

#### 80 to 94: recommended

- Agent proposes the treatment.
- Do not use in final approved output until reviewer accepts, unless the approved MVP policy explicitly permits provisional inclusion.
- Add to review queue.

#### 60 to 79: needs review

- Do not include automatically.
- Ask a focused reviewer question.

#### Below 60: blocked

- Do not include.
- Identify missing evidence or conflict.
- Require human decision.

### 15.6 Confidence calibration

Do not assume the scoring model is accurate at launch. Build a test set from historical decisions.

For each test record:

- AI decision.
- Human-approved decision.
- Score components.
- Final confidence.
- Materiality.
- Error type.

Measure:

- Accuracy of mapping.
- Accuracy of category.
- Accuracy of inclusion decision.
- False auto-approval rate.
- False escalation rate.
- Reconciliation failure rate.

Raise or lower thresholds only after reviewing test results. Material false auto-approvals must be treated as more serious than unnecessary reviews.

---

## 16. Adjustment decision framework

### 16.1 Categories

The agent uses the nine policy categories:

1. Recruitment.
2. XPV related.
3. Financing related.
4. M&A related.
5. Exit related.
6. Non-recurring or one-time compensation.
7. Non-recurring or one-time setup.
8. New business startup.
9. Other.

### 16.2 Required adjustment analysis

Every candidate requires:

- Source description.
- Source amount.
- Month.
- Entity.
- Proposed category.
- Policy evidence.
- Historical examples.
- Recurrence assessment.
- Normal-course assessment.
- Materiality assessment.
- Pro forma overlap assessment.
- Supporting-document assessment.
- Confidence components.
- Automation decision.
- Review status.

### 16.3 Auto-application restrictions

Even with a score of 95 or higher, do not auto-apply if:

- The item is a new type for the company and material.
- The item conflicts with a human decision.
- The item may be included in pro forma EBITDA.
- The item changes the valuation methodology.
- The item depends on a future synergy.
- The item affects cap-table rights.
- The item lacks a source amount.
- The item is a Category 8 item without required approvals.
- The item is recurring but proposed as non-recurring.

### 16.4 Review sampling

Review queue views should include:

- All blocked items.
- All recommended items.
- All material AI-applied items.
- A sample of immaterial AI-applied items.
- All items with a category change versus prior treatment.
- All items with pro forma overlap.

---

## 17. Market-input policy for MVP

### 17.1 Current approach

- Carry forward the prior approved comparable set.
- Carry forward the approved aggregation method.
- Carry forward the approved liquidity discount as a proposed quarter value.
- Require a review item for the set, outliers, current observations, discount, and selected multiple.

### 17.2 Human review record

Capture:

- Included comparables.
- Excluded comparables.
- Outlier status.
- Current values.
- Prior values.
- Discount.
- Average or median selection.
- Final selected multiple.
- Source workbook or support.
- Reviewer decision.

### 17.3 Future PitchBook interface

Create a stable market-input schema now:

```text
CompanyID
QuarterID
ComparableName
ComparableType
Metric
Observation
AsOfDate
SourceProvider
SourceRecordID
Included
Outlier
AdjustedObservation
ReviewerStatus
```

PitchBook integration should populate this interface later without changing the valuation formulas.

---

## 18. Calculation and dependency model

### 18.1 Deterministic calculations

The agent must call deterministic calculation tools or flows for:

- TTM aggregation.
- Quarter aggregation.
- Adjustment aggregation.
- Adjusted EBITDA.
- Pro forma bridge.
- Comparable average or median.
- Liquidity discount.
- Enterprise value.
- Equity value.
- Ownership or waterfall proceeds.
- MOIC.
- IRR.
- Attribution.
- Fund III output contract.

### 18.2 Dependency graph

Example:

```text
Adjustment decision
  -> Included adjustment amount
  -> TTM approved adjustments
  -> TTM adjusted EBITDA
  -> Enterprise value
  -> Equity value
  -> XPV investment value
  -> MOIC and IRR
  -> EBITDA attribution
  -> Total attribution
  -> LP narrative
  -> Fund III output fields
```

### 18.3 Incremental recalculation

When a reviewer changes a record:

1. Locate direct downstream dependencies.
2. Recalculate them in dependency order.
3. Update corresponding SharePoint records.
4. Update workbook cells and formulas.
5. Re-run checks for affected sections.
6. Update narratives referencing changed values.
7. Preserve unaffected extraction and decisions.

### 18.4 Formula evidence

Every material Excel formula should be stored in `ValuationOutputs` with:

- Sheet.
- Cell.
- Formula.
- Dependency IDs.
- Calculated value.
- Reconciliation status.

---

## 19. Conversational interaction design

### 19.1 Supported user intents

The agent should support:

- Start a new company-quarter valuation.
- Show missing source documents.
- Explain how a number was sourced.
- Explain why an adjustment was classified.
- Show AI-applied items.
- Show unresolved items.
- Approve or reject an item.
- Change an adjustment category.
- Change an included amount.
- Change a quarter-specific method or assumption.
- Exclude or include a comparable.
- Change a selected multiple.
- Update an ownership input.
- Recalculate affected outputs.
- Regenerate workbook.
- Compare current and prior valuation.
- Explain attribution.
- Run release checks.

### 19.2 Change-control dialogue

Before applying a material chat-requested change, the agent should show:

- Current value.
- Proposed value.
- Scope.
- Affected outputs.
- Whether evidence supports the change.
- Whether approval is required.

For unambiguous, authorized requests, apply the change and report the impact. For ambiguous scope, ask one focused question.

### 19.3 Example conversations

#### Adjustment change

```text
User: Reject the June ERP adjustment. It is a recurring subscription.
Agent: I found adjustment ADJ-104 for $X in Company A Q2 2027. It is currently AI-applied as Category 7. I will reject it for this quarter, record the reason as recurring subscription, and recalculate adjusted EBITDA, enterprise value, equity value, investment value, MOIC, IRR, and attribution.
```

#### Explain a number

```text
User: Where did quarter-end cash come from?
Agent: The value comes from the June 30 balance sheet, Cash and Cash Equivalents, source cell [location]. It reconciles to the approved monthly summary within tolerance. The workbook uses that source fact in the equity bridge at [sheet/cell].
```

#### Rerun only affected work

```text
User: Use 10.5x instead of 10.2x for this quarter and regenerate.
Agent: I will create a quarter-specific human override for the selected multiple, recalculate valuation and attribution, update the workbook formulas and narratives, and leave source extraction unchanged.
```

### 19.4 Agent response discipline

The agent must not:

- Claim final approval.
- Hide uncertainty.
- Fabricate missing values.
- Treat historical use as automatic approval.
- Present invitees, files, or records inaccessible to the user.
- Apply a company decision to all companies without explicit scope.

---

## 20. Company Valuation Agent specification

### 20.1 Name

`Company Valuation Agent`

### 20.2 Description

Analyzes portfolio-company financial statements, inherits approved company valuation methodology, applies XPV policies, produces traceable company valuation workbooks, and supports conversational review and targeted recalculation.

### 20.3 Core instructions

The agent must:

1. Determine company and quarter context.
2. Retrieve the effective generic, company, quarter, and human rules.
3. Identify required outputs before extracting data.
4. Use prior approved workbooks when establishing company methodology.
5. Extract only required facts plus evidence needed for adjustments and validation.
6. Preserve source locations.
7. Apply the confidence framework.
8. Auto-apply only eligible high-confidence decisions.
9. Add all AI-applied decisions to the review queue.
10. Use deterministic flows for calculations.
11. Write traceable formulas to Excel.
12. Support targeted conversational changes.
13. Recalculate only affected outputs.
14. Record every change and decision.
15. Never release a final valuation while critical checks are open.

### 20.4 Agent knowledge

Add as knowledge sources:

- Generic policy library.
- Adjustment policy.
- Valuation methodology specification.
- Data dictionary.
- Workbook output specification.
- Company-specific prior valuations and LP reports during onboarding.

Do not rely on SharePoint knowledge retrieval alone for structured system state. Use tools to query SharePoint Lists.

### 20.5 Agent tools

Create these tools or flows:

1. `Get Company Context`
2. `Create Company Quarter`
3. `Get Effective Rules`
4. `Find Source Documents`
5. `Register Source Document`
6. `Extract Financial Facts`
7. `Analyze Prior Valuation`
8. `Score Confidence`
9. `Create Adjustment Candidate`
10. `Create or Update Decision`
11. `Create Review Item`
12. `Calculate Valuation`
13. `Get Dependency Impact`
14. `Recalculate Affected Outputs`
15. `Create or Update Workbook`
16. `Run Release Checks`
17. `Get Lineage Explanation`
18. `Publish Working Workbook`
19. `Release Approved Workbook`

### 20.6 Tool contract rules

Each tool should:

- Accept a correlation ID.
- Return success or failure.
- Return record IDs created or changed.
- Return warnings.
- Return next required action.
- Be idempotent where practical.
- Avoid creating duplicate records when rerun.

---

## 21. Agent-flow design

### 21.1 Flow A: Start or resume valuation

Trigger:

- Agent request.
- SharePoint file-created event.
- Manual operator action.

Actions:

1. Resolve company and quarter.
2. Find or create `CompanyQuarterID`.
3. Load prior-quarter reference.
4. Load active company profile.
5. Check required source types.
6. Return missing-input list or start processing.

### 21.2 Flow B: Process source document

1. Register the document.
2. Classify document type.
3. Extract metadata.
4. Determine required fields.
5. Extract candidate facts.
6. Map to canonical fields.
7. Calculate confidence.
8. Create facts and mapping decisions.
9. Reconcile.
10. Add exceptions to review queue.

### 21.3 Flow C: Analyze prior valuation

1. Identify output sheets.
2. Extract key formulas and named inputs.
3. Identify methods and periods.
4. Identify adjustment structure.
5. Identify market-input logic.
6. Identify equity bridge, ownership, waterfall, returns, and attribution.
7. Compare with generic policy.
8. Propose company profile records.
9. Score confidence.
10. Create review items.

### 21.4 Flow D: Build valuation draft

1. Retrieve approved and provisionally eligible facts.
2. Resolve effective rules.
3. Aggregate periods.
4. Resolve included adjustments.
5. Calculate valuation inputs and outputs.
6. Create dependencies.
7. Create workbook copy.
8. Populate source and decision sheets.
9. Write formulas.
10. Run workbook checks.
11. Create review summary.

### 21.5 Flow E: Apply conversational change

1. Parse requested target, change, scope, and reason.
2. Retrieve current record and dependencies.
3. Validate authorization.
4. Create decision or override.
5. Recalculate downstream outputs.
6. Update workbook.
7. Run affected checks.
8. Write audit event.
9. Return impact summary.

### 21.6 Flow F: Release company valuation

1. Confirm all critical review items are closed.
2. Confirm required human approvals.
3. Confirm workbook checks pass.
4. Confirm output contract is complete.
5. Freeze profile and policy versions used.
6. Copy working workbook to approved library.
7. Generate PDF if required.
8. Mark CompanyQuarter as approved.
9. Expose approved outputs to Fund III aggregation.

---

## 22. Review queue design

### 22.1 Views

Create views:

- My open items.
- Critical blockers.
- AI applied, scan required.
- Recommended decisions.
- Low-confidence items.
- Pro forma overlap.
- Market-input review.
- Cap-table review.
- Resolved this quarter.

### 22.2 Human actions

Reviewers can:

- Approve.
- Reject.
- Modify.
- Request support.
- Change scope.
- Mark immaterial.
- Promote a quarter decision to company profile.
- Escalate.

### 22.3 Promotion rule

A reviewer may promote a recurring human decision:

```text
DecisionOnly -> Quarter -> Company
```

Promotion creates a new profile record and does not rewrite historical decisions.

---

## 23. Audit and control framework

### 23.1 Audit questions the platform must answer

For any material output:

- What is the number?
- Where did it come from?
- Which source document, sheet/page, and cell/range?
- Was it extracted or calculated?
- What transformation was applied?
- Which rules applied?
- Which historical examples supported it?
- What was the confidence score and why?
- Was it AI applied or human decided?
- Who changed it?
- What changed afterward?
- Which workbook cell contains it?
- Which downstream outputs depend on it?

### 23.2 Required control checks

- Company and quarter resolved.
- Required sources present.
- TTM months complete.
- No duplicate month/entity/scenario facts.
- Revenue and EBITDA reconciled where possible.
- Cash and debt tied to quarter-end balance sheet.
- Adjustments tied to sources.
- No unresolved pro forma overlap.
- Adjusted metric formula correct.
- Comparable calculations correct.
- Enterprise value formula correct.
- Equity bridge correct.
- Waterfall totals equal equity value.
- XPV value matches waterfall.
- MOIC and IRR formulas correct.
- Attribution matches value change.
- Fund III output contract complete.
- Workbook formulas agree with structured outputs.
- Critical reviews closed.
- Required approvals present.

### 23.3 Override controls

Manual overrides must have:

- Original value.
- Override value.
- Reason.
- Scope.
- Effective period.
- User.
- Timestamp.
- Affected outputs.

---

## 24. Security and governance

### 24.1 Data access

- Agent responses and tools must respect SharePoint permissions.
- Separate source-library access from approved-output access where necessary.
- Avoid broad sharing links.
- Use security groups rather than individuals where possible.

### 24.2 Production ownership

- Use team-owned connections or organization-approved connection references.
- Avoid personal connections for production flows.
- Record backup owners.
- Export the solution after material changes.

### 24.3 Environment strategy

Minimum:

- Development environment.
- Production environment.

Preferred later:

- Development.
- Test.
- Production.

### 24.4 Sensitive content

- Apply appropriate sensitivity labels.
- Restrict cap-table and investor data.
- Do not expose source documents to users without permission.
- Log access and decision events.

---

## 25. Testing and evaluation

### 25.1 Historical replay test

Select one approved historical company-quarter.

Provide only the source documents that would have been available before the valuation.

Test whether the system reproduces:

- Required facts.
- Approved adjustments.
- Adjusted metric.
- Selected method.
- Enterprise value.
- Equity value.
- XPV investment value.
- MOIC.
- IRR.
- Attribution.
- LP output fields.

### 25.2 New-quarter test

Use the next available monthly statements.

Evaluate:

- New layout handling.
- New labels.
- Missing adjustment schedule handling.
- Review queue quality.
- Incremental recalculation.
- Workbook traceability.

### 25.3 Conversational-change tests

Test at least:

- Reject adjustment.
- Change category.
- Modify included amount.
- Exclude comparable.
- Change selected multiple.
- Change quarter-specific cash or debt source.
- Ask for source explanation.
- Regenerate workbook.

### 25.4 Release criteria

Do not move beyond pilot until:

- Formula outputs reconcile.
- High-confidence false auto-approvals are acceptably controlled.
- Source lineage is complete.
- User permissions work correctly.
- Chat changes are auditable.
- Duplicate reruns do not create duplicate records.
- Approved workbooks remain immutable.

---

## 26. Build plan

### Phase 1: Foundation

Deliverables:

- SharePoint site.
- Libraries.
- Core Lists.
- Generic policy documents.
- Company workbook template.
- One pilot company record.

Exit condition:

- Documents and records can be stored with stable IDs and permissions.

### Phase 2: Company onboarding

Deliverables:

- Prior-valuation analysis flow.
- Company methodology profile.
- Historical replay test set.

Exit condition:

- Agent can propose a company profile from historical workbooks and packages.

### Phase 3: Current-quarter extraction

Deliverables:

- Source-processing flow.
- Financial-fact extraction.
- AI mapping.
- Confidence scoring.
- Reconciliation.
- Adjustment candidates.

Exit condition:

- New monthly statements create usable structured facts and review items.

### Phase 4: Calculation and workbook

Deliverables:

- Calculation flow.
- Dependency records.
- Workbook template population.
- Excel formulas.
- Checks.

Exit condition:

- Draft company valuation workbook is generated and reconciles to structured outputs.

### Phase 5: Conversation and delta changes

Deliverables:

- Change-intent handling.
- Decision updates.
- Dependency-driven recalculation.
- Workbook patching.
- Impact summaries.

Exit condition:

- Human can request a targeted change without rerunning intake and extraction.

### Phase 6: Approval and release

Deliverables:

- Review views.
- Release check.
- Approval flow.
- Approved workbook and PDF archive.
- Fund III output contract records.

Exit condition:

- One pilot company-quarter is approved and available for downstream aggregation.

### Phase 7: Fund III aggregation

Deliverables:

- Fund III Agent.
- Company-record retrieval.
- Fund workbook formulas.
- Fund reconciliations.
- Fund approval and release.

Exit condition:

- Fund III package is produced from approved company valuation records.

---

# Part II: Accompanying build instructions

## 27. Before opening Copilot Studio

Complete these preparation steps first.

### Step 1: Confirm access

Ask the Microsoft 365 or Power Platform administrator to confirm:

- Access to Copilot Studio.
- Permission to create an agent and agent flows.
- A development Power Platform environment.
- Permission to use SharePoint connectors.
- Permission to use Excel Online and Office Scripts if needed.
- Available Copilot Studio capacity or billing arrangement.
- Permission to create a solution.
- Permission to publish only to a limited pilot audience.

Do not assume the Microsoft 365 Copilot user license alone covers every production agent-flow action or premium connector. Confirm tenant licensing and capacity with the administrator before production deployment.

### Step 2: Choose the pilot

Use one company with:

- A complete approved historical valuation workbook.
- Monthly financial statements for that historical period.
- A prior LP valuation report.
- A manageable cap table.
- A known reviewer.

Use one historical quarter for replay and one newer quarter for forward testing.

### Step 3: Collect source files

Create an intake checklist:

- Prior approved valuation workbook.
- Prior company LP report.
- Twelve monthly financial statements required by the methodology.
- Quarter-end balance sheet.
- Adjustment support.
- Pro forma support if applicable.
- Cap table.
- Comparable support.
- Generic adjustment policy.

---

## 28. Create the SharePoint MVP

### Step 1: Create the site

Create a private team site named:

```text
AI Valuation Platform
```

Assign at least two owners.

### Step 2: Create libraries

Create:

- `01 Policies and Templates`
- `02 Company Sources`
- `03 Working Valuations`
- `04 Approved Company Valuations`
- `05 Fund III Packages`
- `06 Audit Exports`

Enable version history.

### Step 3: Create the pilot folders

Under `02 Company Sources`:

```text
[PILOT_COMPANY_ID]/
  Prior Valuations/
  Prior LP Reports/
  Monthly Financials/
    [HISTORICAL_QUARTER]/
    [NEW_QUARTER]/
  Adjustment Support/
  Cap Table/
  Market Inputs/
  Other Evidence/
```

### Step 4: Add metadata

Add the required columns from Section 9.3.

Begin with simple choice columns. Avoid complex automation until the structure is validated.

### Step 5: Upload authoritative documents

Upload the adjustment policy, valuation template, and data dictionary to `01 Policies and Templates`.

Upload pilot source documents to the company folders. Mark authoritative versions.

---

## 29. Create the SharePoint Lists

Create the Lists in this order:

1. `Companies`
2. `CompanyQuarters`
3. `PolicyRules`
4. `CompanyMethodologyProfiles`
5. `SourceDocuments`
6. `ExtractedFacts`
7. `AdjustmentCandidates`
8. `Decisions`
9. `ConfidenceComponents`
10. `ValuationInputs`
11. `ValuationOutputs`
12. `ReviewQueue`
13. `CalculationDependencies`
14. `AuditEvents`

For the first build, create all required columns but populate only the pilot records.

### Initial records

Create:

- One company.
- One historical replay quarter.
- One current quarter.
- Generic policy records for the nine adjustment categories.
- Generic formula and governance rules.

Use stable IDs such as:

```text
COMP-PILOT
COMP-PILOT-2026-Q2
COMP-PILOT-2027-Q2
POL-ADJ-01
```

---

## 30. Create a Power Platform solution

In the development environment:

1. Create a solution named `AI Valuation Platform MVP`.
2. Use an organization-owned publisher prefix.
3. Add the Copilot Studio agent to the solution.
4. Add agent flows and Power Automate flows to the solution.
5. Add connection references.
6. Add environment variables for SharePoint site URL, library names, list names, template URL, and confidence thresholds.

Recommended environment variables:

```text
ValuationSharePointSite
PoliciesLibrary
CompanySourcesLibrary
WorkingValuationsLibrary
ApprovedValuationsLibrary
CompanyWorkbookTemplateURL
AutoApplyThreshold = 95
RecommendThreshold = 80
ReviewThreshold = 60
ConfidenceModelVersion = 1.0
```

---

## 31. Create the Company Valuation Agent

### Step 1: Create a blank agent

In Copilot Studio:

1. Select **Agents**.
2. Create a blank agent.
3. Name it `Company Valuation Agent - DEV`.
4. Add the description from Section 20.2.
5. Configure authentication for internal organizational users.

### Step 2: Add instructions

Use Section 20.3 as the initial instruction set.

Add explicit prohibitions:

- Never invent a missing financial value.
- Never claim a valuation is approved unless the approved record exists.
- Never apply a decision outside its scope.
- Never silently change a company methodology.
- Never hide a reconciliation difference.
- Never replace an authoritative source with an unsupported inference.

### Step 3: Add knowledge

Add:

- Adjustment policy.
- Generic valuation methodology.
- Data dictionary.
- Workbook output specification.
- Pilot historical valuation workbook.
- Pilot historical LP report.

Use SharePoint folders rather than individual files where the approved content set is expected to grow.

### Step 4: Configure conversation starters

Add:

- `Start a valuation for a company and quarter`
- `Show the open review items`
- `Explain where a valuation number came from`
- `Change an adjustment and recalculate`
- `Generate or refresh the company valuation workbook`

---

## 32. Build the first four agent tools

Do not build the entire platform at once. Start with four tools.

### Tool 1: Get Company Context

Inputs:

- Company name or ID.
- Quarter.

Actions:

- Find company.
- Find or create company-quarter.
- Retrieve prior quarter.
- Retrieve active profile version.
- Retrieve status.

Returns:

- Company ID.
- CompanyQuarter ID.
- Valuation date.
- Status.
- Prior quarter ID.
- Profile version.
- Missing context.

### Tool 2: Get Effective Rules

Inputs:

- Company ID.
- CompanyQuarter ID.
- Rule area.

Actions:

- Retrieve active generic rules.
- Retrieve approved company overrides.
- Retrieve approved quarter and human decisions.
- Resolve effective rules.

Returns:

- Effective rules.
- Source layer.
- Conflicts.
- Required review.

### Tool 3: Find and Register Sources

Inputs:

- Company ID.
- CompanyQuarter ID.

Actions:

- Search company source folder.
- Classify files.
- Create or update SourceDocuments records.
- Identify missing required source types.

Returns:

- Source IDs.
- Classified document list.
- Missing-document list.
- Warnings.

### Tool 4: Create Review Item

Inputs:

- CompanyQuarter ID.
- Area.
- Target record.
- Summary.
- Severity.
- Confidence.
- Recommendation.

Actions:

- Create deduplicated ReviewQueue record.
- Assign appropriate reviewer group.

Returns:

- Review item ID.
- Status.

### First milestone

Test this chat:

```text
Start a valuation for [pilot company] for [historical quarter]. Tell me which sources are present, which are missing, and which effective methodology rules will apply.
```

Do not proceed until the result is correct and repeatable.

---

## 33. Build historical methodology onboarding

### Step 1: Create `Analyze Prior Valuation` flow

Inputs:

- Company ID.
- Prior valuation SourceDocument ID.
- Prior LP report SourceDocument ID.

Required outputs:

- Proposed methodology profile records.
- Source locations.
- Confidence components.
- Conflicts with generic rules.
- Review items.

### Step 2: Limit the first profile

For the first iteration, extract only:

- Valuation method.
- Earnings metric.
- Earnings period.
- Liquidity discount.
- Comparable set.
- Comparable aggregation method.
- Equity bridge components.
- Ownership or waterfall approach.
- Attribution drivers.
- Required output fields.

Do not attempt to understand every workbook formula yet.

### Step 3: Review profile

Have the reviewer approve or correct the proposed profile.

Version it as `1.0`.

### Second milestone

Ask:

```text
Explain the pilot company's approved valuation methodology and cite the historical workbook locations that support each element.
```

The agent must distinguish approved profile records from unapproved proposals.

---

## 34. Build current-source extraction

### Step 1: Create required-field plan

The agent retrieves the approved profile and identifies the minimum required fields.

### Step 2: Create extraction flow

For each source:

- Extract candidate facts.
- Preserve source location.
- Propose canonical mapping.
- Calculate confidence components.
- Create fact records.
- Run available reconciliations.
- Create review items.

### Step 3: Begin with a small canonical field set

Start with:

- Revenue.
- Reported EBITDA.
- Cash.
- Debt.
- Approved adjustment amount.
- Adjusted EBITDA.
- Ownership.

Expand only when the pilot workbook requires more fields.

### Step 4: Add adjustment handling

Implement:

- Policy match.
- Historical-company match.
- Recurrence assessment.
- Pro forma overlap.
- Confidence scoring.
- AI application threshold.
- Review queue creation.

### Third milestone

Upload one new monthly statement and ask:

```text
Process the new source for the pilot company. Show the extracted facts, mapped fields, reconciliation status, confidence components, and adjustment candidates.
```

---

## 35. Build deterministic calculations

### Step 1: Encode calculation specifications

Create structured rules for:

- Period aggregation.
- Adjusted EBITDA.
- Market multiple.
- Enterprise value.
- Equity bridge.
- XPV value.
- MOIC.
- IRR.
- Attribution.

### Step 2: Create calculation flow

The flow should:

- Retrieve effective inputs.
- Calculate outputs.
- Create ValuationInputs and ValuationOutputs.
- Create dependency records.
- Reconcile against prior or expected values.

### Step 3: Build formulas in Excel

Use an Office Script to:

- Populate input tables.
- Populate source and decision tables.
- Write formulas into calculation cells.
- Link output sheets to calculation cells.
- Add checks.
- Write decision IDs and source IDs beside inputs.

### Fourth milestone

The historical replay workbook should reproduce the approved quarter within tolerance and expose formulas for the material outputs.

---

## 36. Build conversational changes

### Step 1: Create `Apply Change` tool

Inputs:

- CompanyQuarter ID.
- Target type and ID.
- New value or decision.
- Scope.
- Reason.

Actions:

- Retrieve current state.
- Create human decision.
- Find dependencies.
- Recalculate affected outputs.
- Patch workbook.
- Write audit event.

### Step 2: Test changes

Test:

```text
Reject adjustment [ID] because it is recurring.
```

```text
Use [multiple] for this quarter only.
```

```text
Exclude [comparable] and show the valuation impact.
```

```text
Restore the previous adjustment decision.
```

### Fifth milestone

The agent applies the change without re-extracting unchanged sources and provides before-and-after values.

---

## 37. Build release controls

Create `Run Release Checks`.

Block release if:

- Critical review items remain open.
- Required sources are missing.
- Material facts are unreconciled.
- Adjustments lack required evidence.
- Market inputs are not reviewed.
- Ownership changes are not approved.
- Workbook formulas disagree with structured outputs.
- Fund III contract fields are incomplete.

Create `Release Approved Workbook` only after final approval.

---

## 38. Build the Fund III handoff

Do not build the full Fund III Agent until one company valuation is stable.

First create a SharePoint view or export containing only approved `ValuationOutputs` required by the fund contract.

Validate that the fund-level workbook could retrieve:

- Invested capital.
- Prior valuation.
- New investment.
- Performance change.
- Current valuation.
- Proceeds.
- MOIC.
- Gross IRR.
- DPI.
- Ownership.
- Projection values if applicable.

Then design the Fund III Agent around that approved interface.

---

## 39. Suggested first-week build sequence

### Build session 1

- Create SharePoint site and libraries.
- Create Companies, CompanyQuarters, SourceDocuments, ReviewQueue, and AuditEvents Lists.
- Upload pilot files.

### Build session 2

- Create Power Platform solution.
- Create blank Company Valuation Agent.
- Add instructions and knowledge.
- Build Get Company Context.

### Build session 3

- Build Find and Register Sources.
- Build Get Effective Rules.
- Populate initial generic rules.

### Build session 4

- Build Analyze Prior Valuation for a narrow methodology profile.
- Review and approve profile version 1.0.

### Build session 5

- Build extraction for seven core fields.
- Add confidence components.
- Create review items.

Do not build workbook generation until the structured facts and decisions are correct.

---

## 40. Open items that do not block starting

These questions can be resolved during the pilot:

1. Which exact role provides final company-valuation approval?
2. What materiality thresholds should affect confidence and review severity?
3. Which company-quarter should be the historical replay test?
4. Whether recommended items at 80 to 94 may be provisionally included in a draft workbook.
5. Whether profiles require one or two historical quarters before approval.
6. Which IRR cash-flow sources are authoritative.
7. Which balance-sheet items are treated as debt-like by default.
8. How to handle restated monthly financials after a quarter is approved.
9. Whether every AI-applied item must be individually acknowledged or may be batch approved.
10. Which approved company output fields are mandatory for Fund III projections.

The MVP can begin now using conservative defaults:

- Final approval remains human.
- Materiality increases review requirements.
- Recommended items are visible in draft but not final until accepted.
- Restatements create a reopened quarter and preserve the prior approved version.

---

## 41. Definition of done for the first MVP

The MVP is done when:

- One historical valuation is reproduced.
- One new-quarter draft is generated.
- The company methodology profile is stored and versioned.
- AI creates source-grounded facts automatically.
- High-confidence eligible decisions are applied and queued for scanning.
- Lower-confidence items are properly escalated.
- Excel contains traceable formulas.
- Source and decision lineage is complete.
- A user can request a targeted change by chat.
- Only affected records and workbook sections recalculate.
- A final approved company workbook can be released.
- The approved company output contract can feed Fund III.

---

## 42. Immediate next action

Start with the SharePoint foundation and the narrowest possible pilot.

The first working target is not “automate the entire valuation.” It is:

> Given one pilot company and one historical quarter, the agent identifies the approved methodology, registers the correct source documents, explains the effective rules, and produces a reviewable company profile with citations to the historical workbook.

Once that works, add extraction, then calculations, then workbook generation, then conversational changes, and finally Fund III aggregation.

---

## Appendix A: Initial agent instruction block

```text
You are the Company Valuation Agent for XPV's AI Valuation Platform.

Your purpose is to analyze portfolio-company source documents, retrieve approved company methodology, apply XPV policy, create traceable valuation records, and produce or update company valuation workbooks.

Use this precedence order:
1. Explicit in-scope human decisions.
2. Approved quarter-specific rules.
3. Approved company methodology and historical decisions.
4. Active generic XPV policy.

Before extraction, identify the company, quarter, approved profile version, required LP outputs, and required valuation inputs.

Treat source facts, calculations, decisions, and outputs as different record types.

Never invent missing values. Never treat a historical formula as correct only because it existed. Never silently change methodology. Never apply a decision outside its scope. Never claim final approval without an approved release record.

For AI decisions, calculate confidence from evidence quality, historical company match, policy match, reconciliation, cross-source consistency, and defined penalties. Do not rely on self-reported model confidence.

AI-applied items must remain visible in the review queue. Material conflicts, missing evidence, pro forma overlap, methodology changes, market-input changes, and cap-table changes require human review.

Use deterministic tools for calculations. Ensure the Excel workbook contains formulas and cell references that reproduce material calculations. Preserve source location, rule IDs, decision IDs, confidence components, and audit events.

When a user asks for a change, update the smallest applicable scope, identify dependent outputs, recalculate only those outputs, patch the workbook, and report the before-and-after impact.
```

## Appendix B: Initial confidence examples

### Example 1: Exact approved mapping

```text
Evidence quality: 25
Historical company match: 20
Policy match: 20
Reconciliation: 20
Cross-source consistency: 15
Penalties: 0
Overall confidence: 100
Decision: AI applied, scan required
```

### Example 2: New ERP consulting expense

```text
Evidence quality: 25
Historical company match: 10
Policy match: 20
Reconciliation: 20
Cross-source consistency: 10
New adjustment type penalty: -10
Overall confidence: 75
Decision: Needs review
```

### Example 3: Adjustment may already be in pro forma EBITDA

```text
Evidence quality: 25
Historical company match: 15
Policy match: 20
Reconciliation: 15
Cross-source consistency: 10
Pro forma overlap penalty: -20
Overall confidence: 65
Decision: Needs review and overlap resolution
```

### Example 4: Missing support

```text
Raw score: 82
Missing required evidence: score capped at 59
Decision: Blocked pending support
```

## Appendix C: Initial workbook checks

```text
CHECK-001 Required source documents present
CHECK-002 TTM period contains required months
CHECK-003 No month duplicated
CHECK-004 Cash reconciles to quarter-end balance sheet
CHECK-005 Debt reconciles to quarter-end balance sheet
CHECK-006 Adjustment detail equals adjustment total
CHECK-007 No unresolved pro forma overlap
CHECK-008 Adjusted metric equals reported metric plus included adjustments and approved pro forma items
CHECK-009 Selected multiple agrees with reviewed market-input calculation
CHECK-010 Enterprise value formula agrees with approved methodology
CHECK-011 Equity bridge totals correctly
CHECK-012 Waterfall totals to equity value
CHECK-013 XPV investment value agrees with waterfall
CHECK-014 MOIC formula agrees with cost and value
CHECK-015 IRR formula uses approved cash-flow dates and values
CHECK-016 Attribution totals to change in investment value
CHECK-017 ValuationOutputs agree with workbook cells
CHECK-018 Fund III output contract complete
CHECK-019 Critical review queue empty
CHECK-020 Final approval recorded
```

## Appendix D: Build artifact checklist

```text
[ ] SharePoint site created
[ ] Libraries created
[ ] Metadata added
[ ] Companies List created
[ ] CompanyQuarters List created
[ ] PolicyRules List created
[ ] CompanyMethodologyProfiles List created
[ ] SourceDocuments List created
[ ] ExtractedFacts List created
[ ] AdjustmentCandidates List created
[ ] Decisions List created
[ ] ConfidenceComponents List created
[ ] ValuationInputs List created
[ ] ValuationOutputs List created
[ ] ReviewQueue List created
[ ] CalculationDependencies List created
[ ] AuditEvents List created
[ ] Power Platform solution created
[ ] Environment variables created
[ ] Company Valuation Agent created
[ ] Agent instructions added
[ ] Knowledge sources added
[ ] Get Company Context tool built
[ ] Get Effective Rules tool built
[ ] Find and Register Sources tool built
[ ] Create Review Item tool built
[ ] Historical methodology flow built
[ ] Source extraction flow built
[ ] Confidence flow built
[ ] Adjustment flow built
[ ] Calculation flow built
[ ] Workbook generation script built
[ ] Conversational change flow built
[ ] Release check built
[ ] Historical replay test passed
[ ] New-quarter test passed
[ ] Company output contract validated
```
