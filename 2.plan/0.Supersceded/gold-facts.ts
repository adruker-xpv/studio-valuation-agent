// gold-facts.ts (build 11.4) - INDEPENDENT EXCEL-SIDE FACTS for a Gold workbook. Excel itself, not the discovery code,
// establishes what physically exists and which cells each sampled formula directly reads.
// Read-only: it changes nothing and saves nothing. Run it on a COPY of the hash-locked Gold file to be safe.
// Parameter `request` (JSON text):
//   {"mode": "counts"}                              per-sheet populated / formula / error cells, sheet visibility,
//   {"mode": "counts", "sheets": ["Sheet A"]}       defined names, tables, linked workbooks (one sheet at a time if a big
//                                                   workbook hits the 120 s limit; merge the results)
//   {"mode": "precedents", "cells": ["Sheet!B5"]}   each cell's DIRECT precedents as Excel reports them (getDirectPrecedents)
// If your Excel does not prompt for the parameter, paste the request into DEFAULT_REQUEST below and leave the box empty.
// Copy the logged JSON (console output) into a file: excel_facts_counts.json / excel_facts_precedents.json.
const DEFAULT_REQUEST = '{"mode": "counts"}';
const ROWS_PER_READ = 5000;

function main(workbook: ExcelScript.Workbook, request: string): string {
  const req = parseRequest(request && request.trim() ? request : DEFAULT_REQUEST);
  let out = "";
  if (req.mode === "precedents") {
    const prec: { [cell: string]: string[] | string } = {};
    for (const ref of req.cells) {
      const bang = ref.lastIndexOf("!");
      let sheetName = ref.substring(0, bang).trim();
      if (sheetName.startsWith("'") && sheetName.endsWith("'")) {
        sheetName = sheetName.substring(1, sheetName.length - 1).split("''").join("'");
      }
      const ws = workbook.getWorksheet(sheetName);
      if (!ws) {
        prec[ref] = "sheet not found";
        continue;
      }
      const rg = ws.getRange(ref.substring(bang + 1).trim());
      const formulas = rg.getFormulas();
      const f = String(formulas[0][0]);
      if (!f.startsWith("=")) {
        prec[ref] = [];
        continue;
      }
      try {
        prec[ref] = rg.getDirectPrecedents().getAddresses();
      } catch (e) {
        prec[ref] = "unavailable: " + String(e).substring(0, 80);
      }
    }
    out = JSON.stringify({ version: 1, mode: "precedents", workbook: workbook.getName(), precedents: prec });
  } else {
    const sheets: SheetCount[] = [];
    for (const ws of workbook.getWorksheets()) {
      if (req.sheets.length > 0 && req.sheets.indexOf(ws.getName()) < 0) {
        continue;
      }
      sheets.push(countSheet(ws));
    }
    let names = workbook.getNames().length;
    for (const ws of workbook.getWorksheets()) {
      names += ws.getNames().length;
    }
    let linked = -1;
    try {
      linked = workbook.getLinkedWorkbooks().length;
    } catch (e) {
      linked = -1;
    }
    out = JSON.stringify({ version: 1, mode: "counts", workbook: workbook.getName(), sheets: sheets, defined_names: names,
      tables: workbook.getTables().length, linked_workbooks: linked < 0 ? null : linked });
  }
  console.log(out);
  return out;
}

interface SheetCount {
  name: string;
  visibility: string;
  populated: number;
  formulas: number;
  errors: number;
}

interface FactsRequest {
  mode: string;
  cells: string[];
  sheets: string[];
}

function countSheet(ws: ExcelScript.Worksheet): SheetCount {
  const res: SheetCount = { name: ws.getName(), visibility: String(ws.getVisibility()), populated: 0, formulas: 0, errors: 0 };
  const used = ws.getUsedRange(true);
  if (!used) {
    return res;
  }
  const rows = used.getRowCount();
  const cols = used.getColumnCount();
  for (let start = 0; start < rows; start += ROWS_PER_READ) {
    const n = Math.min(ROWS_PER_READ, rows - start);
    const part = used.getOffsetRange(start, 0).getResizedRange(n - rows, 0);
    const f = part.getFormulas();
    const t = part.getValueTypes();
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < cols; j++) {
        const fx = String(f[i][j]);
        if (fx.startsWith("=")) {
          res.formulas += 1;
        }
        if (fx !== "") {
          res.populated += 1;
        }
        if (t[i][j] === ExcelScript.RangeValueType.error) {
          res.errors += 1;
        }
      }
    }
  }
  return res;
}

function parseRequest(text: string): FactsRequest {
  const out: FactsRequest = { mode: "counts", cells: [], sheets: [] };
  try {
    const o = JSON.parse(text) as { mode?: string, cells?: string[], sheets?: string[] };
    out.mode = o.mode === "precedents" ? "precedents" : "counts";
    out.cells = (o.cells || []).map(x => String(x).trim()).filter(x => x.indexOf("!") > 0);
    out.sheets = (o.sheets || []).map(x => String(x));
  } catch (e) {
    out.mode = "counts";
  }
  return out;
}
