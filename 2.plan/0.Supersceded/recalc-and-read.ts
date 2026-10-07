// recalc-and-read.ts (v4, valuation pipeline build 11.2)
// Recalculates a COPY of a workbook in SharePoint and returns the values of the requested cells.
// THIS SCRIPT SAVES THE FILE IT RUNS ON, so it refuses unless the file name contains "__copy" or "__draft".
// v4: reads the cell list BEFORE calculating (tolerates ["Sheet!A1", ...], ['Sheet'!A1, ...] or "Sheet!A1, Sheet!B2"),
//     and checks only the requested cells (no workbook-wide scan), so it returns as fast as Excel can calculate.
// Parameter `cells`: list of references, e.g. ["Valuation!B21", "LP Summary!C4"].
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
      version: 4, guard: "refused", workbook: name,
      reason: name ? "the file name must contain __copy or __draft; approved originals are never recalculated because this script saves the file"
                   : "the workbook name could not be read, so the copy/draft guard cannot be checked"
    });
  }
  const refs = parseRefs(cells);
  if (refs.length === 0) {
    return JSON.stringify({ version: 4, guard: "ok", workbook: name, error: "no cell references could be read from the cells parameter" });
  }
  const app = workbook.getApplication();
  const mode = String(app.getCalculationMode());
  app.calculate(ExcelScript.CalculationType.full);
  const values: { [ref: string]: string | number | boolean } = {};
  const errors: { [ref: string]: string } = {};
  for (const ref of refs.slice(0, 500)) {
    const bang = ref.lastIndexOf("!");
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
    const r = ws.getRange(address);
    const v = r.getValue();
    if (r.getValueType() === ExcelScript.RangeValueType.error) {
      errors[ref] = String(v);
    } else {
      values[ref] = v;
    }
  }
  return JSON.stringify({
    version: 4, guard: "ok", workbook: name, seconds: (Date.now() - started) / 1000, calculation_mode: mode,
    values: values, errors: errors, error_count_total: Object.keys(errors).length, error_sample: []
  });
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
