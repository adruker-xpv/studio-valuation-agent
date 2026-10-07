I am building an AI-native valuation platform for a private equity fund.

The primary output is a company-specific quarterly valuation workbook.

The secondary output is a Fund III LP valuation package that aggregates approved company valuations.

Use SharePoint as the MVP system of record.

The platform should use the following hierarchy:

Generic XPV valuation policies
    ↓
Company-specific methodology inferred from approved historical valuation workbooks and LP reports
    ↓
Quarter-specific facts and decisions
    ↓
Human overrides

Human overrides always win.

The platform should:

1. Ingest monthly company financial statements and balance sheet data.
2. Analyze historical valuation workbooks and LP reports when onboarding a company.
3. Learn company-specific valuation methodology.
4. Extract only the fields needed for valuation and LP reporting.
5. Automatically map financial statement labels using AI.
6. Classify EBITDA adjustments using policy and prior approved examples.
7. Produce confidence-scored recommendations.
8. Auto-apply high-confidence decisions but add them to a review queue.
9. Allow reviewers to chat with the system and make targeted changes.
10. Recalculate only affected outputs instead of restarting the process.
11. Generate an Excel valuation workbook containing formulas that auditors can trace.
12. Preserve source lineage, decision lineage, and audit history.
13. Eventually provide approved outputs to a Fund III aggregation process.

Design the best agent architecture and agent-flow architecture for this system.

Identify:
- required agents
- required SharePoint lists
- required document libraries
- required workflows
- state transitions
- review process
- confidence-scoring locations and methods
- data model
- workbook generation strategy
- conversational update strategy

Show me the proposed architecture before generating anything.