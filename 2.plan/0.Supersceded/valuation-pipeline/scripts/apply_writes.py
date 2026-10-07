# apply_writes.py (v2) - writes the plan into a copy of the workbook by editing ONLY the target cells
# inside the file. Every other part of the .xlsx (drawings, charts, external links, pivots, macros,
# formatting) is copied byte for byte, so Excel has nothing to repair. Formulas are never touched.
# Cached results of formula cells are removed, so an upload that Excel did not recalculate is detected,
# and the workbook is set to recalculate fully when opened.
# Usage: python apply_writes.py --workbook <base.xlsx> --plan write_plan.json --out <stem>_<mode>_draft.xlsx
import sys, os, re, json, argparse, zipfile
from xml.sax.saxutils import escape
from openpyxl.utils import column_index_from_string as col_idx

REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def sheet_parts(z):
    wb = z.read("xl/workbook.xml").decode("utf-8")
    rels = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    rid = {m.group(1): m.group(2) for m in re.finditer(r'<Relationship[^>]*?Id="([^"]+)"[^>]*?Target="([^"]+)"', rels)}
    rid.update({m.group(2): m.group(1) for m in re.finditer(r'<Relationship[^>]*?Target="([^"]+)"[^>]*?Id="([^"]+)"', rels)})
    out = {}
    for m in re.finditer(r'<sheet\b[^>]*>', wb):
        tag = m.group(0)
        name = re.search(r'\bname="([^"]*)"', tag).group(1)
        r = re.search(r'\br:id="([^"]+)"|\b\w+:id="([^"]+)"', tag)
        target = rid[r.group(1) or r.group(2)]
        target = target.lstrip("/")
        out[unescape(name)] = target if target.startswith("xl/") else "xl/" + target
    return out


def unescape(s):
    return s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'")


def split_ref(ref):
    col = "".join(ch for ch in ref if ch.isalpha())
    return col, int(ref[len(col):])


def cell_xml(ref, attrs, value):
    attrs = re.sub(r'\s+t="[^"]*"', "", attrs)
    if value is None:
        return f'<c r="{ref}"{attrs}/>'
    if isinstance(value, bool):
        return f'<c r="{ref}"{attrs} t="b"><v>{int(value)}</v></c>'
    if isinstance(value, (int, float)):
        return f'<c r="{ref}"{attrs}><v>{repr(float(value)) if isinstance(value, float) else value}</v></c>'
    return f'<c r="{ref}"{attrs} t="inlineStr"><is><t xml:space="preserve">{escape(str(value))}</t></is></c>'


CELL = r'<c r="{ref}"(?P<attrs>(?:\s[^>]*?)?)(?:/>|>(?P<body>.*?)</c>)'


def set_cells(xml, writes):
    """writes: {ref: value}. Refuses formula cells. Inserts missing cells/rows in order."""
    for ref, value in writes.items():
        m = re.search(CELL.format(ref=ref), xml, flags=re.S)
        if m:
            if m.group("body") and "<f" in m.group("body"):
                raise ValueError(f"{ref} holds a formula; refusing to write")
            xml = xml[:m.start()] + cell_xml(ref, m.group("attrs") or "", value) + xml[m.end():]
            continue
        col, row = split_ref(ref)
        new = cell_xml(ref, "", value)
        rm = re.search(rf'<row r="{row}"(?P<a>[^>]*?)(?:/>|>(?P<b>.*?)</row>)', xml, flags=re.S)
        if rm:
            body = rm.group("b") or ""
            cells = list(re.finditer(r'<c r="([A-Z]+)\d+"', body))
            pos = next((c.start() for c in cells if col_idx(c.group(1)) > col_idx(col)), len(body))
            body = body[:pos] + new + body[pos:]
            xml = xml[:rm.start()] + f'<row r="{row}"{rm.group("a")}>{body}</row>' + xml[rm.end():]
        else:
            rows = list(re.finditer(r'<row r="(\d+)"', xml))
            pos = next((r_.start() for r_ in rows if int(r_.group(1)) > row), None)
            if pos is None:
                pos = xml.index("</sheetData>") if "</sheetData>" in xml else None
            if pos is None:
                xml = xml.replace("<sheetData/>", f'<sheetData><row r="{row}">{new}</row></sheetData>')
            else:
                xml = xml[:pos] + f'<row r="{row}">{new}</row>' + xml[pos:]
    return xml


def strip_cached(xml):
    """remove cached results of formula cells (keep the formulas)."""
    def fix(m):
        body = m.group("body")
        if body is None or "<f" not in body:
            return m.group(0)
        attrs = re.sub(r'\s+t="(?:str|n|b|e)"', "", m.group("attrs") or "")
        return f'<c r="{m.group("r")}"{attrs}>' + re.sub(r"<v>.*?</v>|<v/>", "", body, flags=re.S) + "</c>"
    return re.sub(r'<c r="(?P<r>[A-Z]+\d+)"(?P<attrs>(?:\s[^>]*?)?)(?:/>|>(?P<body>.*?)</c>)', fix, xml, flags=re.S)


def full_calc(wbxml):
    if "<calcPr" in wbxml:
        return re.sub(r"<calcPr\b([^>]*?)(/?)>", lambda m: "<calcPr" + re.sub(r'\s+fullCalcOnLoad="[^"]*"', "", m.group(1))
                      + ' fullCalcOnLoad="1"' + m.group(2) + ">", wbxml, count=1)
    for anchor in ("</definedNames>", "</sheets>"):
        if anchor in wbxml:
            return wbxml.replace(anchor, anchor + '<calcPr fullCalcOnLoad="1"/>', 1)
    return wbxml


def main(a):
    plan = json.load(open(a.plan, encoding="utf-8"))
    by_sheet, written, skipped = {}, 0, 0
    for p in plan["writes"]:
        sh, cell = p["cell"].rsplit("!", 1)
        ok = p["status"] in ("ok", "flag", "historical") and p["value"] is not None
        if ok:
            by_sheet.setdefault(sh, {})[cell] = p["value"]; p["written"] = True; written += 1
        else:
            p["written"] = False; skipped += 1
            if plan["mode"] in ("replay", "backtest"):         # prove nothing survives from the base
                by_sheet.setdefault(sh, {})[cell] = None
    with zipfile.ZipFile(a.workbook) as zin:
        parts = sheet_parts(zin)
        missing = [s for s in by_sheet if s not in parts]
        if missing:
            raise ValueError(f"sheets not found in the workbook: {missing}")
        targets = {parts[s]: s for s in by_sheet}
        with zipfile.ZipFile(a.out, "w") as zout:
            for info in zin.infolist():
                data = zin.read(info.filename)
                if info.filename in targets:
                    data = set_cells(data.decode("utf-8"), by_sheet[targets[info.filename]]).encode("utf-8")
                if re.match(r"xl/worksheets/sheet\d*\.xml$", info.filename):
                    data = strip_cached(data.decode("utf-8")).encode("utf-8")
                elif info.filename == "xl/workbook.xml":
                    data = full_calc(data.decode("utf-8")).encode("utf-8")
                elif info.filename == "xl/calcChain.xml":
                    pass                                           # kept: formulas are unchanged
                zout.writestr(info, data)
    log = a.out.rsplit(".", 1)[0] + "_write_log.json"
    json.dump(plan, open(log, "w", encoding="utf-8"), indent=1, default=str)
    print(f"DRAFT WRITTEN: {a.out} | written: {written} | not written: {skipped} | "
          f"method: in-place cell edit (all other workbook parts copied unchanged)")
    print(f"WRITE LOG: {log}")
    print("NEXT REQUIRED STEP: give the user the draft with the Excel-step instructions (open in desktop Excel, save, "
          "upload), then run check_result.py on the uploaded file.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workbook", required=True); ap.add_argument("--plan", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    try:
        main(a)
    except Exception as e:
        print(f"APPLY_ERROR: {type(e).__name__}: {e}"); sys.exit(1)
