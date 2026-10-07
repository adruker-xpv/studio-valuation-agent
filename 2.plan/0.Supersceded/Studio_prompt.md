Create an agent flow named:

Start or Resume Company Valuation

Purpose:

This flow supports a conversational Company Valuation Agent. It must start or resume a portfolio-company quarterly valuation using SharePoint as the MVP system of record.

The flow must not calculate or approve a final valuation yet. Its first purpose is to establish the company-quarter context, register relevant files, resolve the effective methodology hierarchy, identify missing information, and create review items.

Trigger:

The flow is called by an agent.

Inputs from the calling agent:

1. CompanyNameOrID, text, required
2. QuarterID, text, required, formatted as YYYY_Q#
3. RequestedBy, text, required
4. CorrelationID, text, required
5. RequestType, text, required, with possible values:
   - Start
   - Resume
   - Status
6. ReanalyzeHistoricalMethodology, yes/no, default No

Use the following SharePoint connections:

1. SharePoint site:
   AI Valuation Platform

2. SharePoint Lists:
   - Companies
   - CompanyQuarters
   - CompanyMethodologyProfiles
   - PolicyRules
   - SourceDocuments
   - Decisions
   - ReviewQueue
   - AuditEvents

3. SharePoint document library:
   02 Company Sources

Required logic:

Step 1: Resolve the company

Search the Companies list for an active company where either CompanyID or CompanyName matches CompanyNameOrID.

If exactly one company is found:
- Store CompanyID
- Store CompanyName
- Store CurrentMethodologyProfileVersion
- Store CompanySourcesFolder
- Store ReviewerGroup

If no company is found:
- Return status CompanyNotFound
- Do not create a CompanyQuarters record
- Return a message explaining that the company must first be added to the Companies list

If multiple companies are found:
- Return status CompanyAmbiguous
- Return the matching company names and IDs
- Do not continue until the calling agent provides a specific CompanyID

Step 2: Resolve the company-quarter

Construct CompanyQuarterID as:

CompanyID + "-" + QuarterID

Search CompanyQuarters for this CompanyQuarterID.

If it exists:
- Retrieve its status
- Retrieve its valuation date
- Retrieve its prior company-quarter ID
- Retrieve its working workbook URL
- Retrieve its current profile version
- Treat the request as Resume unless RequestType is Status

If it does not exist and RequestType is Start:
- Create the CompanyQuarters record
- Set status to Sources Pending
- Set StartedAt to the current timestamp
- Set current profile version from the Companies record
- Generate a unique RunID
- Record RequestedBy and CorrelationID where supported

If it does not exist and RequestType is Resume or Status:
- Return status CompanyQuarterNotFound
- Do not create the record

Make this step idempotent. Repeated calls with the same CompanyQuarterID must not create duplicate records.

Step 3: Determine the prior quarter

If the CompanyQuarters record does not already contain PriorCompanyQuarterID:
- Determine the immediately preceding calendar quarter
- Search CompanyQuarters for the same CompanyID and that prior QuarterID
- If found, update PriorCompanyQuarterID
- If not found, continue and add a warning named PriorQuarterNotFound

Do not invent a prior valuation or prior-quarter values.

Step 4: Retrieve active generic policy rules

Retrieve PolicyRules where:
- Status is Active
- EffectiveFrom is on or before the valuation date
- EffectiveTo is blank or on or after the valuation date

Return at least:
- RuleID
- RuleType
- Category
- RuleName
- RuleText
- AutoApplyEligible
- RequiredEvidence
- Version

Step 5: Retrieve active company methodology

Retrieve CompanyMethodologyProfiles where:
- CompanyID matches
- Status is Approved
- EffectiveFrom is on or before the valuation date
- EffectiveTo is blank or on or after the valuation date

Return at least:
- ProfileRecordID
- AttributeName
- AttributeValue
- ProfileVersion
- SourceDocumentURL
- SourceSheet
- SourceCellOrRange
- ConfidenceScore

If no approved methodology profile exists:
- Add a warning named CompanyMethodologyMissing
- Mark HistoricalMethodologyAnalysisRequired as Yes
- Do not silently infer or approve a company methodology in this flow

If ReanalyzeHistoricalMethodology is Yes:
- Mark HistoricalMethodologyAnalysisRequired as Yes even if an approved profile exists

Step 6: Retrieve applicable quarter and human decisions

Retrieve Decisions where:
- CompanyQuarterID matches
- Status is Approved or Active
- Scope is Quarter or DecisionOnly

Also retrieve active Company-scope decisions for the same CompanyID.

Resolve the methodology hierarchy in this order:

1. Explicit active human decision
2. Approved quarter-specific decision
3. Approved company methodology profile
4. Active generic policy

For every resolved rule or attribute, return:
- EffectiveValue
- EffectiveSourceLayer
- SourceRecordID
- SourceEvidence
- Whether a conflict exists

If two active records at the same scope conflict:
- Do not choose between them
- Mark the item as Conflict
- Create a critical review item

Step 7: Find and classify source documents

Search the company's folder in the 02 Company Sources library.

Find files associated with:
- The requested QuarterID
- Prior Valuations
- Prior LP Reports
- Monthly Financials
- Balance Sheets
- Adjustment Support
- Pro Forma Support
- Cap Table
- Market Inputs

Classify files into these document types:
- Monthly Financials
- Balance Sheet
- Prior Valuation
- Prior LP Report
- Adjustment Support
- Pro Forma Support
- Cap Table
- Market Inputs
- Other or Unknown

For every discovered file:
- Generate a stable SourceDocumentID if one does not exist
- Create or update its SourceDocuments record
- Preserve file name
- Preserve full SharePoint file URL
- Preserve company
- Preserve quarter
- Preserve period end when available
- Preserve document type
- Preserve SharePoint version or modified date when available
- Set ingestion status to Registered
- Do not duplicate an existing record for the same file version

Do not modify, rename, move, or overwrite the source file.

Step 8: Determine required source types

Use the effective company methodology to identify the minimum required source types.

At minimum, check for:
- Current monthly financial statements required for the valuation period
- Quarter-end balance sheet
- Prior approved valuation workbook
- Prior company LP report, if required for output inheritance
- Adjustment support when adjustments are included
- Pro forma support when pro forma treatment is active
- Cap table or ownership support
- Market-input support

Return:
- PresentSourceTypes
- MissingRequiredSourceTypes
- OptionalMissingSourceTypes

Do not create fake records for missing sources.

Step 9: Create review items

Create deduplicated ReviewQueue items for:

- Missing approved company methodology
- Conflicting rules at the same scope
- Missing required source type
- Unknown document type
- Missing prior quarter
- Historical methodology requiring reanalysis
- Missing or stale market-input support
- Any other condition that prevents reliable processing

Each review item must include:
- Unique ReviewItemID
- CompanyQuarterID
- Area
- TargetRecordType
- TargetRecordID when available
- Summary
- Severity
- ReviewReason
- AIRecommendation
- Status set to Open
- AssignedTo using the company's ReviewerGroup when available
- CreatedAt timestamp
- ConfidenceScore when applicable

Do not create a duplicate open review item for the same company-quarter, reason, and target.

Step 10: Update company-quarter status

Use these rules:

- If critical required sources are missing, status remains Sources Pending
- If sources are present but approved methodology is missing, set status to Extraction Review
- If required sources and methodology are present, set status to Sources Received
- If RequestType is Status, do not change the existing status

Step 11: Write an audit event

Create one AuditEvents record containing:
- Unique AuditEventID
- CompanyQuarterID
- EventType:
  - ValuationStarted
  - ValuationResumed
  - ValuationStatusChecked
- ActorType set to HumanThroughAgent
- Actor set to RequestedBy
- TargetRecordType set to CompanyQuarter
- TargetRecordID set to CompanyQuarterID
- Reason set to the original RequestType
- SourceRunID set to RunID
- Timestamp
- CorrelationID

Step 12: Return a structured response to the calling agent

Return these outputs:

1. Success, yes/no
2. FlowStatus
3. CompanyID
4. CompanyName
5. CompanyQuarterID
6. QuarterID
7. ValuationDate
8. CurrentStatus
9. PriorCompanyQuarterID
10. RunID
11. ProfileVersion
12. HistoricalMethodologyAnalysisRequired, yes/no
13. EffectiveRules, as structured JSON
14. RegisteredSources, as structured JSON
15. PresentSourceTypes
16. MissingRequiredSourceTypes
17. OptionalMissingSourceTypes
18. ReviewItemsCreated, as structured JSON
19. Warnings, as structured JSON
20. RecommendedNextAction
21. HumanReadableSummary

The HumanReadableSummary should tell the user:

- Whether this is a new or resumed valuation
- Which methodology profile is active
- Which effective rule layer is being used
- Which source documents were found
- Which required sources are missing
- Which conflicts or review items exist
- What should happen next

Error handling:

- Return a clear failure status instead of silently stopping
- Record an audit event for material failures when the company-quarter is known
- Do not create duplicate SharePoint records if the flow is retried
- Do not continue to extraction or workbook generation when company identity is unresolved
- Do not infer a missing financial value
- Do not automatically approve a methodology conflict
- Preserve all source and decision references

Security:

- Use the calling user's authorized SharePoint access
- Do not return files or list records the calling user cannot access
- Do not expose cap-table or valuation records outside existing SharePoint permissions

After generating the flow:

1. Show me the proposed trigger, connections, actions, conditions, loops, and outputs.
2. Identify any SharePoint columns or connections that do not yet exist.
3. Do not publish the flow automatically.
4. Wait for me to review the generated plan before finalizing it.