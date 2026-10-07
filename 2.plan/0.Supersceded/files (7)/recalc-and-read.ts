// recalc-and-read.ts (v5, valuation pipeline build 11.3)
// Recalculates a COPY of a workbook in SharePoint and returns the values of requested cells.
// THIS SCRIPT SAVES THE FILE IT RUNS ON, so it refuses unless the file name contains "__copy" or "__draft".
// Parameter `cells` (unchanged name, so the agent's tool needs no change) is either
//   - a cell list, as in v4: ["Valuation!B21", "LP Summary!C4"]  -> mode "full": calculate, then read the cells; or
//   - a JSON object for the staged diagnostic (v5):
//       {"mode": "probe", "cells": [...]}   opens the copy and reads up to 10 cells, NO calculation (proves access / file Id)
//       {"mode": "recalc", "addin_cells": [...], "refresh_links": false}
//                                           full recalculation only, timed; optionally refreshes linked workbooks first
//                                           (timed separately); then checks the given add-in cells for error values
//       {"mode": "read", "cells": [...]}    reads the cells, NO calculation (after a recalc stage)
// Every result reports "stages" with seconds, so formula calculation, link refresh and add-in refresh can be told apart.
function main(workbook: ExcelScript.Workbook, cells: string): string {
  const started = Date.now();
  let name = "";
  try {
    name = workbook.getName();
  } catch (e) {
    name = "";
  }
  if (!/__(copy|draft)/i.test(name)) {
    return JSON.stringify({
      version: 5, guard: "refused", workbook: name,
      reason: name ? "the file name must contain __copy or __draft; approved originals are never recalculated because this script saves the file"
                   : "the workbook name could not be read, so the copy/draft guard cannot be checked"
    });
  }
  const req = parseRequest(cells);
  const app = workbook.getApplication();
  const mode = String(app.getCalculationMode());
  const stages: { [stage: string]: number } = {};
  let linked = -1;
  // LINKS BLOCK (v5). If the script editor underlines getLinkedWorkbooks or refreshLinks, delete from here to END LINKS BLOCK;
  // the rest of the script still works and reports linked_workbooks: -1.
  try {
    const lw = workbook.getLinkedWorkbooks();
    linked = lw.length;
    if (req.mode === "recalc" && req.refreshLinks && lw.length > 0) {
      const t = Date.now();
      for (const l of lw) {
        l.refreshLinks();
      }
      stages["links"] = (Date.now() - t) / 1000;
    }
  } catch (e) {
    linked = -1;
  }
  // END LINKS BLOCK
  if (req.mode === "probe") {
    const r = readCells(workbook, req.cells.slice(0, 10));
    stages["read_values"] = (Date.now() - started) / 1000;
    return JSON.stringify({ version: 5, guard: "ok", mode: "probe", workbook: name, seconds: (Date.now() - started) / 1000,
      calculation_mode: mode, linked_workbooks: linked, sheet_count: workbook.getWorksheets().length, stages: stages,
      values: r.values, errors: r.errors });
  }
  if (req.mode === "recalc") {
    const t = Date.now();
    app.calculate(ExcelScript.CalculationType.full);
    stages["calculate"] = (Date.now() - t) / 1000;
    const a = readCells(workbook, req.addinCells.slice(0, 20));
    return JSON.stringify({ version: 5, guard: "ok", mode: "recalc", workbook: name, seconds: (Date.now() - started) / 1000,
      calculation_mode: mode, linked_workbooks: linked, stages: stages,
      addin_check: { checked: req.addinCells.slice(0, 20).length, errors: Object.keys(a.errors).length, sample: Object.keys(a.errors).slice(0, 5) } });
  }
  if (req.cells.length === 0) {
    return JSON.stringify({ version: 5, guard: "ok", workbook: name, error: "no cell references could be read from the cells parameter" });
  }
  if (req.mode === "full") {
    const t = Date.now();
    app.calculate(ExcelScript.CalculationType.full);
    stages["calculate"] = (Date.now() - t) / 1000;
  }
  const t2 = Date.now();
  const r = readCells(workbook, req.cells.slice(0, 500));
  stages["read_values"] = (Date.now() - t2) / 1000;
  return JSON.stringify({
    version: 5, guard: "ok", mode: req.mode, workbook: name, seconds: (Date.now() - started) / 1000, calculation_mode: mode,
    linked_workbooks: linked, stages: stages, values: r.values, errors: r.errors,
    error_count_total: Object.keys(r.errors).length, error_sample: []
  });
}

interface Request {
  mode: string;
  cells: string[];
  addinCells: string[];
  refreshLinks: boolean;
}

interface CellRead {
  values: { [ref: string]: string | number | boolean };
  errors: { [ref: string]: string };
}

function readCells(workbook: ExcelScript.Workbook, refs: string[]): CellRead {
  const values: { [ref: string]: string | number | boolean } = {};
  const errors: { [ref: string]: string } = {};
  for (const ref of refs) {
    const bang = ref.lastIndexOf("!");
    if (bang < 1) {
      continue;
    }
    let sheetName = ref.substring(0, bang).trim();
    const address = ref.substring(bang + 1).trim();
    if (sheetName.startsWith("'") && sheetName.endsWith("'")) {
      sheetName = sheetName.substring(1, sheetName.length - 1).split("''").join("'");
    }
    const ws = workbook.getWorksheet(sheetName);
    if (!ws) {
      errors[ref] = "#SHEET_NOT_FOUND";
      continue;
    }
    const rg = ws.getRange(address);
    const v = rg.getValue();
    if (rg.getValueType() === ExcelScript.RangeValueType.error) {
      errors[ref] = String(v);
    } else {
      values[ref] = v;
    }
  }
  return { values: values, errors: errors };
}

function parseRequest(cells: string): Request {
  const text = (cells || "").trim();
  const out: Request = { mode: "full", cells: [], addinCells: [], refreshLinks: false };
  if (text.startsWith("{")) {
    try {
      const o = JSON.parse(text) as { mode?: string, cells?: string[], addin_cells?: string[], refresh_links?: boolean };
      out.mode = o.mode === "probe" || o.mode === "recalc" || o.mode === "read" ? o.mode : "full";
      out.cells = (o.cells || []).map(x => String(x).trim()).filter(x => x.indexOf("!") > 0);
      out.addinCells = (o.addin_cells || []).map(x => String(x).trim()).filter(x => x.indexOf("!") > 0);
      out.refreshLinks = o.refresh_links === true;
      return out;
    } catch (e) {
      // fall through
    }
  }
  out.cells = parseRefs(text);
  return out;
}

function parseRefs(cells: string): string[] {
  const text = (cells || "").trim();
  try {
    const parsed = JSON.parse(text) as string[];
    if (Array.isArray(parsed)) {
      return parsed.map(x => String(x).trim()).filter(x => x.indexOf("!") > 0);
    }
  } catch (e) {
    // not JSON: fall through to a tolerant split
  }
  const body = text.replace(/^\[/, "").replace(/\]$/, "");
  const out: string[] = [];
  let cur = "";
  let inQuote = false;
  for (const ch of body) {
    if (ch === "'") {
      inQuote = !inQuote;
    }
    if (ch === "," && !inQuote) {
      out.push(cur);
      cur = "";
    } else {
      cur += ch;
    }
  }
  out.push(cur);
  return out.map(x => x.trim().replace(/^"|"$/g, "")).filter(x => x.indexOf("!") > 0);
}
