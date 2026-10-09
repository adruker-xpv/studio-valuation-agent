// excel-export.ts (build 11.6) - EXCEL'S OWN ANSWER: writes, into the workbook it runs on, every cell (sheet, cell, formula,
// value, type) and, for one cell of every distinct formula, the cells Excel says it uses. Nothing else is changed.
// HOW TO USE: run it on a COPY of the workbook whose name contains "export" (e.g. "Delta Q1 2026 - export.xlsx").
//   Excel for the web > Automate > excel-export > Run.  If it says "Run again", press Run again until it says "Finished".
// It adds three sheets: "XLX Info" (progress and counts), "XLX Cells" (every cell), "XLX Uses" (what formulas use).
const BUDGET_MS = 90000;                 // stop safely before the time limit; the next run continues where this one stopped
const CHUNK_ROWS = 2000;
const SKIP_PREFIX = "XLX ";

function main(workbook: ExcelScript.Workbook): string {
  const t0 = Date.now();
  const name = workbook.getName();
  if (!/export/i.test(name)) {
    const msg = "Stopped: run this only on a COPY whose file name contains the word 'export' (it adds sheets to the file).";
    console.log(msg);
    return msg;
  }
  const info = sheet(workbook, "XLX Info");
  const cells = sheet(workbook, "XLX Cells");
  const uses = sheet(workbook, "XLX Uses");
  const sheets = workbook.getWorksheets().filter(w => !w.getName().startsWith(SKIP_PREFIX));
  if (String(info.getRange("A1").getValue()) !== "Excel export") {
    info.getRange("A:H").setNumberFormat("@");
    cells.getRange("A:E").setNumberFormat("@");
    uses.getRange("A:D").setNumberFormat("@");
    info.getRange("A1:B6").setValues([["Excel export", "script version 1"], ["Workbook", name], ["Status", "In progress"],
      ["Started", new Date().toISOString()], ["Cells rows used", "1"], ["Uses rows used", "1"]]);
    cells.getRange("A1:E1").setValues([["Sheet", "Cell", "Formula", "Value", "Type"]]);
    uses.getRange("A1:D1").setValues([["Sheet", "Cell", "Uses", "Note"]]);
    const rows: string[][] = [["Sheet", "Visibility", "Rows total", "Rows done", "Cells exported", "Patterns total", "Patterns checked", "Done"]];
    for (const w of sheets) {
      rows.push([w.getName(), String(w.getVisibility()), "-1", "0", "0", "-1", "0", "no"]);
    }
    info.getRange(`A10:H${9 + rows.length}`).setValues(rows);
  }
  const n = sheets.length;
  const state = info.getRange(`A11:H${10 + n}`).getValues().map(r => r.map(x => String(x)));
  let cellRow = Number(info.getRange("B5").getValue());
  let useRow = Number(info.getRange("B6").getValue());
  for (let i = 0; i < n; i++) {
    const st = state[i];
    if (st[7] === "yes") {
      continue;
    }
    const ws = workbook.getWorksheet(st[0]);
    const used = ws ? ws.getUsedRange(true) : undefined;
    if (!ws || !used) {
      st[2] = "0"; st[5] = "0"; st[7] = "yes";
      continue;
    }
    const r0 = used.getRowIndex(), c0 = used.getColumnIndex(), nr = used.getRowCount(), nc = used.getColumnCount();
    st[2] = String(nr);
    // 1. every cell, in chunks of rows
    while (Number(st[3]) < nr) {
      const start = Number(st[3]);
      const take = Math.min(CHUNK_ROWS, nr - start);
      const part = ws.getRangeByIndexes(r0 + start, c0, take, nc);
      const f = part.getFormulas(), v = part.getValues(), t = part.getValueTypes();
      const out: string[][] = [];
      for (let a = 0; a < take; a++) {
        for (let b = 0; b < nc; b++) {
          const fx = String(f[a][b]);
          const isF = fx.startsWith("=");
          const val = v[a][b];
          if (!isF && (val === "" || val === null)) {
            continue;
          }
          out.push([st[0], col(c0 + b + 1) + String(r0 + start + a + 1), isF ? fx : "", text(val, t[a][b]), kind(t[a][b])]);
        }
      }
      if (out.length > 0) {
        cells.getRange(`A${cellRow + 1}:E${cellRow + out.length}`).setValues(out);
        cellRow += out.length;
      }
      st[3] = String(start + take);
      st[4] = String(Number(st[4]) + out.length);
      if (Date.now() - t0 > BUDGET_MS) {
        return pause(info, state, n, cellRow, useRow, `${i} of ${n} sheets done`);
      }
    }
    // 2. what formulas use: one cell per distinct formula (copies of one formula share its pattern)
    const r1c1 = used.getFormulasR1C1();
    const seen: { [p: string]: boolean } = {};
    const firsts: string[][] = [];
    for (let a = 0; a < nr; a++) {
      for (let b = 0; b < nc; b++) {
        const p = String(r1c1[a][b]);
        if (p.startsWith("=") && !seen[p]) {
          seen[p] = true;
          firsts.push([col(c0 + b + 1) + String(r0 + a + 1), p]);
        }
      }
    }
    st[5] = String(firsts.length);
    while (Number(st[6]) < firsts.length) {
      const j = Number(st[6]);
      const addr = firsts[j][0];
      let usesText = "";
      let note = "";
      try {
        usesText = ws.getRange(addr).getDirectPrecedents().getAddresses().join("; ");
      } catch (e) {
        note = "Excel could not list what this formula uses: " + String(e).substring(0, 60);
      }
      uses.getRange(`A${useRow + 1}:D${useRow + 1}`).setValues([[st[0], addr, usesText, note]]);
      useRow += 1;
      st[6] = String(j + 1);
      if (Date.now() - t0 > BUDGET_MS) {
        return pause(info, state, n, cellRow, useRow, `${i} of ${n} sheets done`);
      }
    }
    st[7] = "yes";
  }
  let names = workbook.getNames().length;
  for (const w of sheets) {
    names += w.getNames().length;
  }
  let linked = "not available";
  try {
    linked = String(workbook.getLinkedWorkbooks().length);
  } catch (e) {
    linked = "not available";
  }
  info.getRange(`A11:H${10 + n}`).setValues(state);
  info.getRange("A3:B8").setValues([["Status", "Finished"], ["Finished", new Date().toISOString()], ["Cells rows used", String(cellRow)],
    ["Uses rows used", String(useRow)], ["Defined names", String(names)], ["Tables / linked workbooks", `${workbook.getTables().length} / ${linked}`]]);
  const msg = `Finished: ${cellRow - 1} cells and ${useRow - 1} formula checks written. Save the file (it saves automatically) and give it to the agent.`;
  console.log(msg);
  return msg;
}

function pause(info: ExcelScript.Worksheet, state: string[][], n: number, cellRow: number, useRow: number, progress: string): string {
  info.getRange(`A11:H${10 + n}`).setValues(state);
  info.getRange("A5:B6").setValues([["Cells rows used", String(cellRow)], ["Uses rows used", String(useRow)]]);
  const msg = `Run again: not finished yet (${progress}). Press Run again until it says Finished.`;
  console.log(msg);
  return msg;
}

function sheet(workbook: ExcelScript.Workbook, nm: string): ExcelScript.Worksheet {
  const w = workbook.getWorksheet(nm);
  return w ? w : workbook.addWorksheet(nm);
}

function col(n: number): string {
  let s = "";
  while (n > 0) {
    const r = (n - 1) % 26;
    s = String.fromCharCode(65 + r) + s;
    n = Math.floor((n - 1) / 26);
  }
  return s;
}

function kind(t: ExcelScript.RangeValueType): string {
  if (t === ExcelScript.RangeValueType.double || t === ExcelScript.RangeValueType.integer) {
    return "number";
  }
  if (t === ExcelScript.RangeValueType.string) {
    return "text";
  }
  if (t === ExcelScript.RangeValueType.boolean) {
    return "boolean";
  }
  if (t === ExcelScript.RangeValueType.error) {
    return "error";
  }
  if (t === ExcelScript.RangeValueType.empty) {
    return "empty";
  }
  return "other";
}

function text(v: string | number | boolean, t: ExcelScript.RangeValueType): string {
  if (t === ExcelScript.RangeValueType.boolean) {
    return v ? "TRUE" : "FALSE";
  }
  return String(v);
}
