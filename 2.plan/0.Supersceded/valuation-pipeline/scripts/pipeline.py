# pipeline.py - the valuation pipeline: one command per job, all deterministic.
#
#   onboard  --workbook W --statements S [S ...] --company "Display Name" [--company-id id] [--bundle B] [--period-end YYYY-MM-DD]
#   run      --mode replay|backtest|refresh --workbook W --statements S [S ...] --bundle B [--actual A] [--period-end YYYY-MM-DD]
#   check    --saved F [--run-log R]                  (after the Excel step)
#   amend    [--changes /app/created/changes.json] [--bundle B]   (corrections, confirmations, approvals, manual inputs)
#   selftest
# Global options: --out (deliverables, default /app/created)  --work (scratch, default /tmp/valuation_work)
#                 --debug (keep every intermediate file in <out>/debug/<company_id>/ for diagnosis)
#
# Exit codes: 0 done | 10 judgment needed | 20 Excel step | 3 stopped (plan refused or blocked) | 1 error
#
# Company knowledge travels as ONE zip, <company_id>_company.zip:
#   company_profile.json  identity (company_id, display_name), profile_version, named review, decisions log, open items
#   input_map.json        workbook structure: key outputs, controls, input classifications
#   mapping_profile.json  statement rules (executable), lineage evidence, period offsets
# Per run: <company_id>_<quarter>_<mode>_draft.xlsx and <company_id>_<quarter>_<mode>_run_log.json (writes + lineage + check).
import os, re, sys, json, glob, shutil, hashlib, argparse, subprocess, datetime, zipfile
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wbutil import norm_label, cells_of, ref

ASSUMPTION_WORDS = re.compile(r"multiple|discount|rate|premium|haircut|weight|growth|wacc|factor|probability|%|x$", re.I)
CAP_WORDS = re.compile(r"share|units|option|warrant|ownership|holding|strike|exercise|preferred|pref\b|esop|dilut", re.I)
ADJ_WORDS = re.compile(r"add.?back|adjust|normali|one.?off|non.?recurring|pro.?forma", re.I)
OP_PERIOD = {"sum_months": lambda sp: {3: "quarter_sum_of_months", 12: "ltm_sum"}.get(int(sp.get("months", 3)), "month"),
             "ytd_difference": lambda sp: "ytd_difference", "value_at": lambda sp: "quarter_end_balance",
             "components": lambda sp: "point_in_time"}
TODAY = lambda: datetime.date.today().isoformat()
LIMIT = 4_000_000                              # inline limit for connector file uploads
MAX_KEY_OUTPUTS = 25                           # must match extract_schema.py
UPLOADS = "/app/uploads"
# files can be uploaded to SharePoint by path only from here (the self-test points it at its own folder)
UPLOAD_ROOT = os.environ.get("VALUATION_UPLOAD_ROOT") or ("/app/created" if os.path.isdir("/app") else None)
UPLOAD_SUFFIX = re.compile(r"-[0-9a-f]{8}(?=\.[A-Za-z0-9]+$)")
SUFFIX = {"inc", "ltd", "limited", "llc", "lp", "llp", "corp", "corporation", "co", "company", "technologies", "technology",
          "holdings", "holding", "group", "plc", "gmbh", "ag", "sa", "bv", "ulc"}


# ------------------------------------------------------------------------------------------ small helpers
def sh(args):
    p = subprocess.run([sys.executable] + args, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def line(out, key):
    for l in out.splitlines():
        if l.startswith(key):
            return l.split(":", 1)[1].strip()
    return ""


def S(n):
    return os.path.join(HERE, n)


def stem_of(path):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", os.path.splitext(os.path.basename(path))[0])


def load(p, default=None):
    return json.load(open(p, encoding="utf-8")) if p and os.path.exists(p) else default


def dump(obj, p):
    json.dump(obj, open(p, "w", encoding="utf-8"), indent=1, default=str)
    return p


def fail(out_text, stage):
    print(f"PIPELINE ERROR in {stage}:\n" + "\n".join(l for l in out_text.splitlines() if "ERROR" in l or l.startswith("-"))[:2000])
    sys.exit(1)


def company_slug(name):
    """deterministic company_id: lowercase words of the name without legal/generic suffixes ('LuminUltra Technologies' -> luminultra)."""
    words = re.findall(r"[A-Za-z0-9]+", name or "")
    core = [w for w in words if w.lower() not in SUFFIX] or words
    return "-".join(w.lower() for w in core)[:40] or None


def quarter_of(period):
    return f"{period[:4]}-Q{(int(period[5:7]) - 1) // 3 + 1}" if period and re.match(r"\d{4}-\d{2}", str(period)) else "period"


COPY_SUFFIX = re.compile(r"(?:_\d{1,2}| \(\d{1,2}\))(?=\.[A-Za-z0-9]+$)")


def find_file(name, dirs):
    """files are passed by NAME; a chat upload may carry "-1a2b3c4d" and a SharePoint download "_1" or " (1)".
    Exact name first, then the stable name; the newest match wins."""
    if not name:
        return None
    base = os.path.basename(name)
    stable = lambda n: COPY_SUFFIX.sub("", UPLOAD_SUFFIX.sub("", n))
    files = [f for d in dirs for f in glob.glob(os.path.join(d, "**", "*"), recursive=True) if os.path.isfile(f)]
    for test in (lambda f: os.path.basename(f) == base, lambda f: stable(os.path.basename(f)) == stable(base)):
        hits = [f for f in files if test(f)]
        if hits:
            return max(hits, key=os.path.getmtime)
    return None


def resolve_inputs(a, out, names):
    """resolve every input file given by name (uploads or SharePoint downloads); stop listing all that are missing."""
    missing = []
    for n in names:
        v = getattr(a, n, None)
        if not v:
            continue
        if isinstance(v, list):
            got = [resolve(x, out) for x in v]
            missing += [x for x, g in zip(v, got) if not g]
            setattr(a, n, [g for g in got if g])
        else:
            g = resolve(v, out)
            if not g:
                missing.append(v)
            setattr(a, n, g)
    if missing:
        print("PIPELINE ERROR: these files are not in the chat: " + "; ".join(missing) +
              ". Ask the user to upload them or paste their SharePoint links (download each link with sharepoint_get_doc)."); sys.exit(1)


def resolve(path, out):
    if not path:
        return None
    if os.path.exists(path):
        return os.path.abspath(path)
    return find_file(path, [d for d in (out, UPLOADS, os.path.dirname(path)) if d and os.path.isdir(d)])


def work_dir(a, cid):
    d = os.path.join(a.out, "debug", cid) if a.debug else os.path.join(a.work, cid)
    os.makedirs(d, exist_ok=True)
    return d


def sp_lines(cid, sub, paths, folder=True):
    """exact SharePoint tool inputs, so the agent copies them instead of working them out. The folder line is printed
    only where the folder may not exist yet (onboarding: company/, run: the quarter folder)."""
    rel = f"Valuations/{cid}/{sub}"
    lines = [f"SHAREPOINT: Create new folder | library: Documents | path: {rel}  (if it already exists, continue)"] if folder else []
    for p_ in paths:
        if not p_ or not os.path.exists(p_):
            continue
        b, n = os.path.getsize(p_), os.path.basename(p_)
        if b >= LIMIT:
            lines.append(f"SHAREPOINT: SKIP {n} ({b / 1024:,.0f} KB >= 4 MB) - return it as a download")
        elif UPLOAD_ROOT and not os.path.abspath(p_).startswith(UPLOAD_ROOT.rstrip("/") + "/"):
            lines.append(f"SHAREPOINT: SKIP {n} - not in {UPLOAD_ROOT}; return it as a download")
        else:
            lines.append(f"SHAREPOINT: Create file | folderPath: /Shared Documents/{rel} | name: {n} | body: {os.path.abspath(p_)}")
    return lines


# ------------------------------------------------------------------------------------------ company bundle + profile
def read_bundle(bundle, dest):
    """-> {'cp', 'imap', 'prof', 'legacy'} paths from <company_id>_company.zip (or an older _company_files.zip)."""
    shutil.rmtree(dest, ignore_errors=True); os.makedirs(dest)
    with zipfile.ZipFile(bundle) as z:
        z.extractall(dest)
    names = sorted(os.listdir(dest))
    pick = lambda pat: next((os.path.join(dest, n) for n in names if re.search(pat, n)), None)
    cp = pick(r"^company_profile\.json$")
    return {"cp": cp, "imap": pick(r"^input_map\.json$") or pick(r"_input_map\.json$"),
            "prof": pick(r"^mapping_profile\.json$"), "legacy": cp is None}


def write_bundle(out, cp, imap_path, prof_path, W):
    cp_path = dump(cp, os.path.join(W, "company_profile.json"))
    path = os.path.join(out, f"{cp['company_id']}_company.zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(cp_path, "company_profile.json")
        z.write(imap_path, "input_map.json")
        z.write(prof_path, "mapping_profile.json")
    return path


def new_cp(cid, name):
    return {"company_id": cid, "display_name": name, "profile_version": 0, "profile_hash": None, "status": None,
            "period_end": None, "review": {"approved_by": None, "approved_on": None, "profile_version": None},
            "onboarded_from": {}, "open_items": [], "decisions": []}


def entity_of(prof_path):
    for c in (load(prof_path) or {}).get("concepts", []):
        if c.get("entity") and c["entity"] != "UNCERTAIN":
            return c["entity"]
    return None


def approval_text(cp):
    r = cp.get("review") or {}
    if not r.get("approved_by"):
        return "not yet approved"
    t = f"approved by {r['approved_by']} on {r['approved_on']} (v{r['profile_version']})"
    return t if r.get("profile_version") == cp.get("profile_version") else t + f"; current v{cp['profile_version']} not yet approved"


def add_decision(cp, kind, item, change, said, by, status="active"):
    """append to the decisions log; an active decision supersedes earlier ones for the same item."""
    nid = max([d["id"] for d in cp["decisions"]] or [0]) + 1
    if status == "active":
        for d in cp["decisions"]:
            if d["kind"] == kind and d["item"] == item and d["status"] in ("active", "proposed", "confirmed"):
                d["status"], d["superseded_by"] = "superseded", nid
    cp["decisions"].append({"id": nid, "date": TODAY(), "period": quarter_of(cp.get("period_end")), "kind": kind,
                            "item": item, "change": change, "said": said, "by": by, "status": status})
    return nid


def active(cp, kind):
    return [d for d in cp.get("decisions", []) if d["kind"] == kind and d["status"] == "active"]


def history(cp, cell=None, concept=None):
    """decisions touching a cell or concept - shown only when a review item hits that cell or concept."""
    hits = []
    for d in (cp or {}).get("decisions", []):
        if d["status"] == "superseded" or d["kind"] == "approval":
            continue
        it = d["item"]
        if concept and it == f"concept:{concept}":
            hits.append(d)
        elif cell and it.startswith("cell:"):
            try:
                if cell.replace("'", "") in {ref(k) for k in cells_of(it[5:])}:
                    hits.append(d)
            except Exception:
                pass
        elif cell and it == f"key_output:{cell.replace(chr(39), '')}":
            hits.append(d)
    cut = lambda t: t if len(t) <= 120 else t[:117].rsplit(" ", 1)[0] + "..."
    return "; ".join(f"decision #{d['id']} {d['date']} {d['by'] or 'unnamed'}: \"{cut(d.get('said') or '')}\""
                     for d in hits[-2:])


def ko_items_from_imap(imap):
    rs, ctrl = imap.get("key_output_reasons", {}), {c["cell"]: c for c in imap.get("controls", [])}
    items = []
    for c in imap.get("key_outputs", []):
        it = {"cell": c, "reason": rs.get(c) or "reused from saved input map"}
        if c in ctrl:
            it["control"] = {k: ctrl[c][k] for k in ("control_type", "expected", "absolute_tolerance", "severity") if k in ctrl[c]}
        items.append(it)
    return items


def apply_ko_decisions(items, cp):
    nc = lambda c: c.replace("'", "")
    for d in active(cp, "key_output"):
        ch = d["change"]
        items = [i for i in items if nc(i["cell"]) != nc(ch["cell"])]
        if ch.get("action") != "remove":
            it = {"cell": ch["cell"], "reason": ch.get("reason") or f"analyst decision #{d['id']}", "_analyst": True}
            if ch.get("control"):
                it["control"] = ch["control"]
            items.append(it)
    while len(items) > MAX_KEY_OUTPUTS:        # keep analyst choices and controls; drop the last rule-chosen metric
        drop = next((i for i in reversed(items) if not i.get("_analyst") and not i.get("control")), items[-1])
        items.remove(drop)
    return [{k: v for k, v in i.items() if k != "_analyst"} for i in items]


def parse_json_arg(v):
    """--answers / --changes take one-line JSON (saves the agent a file write) or a path to a JSON file."""
    if not v:
        return None
    if v.strip() == "-":
        v = sys.stdin.read()
    v = v.strip()
    if v.startswith("{"):
        try:
            return json.loads(v)
        except json.JSONDecodeError as e:
            print(f"PIPELINE ERROR: the JSON given is not valid ({e}); fix it and re-run the same command."); sys.exit(1)
    p = v if os.path.exists(v) else None
    if not p:
        print(f"PIPELINE ERROR: {v} not found"); sys.exit(1)
    return load(p)


def agent_file(out, W, name, stem):
    """judgment answers are written by the agent in <out>; once used they are kept in the work folder, stamped with
    the workbook they answered, so a later onboarding of a different workbook never reuses them."""
    p = os.path.join(out, name)
    if os.path.exists(p):
        return p
    p = os.path.join(W, name)
    return p if (load(p) or {}).get("_workbook") == stem else None


def tidy(out, W, names, stem=None):
    for n in names:
        p = os.path.join(out, n)
        if os.path.exists(p) and os.path.abspath(out) != os.path.abspath(W):
            try:
                d = load(p)
                if isinstance(d, dict) and stem:
                    d["_workbook"] = stem
                dump(d, os.path.join(W, n)); os.remove(p)
            except Exception:
                os.replace(p, os.path.join(W, n))


# ------------------------------------------------------------------------------------------ onboard
FS_WORDS = re.compile(r"revenue|sales|ebitda|ebit\b|cash|debt|borrow|loan|cogs|cost of|expense|income|margin|profit|"
                      r"assets|liabilit|capex|working capital|payable|receivable|inventory", re.I)
PRIOR_WORDS = re.compile(r"prior|previous|last quarter|last year|\bpq\b|\bpy\b|opening", re.I)
COMP_SHEET = re.compile(r"comp|peer|precedent|transaction|trading|market data", re.I)
CAP_SHEET = re.compile(r"cap ?table|capitali|shareholder|equity schedule|ownership|esop|option", re.I)
INSTR_SHEET = re.compile(r"pref|preferred|note|debenture|loan|instrument|convertible|safe|term sheet", re.I)
DATE_VAL = re.compile(r"^\d{4}-\d{2}-\d{2}")


def suggest(entry, block):
    """deterministic first-pass classification from rule evidence, sheet, header, label and value types.
    needs_judgment marks only what evidence cannot settle."""
    lab, flags = entry["label"], entry.get("flags") or []
    sheet, hdr = entry.get("sheet", ""), entry.get("header") or ""
    vals = [str(v) for v in entry.get("sample_values") or []]
    ctx = f"{lab} | {hdr}"
    path = next(iter((entry.get("paths_to_key_outputs") or {}).values()), [])
    via = " -> ".join(path[:4])
    spec = (block or {}).get("execution_spec")
    base = {"id": entry["id"], "reviewed_by": None}
    sheet_says = (COMP_SHEET.search(entry.get("sheet", "")) or CAP_SHEET.search(entry.get("sheet", ""))
                  or INSTR_SHEET.search(entry.get("sheet", "")))
    if spec and sheet_says and not FS_WORDS.search(lab):
        spec = None                   # a statement "match" on a cap-table / instrument / comps sheet is a coincidence
    if spec:
        rule = f"{spec['operation']}{'(' + str(spec['months']) + ')' if spec.get('months') else ''} of '{spec['source']['label']}'"
        s_ = dict(base, type="financial_statement", expected_source=f"{spec['source']['sheet']}: {spec['source']['label']} ({rule})",
                  changes_each_quarter="yes", confidence="high" if not flags else "medium",
                  notes=f"Statement rule {rule} reproduced the workbook value; path {via}.")
        return s_, bool(flags)
    if re.search(r"(months?|days?|years?|periods?) (until|to|remaining|left)|remaining (term|life)|time to (maturity|expiry)|"
                 r"\bage\b|elapsed|since (issue|investment)", lab, re.I):
        return (dict(base, type="assumption", expected_source=None, changes_each_quarter="yes", confidence="medium",
                     notes=f"'{lab}' counts time, so it changes every period by itself; carrying it forward would be stale; "
                           f"path {' -> '.join((next(iter((entry.get('paths_to_key_outputs') or {}).values()), []))[:4])}."), False)
    ev = lambda t, ch, why, conf="medium": (dict(base, type=t, expected_source=None, changes_each_quarter=ch, confidence=conf,
                                                  notes=f"{why}; path {via}. Cadence proposed, not evidenced."), bool(flags) and conf != "high")
    if PRIOR_WORDS.search(ctx):
        return ev("prior_period", "yes", f"'{ctx}' is labelled as a prior-period value", "high")
    if COMP_SHEET.search(sheet):
        return ev("reference_data", "on_event", f"on the comparables sheet '{sheet}' (comp set reviewed as a whole)")
    if CAP_SHEET.search(sheet) or CAP_WORDS.search(ctx):
        return ev("carry_forward_event_driven", "on_event", f"capitalization data on '{sheet}' ('{lab}')")
    if INSTR_SHEET.search(sheet) and not FS_WORDS.search(lab):
        return ev("carry_forward_event_driven", "on_event", f"instrument term on '{sheet}' ('{lab}')")
    if vals and all(DATE_VAL.match(v) for v in vals):
        return ev("carry_forward_event_driven", "on_event", f"date value(s) {', '.join(vals[:2])} ('{lab}')")
    if vals and all(v.strip().upper() in ("Y", "N", "YES", "NO", "TRUE", "FALSE") for v in vals):
        return ev("assumption", "on_event", f"switch or flag '{lab}' = {vals[0]}")
    if lab.strip() in ("?", ""):
        return dict(base, type="uncertain", expected_source=None, changes_each_quarter="uncertain", confidence="low",
                    notes=f"No label; path {via}."), True
    if re.search(r"multiple|discount|premium|haircut|weight|wacc|probability|growth rate|\brate\b|%", lab, re.I):
        return ev("assumption", "yes", f"'{lab}' is a valuation assumption")
    if FS_WORDS.search(lab):
        return (dict(base, type="financial_statement", expected_source=f"statements: {lab}", changes_each_quarter="yes",
                     confidence="medium", notes=f"Label '{lab}' is a statement line, but no rule reproduced it from the "
                     f"statements supplied (often an earlier period); path {via}."), False)
    if CAP_WORDS.search(lab):
        return dict(base, type="carry_forward_event_driven", expected_source=None, changes_each_quarter="on_event",
                    confidence="medium", notes=f"Label '{lab}' suggests capitalization data; path {via}. Cadence proposed, not evidenced."), bool(flags)
    if ADJ_WORDS.search(lab) or ASSUMPTION_WORDS.search(lab):
        return dict(base, type="assumption", expected_source=None, changes_each_quarter="yes", confidence="medium",
                    notes=f"Label '{lab}' suggests an analyst input; path {via}. Cadence proposed, not evidenced."), bool(flags)
    return dict(base, type="uncertain", expected_source=None, changes_each_quarter="uncertain", confidence="low",
                notes=f"Label '{lab}': no statement rule reproduces it and the label does not settle its type; path {via}."), True


KEY_METRICS = [("enterprise value", r"enterprise value|\bev\b(?!\s*/)"), ("equity value", r"equity value|total equity"),
               ("fair / fund value", r"fair value|xpv.*value|fund.*value|nav\b|current value"),
               ("applied multiple", r"multiple"), ("EBITDA used", r"ebitda"), ("revenue used", r"revenue|sales"),
               ("net debt / cash / debt", r"net debt|\bcash\b|\bdebt\b"), ("ownership", r"ownership|fully diluted|fd %"),
               ("MOIC", r"moic|investment multiple|multiple of cost"), ("IRR", r"\birr\b")]
LINE = re.compile(r"^(\S+) \[(calc|output|KEY OUTPUT)\] (.*?) (=\S.*?)(?:  \(same pattern x\d+\))? -> (.*?)(?:  FLAG|$)")


CORE = ("enterprise value", "equity value", "fair / fund value")


def tidy_title(t):
    """lowercase, single spaces, simple plurals removed ('Enterprises  Value' -> 'enterprise value'); keeps / and %."""
    words = re.sub(r"[^a-z0-9/%]+", " ", str(t).lower()).split()
    return " ".join(w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in words)


def title_matches(rx, label):
    return bool(re.search(rx, label, re.I) or re.search(rx, tidy_title(label)))
OUT_LINE = re.compile(r"^(.+?![A-Z]{1,3}\d+(?::[A-Z]{1,3}\d+)?) (.*?) = (.*?)  \[upstream inputs: (\d+) from (\d+) sheets\]")


def key_output_candidates(schema):
    """deterministic key outputs: one cell per valuation metric (current period, summary sheet first, de-duplicated,
    max 25) plus true check cells as controls. Returns (suggestions, questions): a question is raised ONLY when a core
    value metric is missing or two different cells tie for it; the AI then picks from a closed list."""
    rows, sheet = [], None
    for l in schema.splitlines():
        if l.startswith("=== SHEET: "):
            sheet = l[len("=== SHEET: "):].rstrip(" =")
            continue
        m = LINE.match(l)
        if m and sheet:
            rng, role, lab, f, v = m.groups()
            rows.append((sheet, rng, role, lab, f, v.split(",")[0].strip()))
    sugg, seen, questions = [], set(), []
    VAR = re.compile(r"variance|var\b|change|chg|diff|delta|vs\.?\b|movement|%", re.I)
    PRIOR = re.compile(r"prior|previous|last|opening|budget|plan", re.I)
    simple_diff = lambda f: re.fullmatch(r"=\$?[A-Z]{1,3}\$?\d+\s*-\s*\$?[A-Z]{1,3}\$?\d+", f.replace(" ", ""))
    is_variance = lambda r: bool(VAR.search(r[3].split("|")[-1]) or (simple_diff(r[4]) and VAR.search(r[3])))

    def num(v):
        try:
            return float(str(v).replace(",", ""))
        except ValueError:
            return None
    pref = lambda r: (0 if re.search(r"current", r[3], re.I) else 1,
                      0 if re.search(r"summary|valuation|lp report|report|output", r[0], re.I) else 1,
                      0 if r[2] != "output" else 1, len(r[1]))
    cell_of = lambda r: f"'{r[0]}'!{r[1].split(':')[-1]}"
    desc = lambda r: f"{cell_of(r)} [{r[2]}] {r[3][:60]} {r[4][:70]} -> {r[5]}"
    metric_rows = [r for r in rows if not is_variance(r) and not PRIOR.search(r[3])]
    found_core = False
    for name, rx in KEY_METRICS:
        hits = sorted([r for r in metric_rows if title_matches(rx, r[3]) and r[5] not in ("(blank)", "0")], key=pref)[:4]
        if not hits:
            continue
        found_core |= name in CORE
        tie = [r for r in hits[1:] if pref(r)[:3] == pref(hits[0])[:3] and r[5] != hits[0][5] and r[0] != hits[0][0]]
        if name in CORE and tie:
            opts = [hits[0]] + tie
            questions.append({"metric": name, "options": {chr(65 + i): desc(r) for i, r in enumerate(opts)},
                              "_cells": {chr(65 + i): (cell_of(r), f"{name}; {r[4]} ({r[3]})") for i, r in enumerate(opts)}})
            continue
        r = hits[0]
        if r[:2] not in seen:
            seen.add(r[:2])
            sugg.append({"cell": cell_of(r), "reason": f"{name}; {r[4]} ({r[3]})"})
    if not found_core:                          # nothing labelled as a value: offer the widest outputs instead
        outs = []
        for l in schema[schema.find("=== OUTPUTS BY SHEET"):schema.find("=== END OF OUTPUTS ===")].splitlines():
            m = OUT_LINE.match(l)
            if m:
                outs.append((int(m.group(4)), m.group(1), m.group(2), m.group(3)))
        outs = sorted(outs, key=lambda x: -x[0])[:6]
        if outs:
            sh_, rest = outs[0][1].rsplit("!", 1)
            questions.append({"metric": "valuation output (no cell is labelled enterprise, equity or fair value)",
                              "options": {chr(65 + i): f"{o[1]} {o[2][:60]} = {o[3][:30]} (upstream inputs: {o[0]})"
                                          for i, o in enumerate(outs)},
                              "_cells": {chr(65 + i): ("'" + o[1].rsplit('!', 1)[0] + "'!" + o[1].rsplit('!', 1)[1].split(':')[-1],
                                                       f"valuation output; {o[2]}") for i, o in enumerate(outs)}})
    ctrl_n = 0
    for r in rows:
        f, lab = r[4], r[3]
        boolean = re.fullmatch(r"=[^=<>]+=[^=<>]+", f) and r[5] in ("True", "False")
        v = num(r[5])
        diff = (re.fullmatch(r"=[^=]+-[^=]+", f) and v is not None and abs(v) < 0.01
                and (re.search(r"check|tie|reconcil|error|proof|balance", lab, re.I) or r[2] == "output"))
        if (boolean or diff) and ctrl_n < 8:
            ctrl_n += 1
            sugg.append({"cell": cell_of(r), "reason": f"check; {f} ({lab})",
                         "control": {"control_type": "boolean", "expected": True, "severity": "blocking"} if boolean else
                                    {"control_type": "numeric", "expected": 0, "absolute_tolerance": 1, "severity": "blocking"}})
    return sugg[:MAX_KEY_OUTPUTS], questions


def auto_concepts(imap, matches, company, overrides):
    blocks = {b["id"]: b for b in matches["blocks"]}
    groups, order = {}, []
    for e in imap["inputs"]:
        in_scope = (e.get("material") and e.get("type") != "not_material") or e.get("reporting_required") == "yes"
        if not in_scope:
            continue
        spec = (blocks.get(e["id"]) or {}).get("execution_spec")
        if e.get("type") == "reference_data" and not spec:
            key = (f"comp set {e['sheet']}", None, "reference_data")          # a comp set is one concept
        else:
            key = (norm_label(e["label"]), json.dumps(spec, sort_keys=True) if spec else None, e.get("type"))
        if key not in groups:
            groups[key] = {"entries": [], "spec": spec, "type": e.get("type"),
                           "label": key[0] if key[0].startswith("comp set") else e["label"]}
            order.append(key)
        groups[key]["entries"].append(e)
    used, out = set(), []
    prefix = {"financial_statement": "fs", "assumption": "asm", "carry_forward_event_driven": "cap", "constant": "const",
              "reference_data": "ref", "prior_period": "prior", "uncertain": "unk", "not_material": "rpt"}
    for key in order:
        g = groups[key]
        slug = re.sub(r"[^a-z0-9]+", "_", norm_label(g["label"]).replace("#", "n")).strip("_")[:40] or "unlabelled"
        cid = f"{prefix.get(g['type'], 'x')}.{slug}"
        n = 2
        while cid in used:
            cid = f"{prefix.get(g['type'], 'x')}.{slug}_{n}"; n += 1
        used.add(cid)
        targets = [e["id"] for e in g["entries"]]
        multi = any(":" in t.split("!", 1)[1] for t in targets)
        c = {"concept_id": cid, "name": g["label"] if g["label"] != "?" else f"Unlabelled input {targets[0]}",
             "entity": company or "UNCERTAIN", "targets": targets, "questions": []}
        t, sp = g["type"], g["spec"]
        if sp and t in ("financial_statement", "reference_data", "prior_period", "not_material"):
            c.update(write_mode="roll_window" if multi else "replace_period_value",
                     period_rule=OP_PERIOD[sp["operation"]](sp), missing_source_behavior="block_and_flag")
        elif t == "reference_data":
            c.update(write_mode="carry_forward_event_driven", period_rule="not_periodic", missing_source_behavior="carry_forward_and_flag",
                     questions=["Comparable set: carried forward; review the set (add or remove companies or deals) when due."])
        elif t == "prior_period":
            c.update(write_mode="manual_input", period_rule="not_periodic", missing_source_behavior="carry_forward_and_flag",
                     questions=["Prior-period value: in a refresh it should become last quarter's current value. Confirm which "
                                "current-period cell it comes from (a backtest will test this)."])
        elif t in ("financial_statement", "not_material"):
            c.update(write_mode="manual_input", period_rule="uncertain", missing_source_behavior="carry_forward_and_flag",
                     questions=["Expected in the statements, but no rule reproduces it: name the statement line, or confirm it is entered by hand."])
        elif t == "carry_forward_event_driven":
            c.update(write_mode="carry_forward_event_driven", period_rule="not_periodic", missing_source_behavior="carry_forward_and_flag")
        elif t == "constant":
            c.update(write_mode="carry_forward", period_rule="not_periodic", missing_source_behavior="carry_forward_and_flag")
        elif t == "assumption" and re.search(r"(months?|days?|years?|periods?) (until|to|remaining|left)|remaining (term|life)|"
                                             r"time to (maturity|expiry)|\bage\b|elapsed|since (issue|investment)", g["label"], re.I):
            c.update(write_mode="manual_input", period_rule="not_periodic", missing_source_behavior="block_and_flag",
                     questions=["Counts time, so it changes every period: a carried-forward value would be stale. Make it a "
                                "formula in the workbook (from the dates), or give its value each quarter."])
        elif t == "assumption":
            c.update(write_mode="manual_input", period_rule="not_periodic", missing_source_behavior="carry_forward_and_flag")
        else:
            c.update(write_mode="manual_input", period_rule="uncertain", missing_source_behavior="carry_forward_and_flag",
                     questions=["Meaning unknown: what does this input represent, where does it come from, and how often does it change?"])
        out.append(c)
    for ov in (overrides or {}).get("concepts", []):
        hit = next((c for c in out if c["concept_id"] == ov.get("concept_id") or set(ov.get("targets", [])) & set(c["targets"])), None)
        if hit:
            hit.update({k: v for k, v in ov.items() if k != "targets" or v})
        else:
            out.append(ov)
    return {"concepts": out}


def onboard_review(r, prof):
    """short, ranked list of what a person should look at after onboarding (impact x uncertainty); routine items omitted."""
    ents, kos = r.get("entries", {}), len(r["skel"].get("key_outputs") or []) or 1
    rv = {}

    def item(key, pr, what, why):
        if key not in rv or rv[key][0] < pr:
            rv[key] = (round(pr, 2), what, why)
    for c in r.get("controls", []):
        if c["result"] != "PASS":
            item(c["cell"], 3.0 if c["severity"] == "blocking" else 1.8, c["cell"],
                 f"control {c['result']} on the uploaded workbook (value {c['value']}, expected {c['expected']})")
    for b in r.get("blocking", []):
        item(b, 3.0, "blocking issue", b)
    for lst, unc, tag in ((r.get("unresolved", []), 1.0, "meaning unresolved"), (r.get("low_conf", []), 0.7, "low confidence")):
        grp = {}
        for i in lst:
            grp.setdefault((ents[i]["sheet"], ents[i]["type"]), []).append(i)
        for (sh_, ty), ids in grp.items():
            if len(ids) >= 3:
                item(f"grp {sh_} {ty} {tag}", 2.5 * unc, f"{sh_}: {len(ids)} blocks ({ids[0]} ... {ids[-1]})", f"{tag}: classified {ty}")
                continue
            for i in ids:
                e = ents[i]
                item(i, (2 + min(1.0, len(e.get("feeds_key_outputs") or []) / kos)) * unc, f"{i} ({e['label']})",
                     f"{tag}: {e['type']}. {(e.get('notes') or '')[:100]}")
    manual = []
    for c in prof["concepts"]:
        for q in c.get("questions") or []:
            if q.startswith("Counts time"):
                item(c["concept_id"], 2.4, f"{c['name']} ({', '.join(c['targets'][:3])})", q)
            elif q.startswith("Prior-period"):
                item(c["concept_id"], 1.5, f"{c['name']} ({', '.join(c['targets'][:3])})", q)
            elif q.startswith("Comparable set"):
                continue
            else:
                for t in c["targets"]:
                    item(t, 3.0 if c["period_rule"] == "uncertain" else 1.2, f"{t} ({c['name']})", q)
        sp = c.get("execution") or {}
        n_rep = sum(1 for v in (c.get("offset_basis") or {}).values() if v == "reproduced")
        src = norm_label((sp.get("source") or {}).get("label", ""))
        if c["status"] == "EXECUTABLE" and n_rep == 1 and src and src not in norm_label(c["name"]) \
                and norm_label(c["name"]) not in src:
            item(c["concept_id"], 1.6, f"{c['name']} ({', '.join(c['targets'][:2])})",
                 f"rule proven by one number only, from a differently named line '{sp['source']['label']}': confirm it is the right source")
        if c["status"] == "EXCEPTION":
            item(c["concept_id"], 3.0, c["name"], "automated input without a runnable rule: give the rule in words")
        elif c["status"] == "EXECUTABLE_UNVERIFIED":
            item(c["concept_id"], 1.8, c["name"], "analyst-stated rule not yet reproduced from the statements")
        elif c["write_mode"] == "manual_input" and c["period_rule"] != "uncertain":
            manual.append(c["name"])
    if manual:
        item("manual", 0.6, "manual inputs each quarter", f"{len(manual)} values carried forward and flagged unless given: {', '.join(manual[:12])}")
    for x in prof.get("layout_checks", []):
        item("pack " + x[:40], 0.6 if any(w in x for w in ("layout", "same month", "missing", "no date")) else 0.4, "statement pack", x)
    return sorted(rv.values(), key=lambda x: -x[0])


def onboard(a):
    out = a.out
    os.makedirs(out, exist_ok=True)
    resolve_inputs(a, out, ["workbook", "statements"])
    bundle = resolve(a.bundle, out)
    if a.bundle and not bundle:
        print(f"PIPELINE ERROR: bundle not found: {a.bundle} (upload <company_id>_company.zip)"); sys.exit(1)
    tmp = os.path.join(a.work, "_bundle_in"); os.makedirs(a.work, exist_ok=True)
    B = read_bundle(bundle, tmp) if bundle else None
    cp = load(B["cp"]) if B and B["cp"] else None
    name = a.company or (cp or {}).get("display_name") or (entity_of(B["prof"]) if B else None)
    cid = company_slug(a.company_id) if a.company_id else ((cp or {}).get("company_id") or company_slug(name))
    if not cid:
        print("PIPELINE ERROR: give --company \"<display name>\" (the company_id is derived from it once, then fixed)"); sys.exit(1)
    cp = cp or new_cp(cid, name)
    cp["company_id"], cp["display_name"] = cid, cp.get("display_name") or name
    W = work_dir(a, cid)
    reuse_path = None
    if B and not a.fresh:
        shutil.copy(B["prof"], os.path.join(W, "mapping_profile.json"))      # earlier per-concept approvals carry over
        reuse_path = shutil.copy(B["imap"], os.path.join(W, "reuse_input_map.json"))
    elif os.path.exists(os.path.join(W, "mapping_profile.json")):
        os.remove(os.path.join(W, "mapping_profile.json"))       # fresh structure: only the decisions log is carried over
    reuse = load(reuse_path)
    wb, stem = a.workbook, stem_of(a.workbook)
    skel = os.path.join(W, f"{stem}_inputs_skeleton.json")
    proposals = []

    # ---- key outputs: chosen by rule once, reused afterwards. A tie between different cells for a core value metric
    # is NOT asked now: every tied candidate is kept provisionally, the whole onboarding runs, and the tie is asked at the
    # end together with any unclear inputs - one AI question per onboarding at most.
    answers = parse_json_arg(a.answers)
    questions = []
    if reuse:
        items = ko_items_from_imap(reuse)
    else:
        rc, o = sh([S("extract_schema.py"), wb, "--out", W])
        if "EXTRACTION_ERROR" in o:
            fail(o, "extract (discovery)")
        schema = open(os.path.join(W, f"{stem}_schema.md"), encoding="utf-8").read()
        items, questions = key_output_candidates(schema)
        if questions and answers is None:
            have = {i["cell"].replace("'", "") for i in items}
            prov = [{"cell": cell, "reason": why + " (tied candidate, provisional)"} for q in questions
                    for cell, why in q["_cells"].values() if cell.replace("'", "") not in have]
            items = prov + items                       # first, so the cap never drops a candidate
        elif questions:
            picks = answers.get("key_outputs") or {}
            for q in questions:
                pick = str(picks.get(q["metric"], "none")).strip().upper()[:1]
                if pick in q["_cells"]:
                    cell, why = q["_cells"][pick]
                    items.insert(0, {"cell": cell, "reason": why + " (AI pick)"})
                    proposals.append(("key_output_pick", f"key_output:{cell.replace(chr(39), '')}", {"metric": q["metric"], "cell": cell},
                                      f"AI picked {cell} for {q['metric']} from options {', '.join(q['_cells'])}"))
                else:
                    proposals.append(("key_output_pick", f"key_output:{q['metric']}", {"metric": q["metric"], "cell": None},
                                      f"AI found no cell for {q['metric']}"))
    items = apply_ko_decisions(items, cp)
    if not items:
        print("PIPELINE ERROR: no key output could be chosen; name the valuation output cell (e.g. \"key output is "
              "'Valuation Summary'!F25\") and run amend."); sys.exit(1)
    ko_path = dump({"key_outputs": items}, os.path.join(W, "key_outputs.json"))
    rc, o = sh([S("extract_schema.py"), wb, "--out", W, "--key-outputs-file", ko_path])
    if "EXTRACTION_ERROR" in o:
        fail(o, "extract (final)")
    idx = os.path.join(W, "sources_index.json")
    rc, o = sh([S("index_sources.py")] + a.statements + ["--out", idx])
    if "INDEX_ERROR" in o:
        fail(o, "index statements")
    mt = os.path.join(W, "matches.json")
    rc, o = sh([S("match_values.py"), wb, skel, idx, "--out", mt] + (["--period-end", a.period_end] if a.period_end else []))
    if "MATCH_ERROR" in o:
        fail(o, "rule discovery")
    sk, matches = load(skel), load(mt)
    blocks = {b["id"]: b for b in matches["blocks"]}

    # ---- classifications: evidence first; the AI answers only the blocks evidence cannot settle
    sugg, need = {}, []
    for e in sk["inputs"]:
        if not e["material"]:
            continue
        s_, j = suggest(e, blocks.get(e["id"]))
        sugg[e["id"]] = s_
        if j:
            need.append(e["id"])
    decided = {d["item"][5:] for d in active(cp, "classification")}
    need = [i for i in need if i not in decided]
    if not reuse and (need or questions) and answers is None:
        ent = {e["id"]: e for e in sk["inputs"]}
        TYPES = ("financial_statement, assumption, prior_period, constant, carry_forward_event_driven, reference_data, uncertain")
        L = ["JUDGMENT NEEDED (the only AI step; everything else is done). Answer from what is shown here, then re-run the "
             "SAME command adding: --answers '<one-line JSON>'"]
        if questions:
            L.append("Key outputs: pick the current-period cell on the valuation summary (not prior-period, variance or display "
                     "cells); one letter per metric, or \"none\".")
            for n, q in enumerate(questions, 1):
                L.append(f"K{n} {q['metric']}: " + " | ".join(f"{k}) {v}" for k, v in q["options"].items()))
        if need:
            L.append(f"Inputs: classify each as one of {TYPES}. Use uncertain when the label and path do not settle it; never guess.")
            for n, i in enumerate(need, 1):
                e = ent[i]
                path = " -> ".join(next(iter((e.get("paths_to_key_outputs") or {}).values()), [])[:4])
                L.append(f"C{n} {i}: label '{e['label']}' header '{e.get('header') or ''}' values {e['sample_values'][:3]} "
                         f"path {path}{' flags ' + '; '.join(e['flags']) if e['flags'] else ''} (suggested {sugg[i]['type']})")
        L.append('Answer format: {"key_outputs": {"<metric>": "<letter>"}, "classifications": [{"id": "<id>", "type": "<type>", '
                 '"confidence": "high|medium|low", "notes": "<one sentence citing label and path, no apostrophes>"}]}')
        dump({"questions": [{k: v for k, v in q.items() if k != "_cells"} for q in questions], "inputs": need},
             os.path.join(W, "judgment.json"))
        print("\n".join(L))
        sys.exit(10)
    if answers is not None:
        dump(answers, os.path.join(W, "answers_used.json"))
    ca = None
    merged = dict(sugg)
    for c in (answers or {}).get("classifications", []) if not reuse else []:
        if c.get("id") in merged:
            merged[c["id"]] = {**merged[c["id"]], **{k: v for k, v in c.items() if v is not None}, "reviewed_by": None}
            proposals.append(("classification", f"cell:{c['id']}", {"type": merged[c["id"]]["type"]},
                              f"AI classified {c['id']} as {merged[c['id']]['type']} ({merged[c['id']].get('confidence')})"))
    full = dump({"classifications": list(merged.values())}, os.path.join(W, "classifications_full.json"))
    base_entries = {e["id"]: e for e in (reuse or {}).get("inputs", [])}
    dec_cls, off_path = [], []
    for d in active(cp, "classification"):
        i = d["item"][5:]
        if i not in sugg:
            off_path.append(f"decision #{d['id']} targets {i}, which no longer feeds a key output")
            continue
        basis = {k: v for k, v in (base_entries.get(i) or merged[i]).items()
                 if k in ("type", "expected_source", "changes_each_quarter", "confidence", "notes", "reviewed_by")}
        ch = {k: v for k, v in d["change"].items() if k in ("type", "expected_source", "changes_each_quarter", "confidence")}
        if ch.get("type") == "carry_forward_event_driven":
            ch.setdefault("changes_each_quarter", "on_event")
        dec_cls.append({"id": i, **basis, "confidence": "high", **ch,
                        "notes": f"analyst (decision #{d['id']}): {d['said'][:200]}", "reviewed_by": d.get("by")})
    files = ([reuse_path] if reuse else []) + ([full] if not reuse else [])
    if dec_cls:
        files.append(dump({"classifications": dec_cls}, os.path.join(W, "decision_classifications.json")))
    imap = os.path.join(W, "input_map.json")
    sh([S("apply_classifications.py"), skel] + files + ["--out", imap])
    rc, o = sh([S("validate_input_map.py"), skel, imap])
    if "STATUS: INVALID" in o:
        fail(o, "input map validation (fix classifications.json and re-run)")
    if a.debug:
        sh([S("build_report.py"), skel, imap, "--out", os.path.join(W, f"{stem}_run_report.md")])
    overrides = {"concepts": [{"concept_id": d["item"][8:], **d["change"]} for d in active(cp, "rule")]}
    con = auto_concepts(load(imap), matches, cp["display_name"], overrides)
    cpath = dump(con, os.path.join(W, "concepts.json"))
    rc, o = sh([S("build_profile.py"), imap, mt, cpath, "--out-dir", W])
    if "PROFILE STATUS: INVALID" in o or "PROFILE_ERROR" in o:
        fail(o, "profile build (a rule correction is malformed: see references/profile-fields.md)")
    prof_path = os.path.join(W, "mapping_profile.json")
    prof = load(prof_path)
    from validate_input_map import evaluate
    r = evaluate(skel, imap)
    review = onboard_review(r, prof) + [(2.0, "decision", x) for x in off_path]
    review.sort(key=lambda x: -x[0])

    # ---- company profile: version, named review, decisions log, open items
    im = load(imap)
    h = hashlib.sha256(json.dumps([im.get("key_outputs"), im.get("controls"),
                                   sorted((e["id"], e.get("type")) for e in im["inputs"]),
                                   sorted(c["approval_basis_hash"] for c in prof["concepts"])], default=str).encode()).hexdigest()[:16]
    if h != cp.get("profile_hash"):
        cp["profile_version"], cp["profile_hash"] = cp.get("profile_version", 0) + 1, h
    cp["period_end"] = prof.get("period_end")
    for kind, item_, change, said in proposals:
        add_decision(cp, kind, item_, change, said, "agent", status="proposed")
    pend = (cp.get("review") or {}).pop("pending_by", None)
    if pend:
        cp["review"] = {"approved_by": pend, "approved_on": TODAY(), "profile_version": cp["profile_version"]}
        for d in cp["decisions"]:
            if d["status"] == "proposed":
                d["status"], d["confirmed_by"] = "confirmed", pend
    cp.update(status=prof["status"], period_end=prof.get("period_end"),
              open_items=[f"{w}: {y}" for _, w, y in review],
              onboarded_from={"workbook": os.path.abspath(wb), "statements": [os.path.abspath(s) for s in a.statements],
                              "period_end": a.period_end, "date": TODAY()})
    bpath = write_bundle(out, cp, imap, prof_path, W)

    # ---- report (the only output the agent posts)
    kos, ctrls = im.get("key_outputs", []), {c["cell"]: c for c in im.get("controls", [])}
    reasons = im.get("key_output_reasons", {})
    counts = {}
    for e in im["inputs"]:
        if e.get("type") != "not_material":
            counts[e["type"]] = counts.get(e["type"], 0) + 1
    st = {}
    for c in prof["concepts"]:
        k = "rules" if c["status"] in ("EXECUTABLE", "EXECUTABLE_UNVERIFIED") else ("exceptions" if c["status"] == "EXCEPTION" else
             "carried forward" if c["write_mode"].startswith("carry") else "manual each quarter")
        st[k] = st.get(k, 0) + 1
    cres = [c for c in r.get("controls", [])]
    print(f"ONBOARD STATUS: {prof['status']} | {cp['display_name']} (company_id {cid}) | profile v{cp['profile_version']} | "
          f"{approval_text(cp)}")
    print(f"Key outputs ({len(kos)}, of which controls {len(ctrls)}):")
    for c in kos:
        print(f"- {c}{' [control]' if c in ctrls else ''}: {(reasons.get(c) or '')[:110]}")
    print(f"Inputs: {sum(counts.values())} material blocks (" + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) +
          f") | concepts {len(prof['concepts'])}: " + ", ".join(f"{v} {k}" for k, v in st.items()))
    if cres:
        print(f"Controls on the uploaded workbook: {sum(1 for c in cres if c['result'] == 'PASS')} pass, "
              f"{sum(1 for c in cres if c['result'] != 'PASS')} fail")
    if proposals:
        print("AI proposals this run (confirm or correct): " + "; ".join(p[3] for p in proposals))
    if active(cp, "classification") or active(cp, "rule") or active(cp, "key_output"):
        print(f"Analyst decisions applied: {len(active(cp, 'classification')) + len(active(cp, 'rule')) + len(active(cp, 'key_output'))}")
    print(f"Review ({len(review)}):" + ("" if review else " nothing needs review."))
    for i, (_, w, y) in enumerate(review[:15], 1):
        print(f"{i}. {w} - {y}")
    if len(review) > 15:
        print(f"(+{len(review) - 15} more in company_profile.json open_items)")
    for l in sp_lines(cid, "company", [bpath], folder=cp["profile_version"] <= 1):
        print(l)
    print("NEXT: carry out the SHAREPOINT lines, then post this report from ONBOARD STATUS to the end of Review unchanged. Stop.")
    sys.exit(0)


# ------------------------------------------------------------------------------------------ run / check / amend
def open_company(a, out):
    bundle = resolve(a.bundle, out)
    if not bundle:
        print(f"PIPELINE ERROR: company bundle not found{': ' + a.bundle if a.bundle else ''} "
              "(upload <company_id>_company.zip from Valuations/<company_id>/company/)"); sys.exit(1)
    tmp = os.path.join(a.work, "_bundle_in"); os.makedirs(a.work, exist_ok=True)
    B = read_bundle(bundle, tmp)
    if not (B["imap"] and B["prof"]):
        print("PIPELINE ERROR: the bundle has no input map or mapping profile; re-onboard the company."); sys.exit(1)
    cp = load(B["cp"]) if B["cp"] else None
    if not cp:                                   # an older bundle: give it a fixed company_id once
        name = getattr(a, "company", None) or entity_of(B["prof"]) or stem_of(bundle).split("_company")[0]
        cid = company_slug(getattr(a, "company_id", None) or name)
        cp = new_cp(cid, name)
        cp.update(profile_version=1, status=(load(B["prof"]) or {}).get("status"), period_end=(load(B["prof"]) or {}).get("period_end"))
    W = work_dir(a, cp["company_id"])
    imap, prof = shutil.copy(B["imap"], os.path.join(W, "input_map.json")), shutil.copy(B["prof"], os.path.join(W, "mapping_profile.json"))
    return bundle, B["legacy"], cp, W, imap, prof


def run(a):
    out = a.out
    os.makedirs(out, exist_ok=True)
    resolve_inputs(a, out, ["workbook", "statements", "actual"])
    bundle, legacy, cp, W, imap, prof = open_company(a, out)
    cid = cp["company_id"]
    idx = os.path.join(W, "sources_index.json")
    rc, o = sh([S("index_sources.py")] + a.statements + ["--out", idx, "--expect-layout", prof])
    if "INDEX_ERROR" in o:
        fail(o, "index statements")
    plan = os.path.join(W, "write_plan.json")
    args = [S("plan_writes.py"), "--mode", a.mode, "--workbook", a.workbook, "--input-map", imap, "--profile", prof,
            "--sources-index", idx, "--out", plan]
    for flag, v in (("--actual", a.actual), ("--period-end", a.period_end), ("--manual", a.manual)):
        if v:
            args += [flag, v]
    rc, o = sh(args)
    ps = line(o, "PLAN STATUS")
    print(f"PLAN STATUS: {ps}")
    if ps.startswith("REFUSED") or ps.startswith("BLOCKED") or "PLAN_ERROR" in o:
        for l in o.splitlines():
            if l.startswith("- EXCEPTION") or (l.startswith("- ") and ps.startswith("REFUSED")) or "PLAN_ERROR" in l:
                m = re.match(r"- EXCEPTION (\S+) \[([^\]]+)\]", l)
                hx = history(cp, m.group(1), m.group(2)) if m else ""
                print(l + (f" (previous {hx})" if hx else ""))
        if "fingerprint" in o:
            print("ROUTE: the workbook structure changed since onboarding -> re-onboard with --bundle --fresh "
                  "(structure is rediscovered; the decisions log is re-applied).")
        print("NEXT: stop. Post the lines above as one list; do not do the Excel step.")
        sys.exit(3)
    for l in o.splitlines():
        if l.startswith("note:"):
            print(l)
    pl = load(plan)
    q = quarter_of(pl.get("period_end"))
    base = f"{cid}_{q}_{a.mode}"
    draft = os.path.join(out, f"{base}.xlsx")
    rc, o2 = sh([S("apply_writes.py"), "--workbook", a.workbook, "--plan", plan, "--out", draft])
    if "APPLY_ERROR" in o2:
        fail(o2, "write draft")
    wlog = draft.rsplit(".", 1)[0] + "_write_log.json"
    rl = load(wlog)
    os.replace(wlog, os.path.join(W, os.path.basename(wlog)))
    approved = (cp.get("review") or {}).get("approved_by")
    if a.mode == "refresh" and not approved:
        rl["notes"].append("company profile not yet approved by a named reviewer (recorded, not required)")
    mfile = (load(a.manual) or {}) if a.manual else {}
    manual = mfile.get("values", {})
    im = load(imap)
    cells = list(dict.fromkeys(im.get("key_outputs", []) + [c["cell"] for c in im.get("controls", [])]))
    rl.update(run_log_version=2, company_id=cid, display_name=cp["display_name"], quarter=q, status="awaiting_recalc",
              created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              profile_version=cp.get("profile_version"), profile_approval=approval_text(cp),
              sharepoint_file=f"Valuations/{cid}/{q}/{os.path.basename(draft)}", recalc_cells=cells,
              inputs={"workbook": os.path.basename(a.workbook), "statements": [os.path.basename(s) for s in a.statements],
                      "bundle": os.path.basename(bundle), "actual": os.path.basename(a.actual) if a.actual else None,
                      "manual_inputs": manual, "manual_inputs_said": mfile.get("said"), "manual_inputs_by": mfile.get("by")},
              paths={"workbook": os.path.abspath(a.workbook), "statements": [os.path.abspath(s) for s in a.statements],
                     "bundle": os.path.abspath(bundle), "actual": os.path.abspath(a.actual) if a.actual else None,
                     "draft": os.path.abspath(draft), "period_end_arg": a.period_end},
              check=None, review=[], reviewed_by=None, reviewed_on=None)
    rlp = dump(rl, os.path.join(out, f"{base}_run_log.json"))
    if legacy:
        up = write_bundle(out, cp, imap, prof, W)
        print(f"note: older company bundle upgraded to {os.path.basename(up)} (company_id {cid}); it is saved below.")
        for l in sp_lines(cid, "company", [up]):
            print(l)
    for l in sp_lines(cid, q, [draft]):
        print(l)
    print(f"RECALC: Run script from SharePoint library | file: the Id that Create file returned for {os.path.basename(draft)} "
          f"| cells: {json.dumps(cells)}")
    print("THEN: python scripts/pipeline.py check --values - <<'JSON'\n<the Run script result, exactly as returned>\nJSON")
    print(f"IF RUN SCRIPT FAILS: give the user {os.path.basename(draft)} with references/excel-step.md; when they upload the "
          f"saved file run: python scripts/pipeline.py check --saved \"<file name>\"")
    print("NEXT: carry out the SHAREPOINT lines, then the RECALC line, then the THEN command. No other steps.")
    sys.exit(20)


def latest_run_log(out, cid=None, status=None):
    cands = []
    for d in (out, UPLOADS):
        cands += glob.glob(os.path.join(d, "**", "*_run_log*.json"), recursive=True) if os.path.isdir(d) else []
    ok = []
    for p_ in cands:
        rl = load(p_) or {}
        if (not cid or rl.get("company_id") == cid) and (not status or rl.get("status") == status):
            ok.append(p_)
    return max(ok, key=os.path.getmtime) if ok else None


def check(a):
    out = a.out
    rlp = resolve(a.run_log, out) if a.run_log else (latest_run_log(out, status="awaiting_recalc")
                                                    or latest_run_log(out, status="awaiting_excel") or latest_run_log(out))
    if not rlp:
        print("PIPELINE ERROR: no run log found. In a new chat upload the <company>_<quarter>_<mode>_run_log.json saved at the "
              "Excel step, the company bundle and the base workbook, then run check again."); sys.exit(1)
    rl = load(rlp)
    P = rl.get("paths", {})
    base = resolve(P.get("workbook"), out) or resolve(rl["inputs"]["workbook"], out)
    a.bundle = P.get("bundle") if P.get("bundle") and os.path.exists(P["bundle"]) else rl["inputs"]["bundle"]
    missing = [n for n, v in (("base workbook " + rl["inputs"]["workbook"], base), ("company bundle " + rl["inputs"]["bundle"],
                                                                                   resolve(a.bundle, out))) if not v]
    actual = resolve(P.get("actual"), out) or resolve(rl["inputs"].get("actual"), out) if rl.get("mode") == "backtest" else None
    if rl.get("mode") == "backtest" and not actual:
        missing.append("actual workbook " + str(rl["inputs"].get("actual")))
    values = parse_json_arg(a.values) if a.values else None
    saved = resolve(a.saved, out) if a.saved else None
    if not values and not saved:
        missing.append("the Run script result (--values) or the saved workbook (--saved)")
    if missing:
        print("PIPELINE ERROR: upload these files, then run check again: " + ", ".join(missing)); sys.exit(1)
    bundle, legacy, cp, W, imap, prof = open_company(a, out)
    res_path = os.path.join(W, "check.json")
    args = [S("check_result.py"), "--mode", rl["mode"], "--base", base, "--input-map", imap, "--plan", rlp, "--out-json", res_path]
    args += ["--values-json", dump(values, os.path.join(W, "recalc_values.json"))] if values else ["--result", saved]
    draft = resolve(P.get("draft"), out)
    if draft:
        args += ["--draft", draft]
    if actual:
        args += ["--actual", actual]
    if a.debug:
        args += ["--report-md", os.path.join(W, f"{stem_of(rlp)}_check_report.md")]
    rc, o = sh(args)
    if "CHECK_ERROR" in o:
        fail(o, "check")
    res = load(res_path)
    for r_ in res["review"]:
        hx = history(cp, r_.get("cell"), r_.get("concept"))
        if hx:
            r_["why"] += f" (previous {hx})"
    status, c = res["status"], res["counts"]
    rl.update(status=status, checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              saved_file=os.path.basename(saved) if saved else rl.get("sharepoint_file"),
              check={k: res[k] for k in ("checks", "counts", "key_outputs", "controls", "new_errors", "historical_cells_kept")},
              review=[{"item": r_["item"], "why": r_["why"]} for r_ in res["review"]])
    dump(rl, rlp)
    not_calc = not res["checks"].get("Excel recalculated the file", True)
    ko = (f"key outputs {c['key_outputs_ok']}/{c['key_outputs']} match" if rl["mode"] != "refresh" else
          f"key outputs {c['key_outputs']} ({sum(1 for k in res['key_outputs'] if k.get('flag'))} moved beyond threshold)")
    print(f"CHECK STATUS: {status} | {rl['display_name']} ({rl['company_id']}) {rl['quarter']} {rl['mode']} | cells written "
          f"{c['written']}/{c['cells']} | {ko} | controls {c['controls_pass']}/{c['controls']} pass | new Excel errors {len(res['new_errors'])}"
          + (f" | {res['historical_cells_kept']} earlier-period cells kept from the workbook (not rebuilt)" if res["historical_cells_kept"] else ""))
    for k, ok in res["checks"].items():
        if not ok and k != "no variance flags":                  # variance is a review item, not a failure
            print(f"check FAIL: {k}")
    print(f"Review ({len(res['review'])}):" + ("" if res["review"] else " nothing needs review."))
    for i, r_ in enumerate(res["review"][:15], 1):
        print(f"{i}. {r_['item']} - {r_['why']}")
    if len(res["review"]) > 15:
        print(f"(+{len(res['review']) - 15} more in {os.path.basename(rlp)})")
    if not_calc:
        print("NEXT: the workbook was not recalculated. Give the user the draft with references/excel-step.md and, when they "
              "upload the saved file, run check --saved. Save nothing now. Stop.")
        sys.exit(0)
    files = [rlp]
    if saved and rl["mode"] == "refresh" and status != "DRAFT_BLOCKED":
        final = os.path.join(out, f"{rl['company_id']}_{rl['quarter']}_{rl['mode']}.xlsx")
        if os.path.abspath(saved) != os.path.abspath(final):
            shutil.copy(saved, final)
        files.insert(0, final)
    if values:
        print(f"Workbook: {rl.get('sharepoint_file')} (recalculated in SharePoint)")
    for l in sp_lines(rl["company_id"], rl["quarter"], files, folder=False):
        print(l)
    print("NEXT: carry out the SHAREPOINT lines, then post this report from CHECK STATUS to the end of Review unchanged. Stop.")
    sys.exit(0)


def amend(a):
    """one entry point for everything the user says after a run: corrections, confirmations, approvals, manual inputs.
    Company-level changes go into the decisions log and re-run onboarding; the log is re-applied on every onboarding."""
    out = a.out
    ch = parse_json_arg(a.changes) if a.changes else load(os.path.join(out, "changes.json"))
    if not ch or not ch.get("said"):
        print("PIPELINE ERROR: give --changes '<one-line JSON>' with at least \"said\" (the user's exact words); "
              "see SKILL.md changes format."); sys.exit(1)
    by, said = (ch.get("by") or None), ch["said"]
    if not a.bundle:
        cands = [p_ for p_ in glob.glob(os.path.join(out, "*_company.zip"))
                 if not ch.get("company_id") or os.path.basename(p_).startswith(ch["company_id"] + "_")]
        a.bundle = max(cands, key=os.path.getmtime) if cands else None
    a.company = a.company_id = None
    bundle, legacy, cp, W, imap, prof = open_company(a, out)
    cid, logged, notes = cp["company_id"], [], []
    for c in ch.get("classifications", []):
        logged.append(add_decision(cp, "classification", f"cell:{c['id']}", {k: v for k, v in c.items() if k != "id"}, said, by))
    concepts = (load(prof) or {}).get("concepts", [])
    for r_ in ch.get("rules", []):
        cid_ = r_.get("concept_id")
        if not cid_ and r_.get("cell"):                  # a rule named by a cell: find the concept that owns it
            want = r_["cell"].replace("'", "")
            cid_ = next((c["concept_id"] for c in concepts for t in c["targets"]
                         if want in {ref(k) for k in cells_of(t)} or want == t), None)
        if not cid_:
            print(f"PIPELINE ERROR: rule for {r_.get('cell') or r_} matches no concept; name a target cell of the input."); sys.exit(1)
        logged.append(add_decision(cp, "rule", f"concept:{cid_}", {k: v for k, v in r_.items() if k not in ("concept_id", "cell")}, said, by))
    ko = ch.get("key_outputs") or {}
    for it in ko.get("add", []) + [dict(x, action="add") for x in ch.get("controls", [])]:
        logged.append(add_decision(cp, "key_output", f"key_output:{it['cell'].replace(chr(39), '')}",
                                   {"action": "add", "cell": it["cell"], "reason": it.get("reason"), "control": it.get("control")}, said, by))
    for cell in ko.get("remove", []):
        logged.append(add_decision(cp, "key_output", f"key_output:{cell.replace(chr(39), '')}", {"action": "remove", "cell": cell}, said, by))
    company_change = bool(logged)
    if ch.get("approve_profile"):
        if not by:
            print("PIPELINE ERROR: an approval needs the approver's name as the user stated it (\"by\")."); sys.exit(1)
        logged.append(add_decision(cp, "approval", "profile", {"profile_version": "next" if company_change else cp.get("profile_version")}, said, by))
        if company_change:
            cp.setdefault("review", {})["pending_by"] = by
        else:
            cp["review"] = {"approved_by": by, "approved_on": TODAY(), "profile_version": cp.get("profile_version")}
            for d in cp["decisions"]:
                if d["status"] == "proposed":
                    d["status"], d["confirmed_by"] = "confirmed", by
    rlp = resolve(a.run_log, out) if a.run_log else latest_run_log(out, cid)
    saves = []
    if ch.get("review_period"):
        if not by:
            print("PIPELINE ERROR: a period review needs the reviewer's name as the user stated it (\"by\")."); sys.exit(1)
        if not rlp:
            print("PIPELINE ERROR: no run log for this company to mark as reviewed."); sys.exit(1)
        rl = load(rlp)
        rl.update(reviewed_by=by, reviewed_on=TODAY(), review_note=said)
        dump(rl, rlp)
        notes.append(f"{rl['quarter']} {rl['mode']} marked reviewed by {by}")
        saves += sp_lines(cid, rl["quarter"], [rlp], folder=False)
    bpath = write_bundle(out, cp, imap, prof, W)
    tidy(out, W, ["changes.json"])
    for n in logged:
        d = next(x for x in cp["decisions"] if x["id"] == n)
        print(f"DECISION LOGGED: #{n} {d['kind']} {d['item']} (by {by or 'unnamed'})")
    for n in notes:
        print(f"NOTE: {n}")
    if company_change:
        src = cp.get("onboarded_from") or {}
        wb = resolve(src.get("workbook"), out)
        stm = [resolve(s, out) for s in src.get("statements", [])]
        if not wb or not all(stm):
            print("NEXT: decisions are saved in the bundle. To apply them, upload the onboarding workbook and statements and run "
                  f"onboard with --bundle {os.path.basename(bpath)}.")
            for l in sp_lines(cid, "company", [bpath], folder=False):
                print(l)
            sys.exit(0)
        ob = argparse.Namespace(out=out, work=a.work, debug=a.debug, workbook=wb, statements=stm, company=None, company_id=None,
                                bundle=bpath, period_end=src.get("period_end"), fresh=False, answers=None)
        onboard(ob)
    if ch.get("manual_inputs"):
        mp = dump({"values": ch["manual_inputs"], "said": said, "by": by}, os.path.join(W, "manual_inputs.json"))
        rl = load(rlp) if rlp else None
        if not rl:
            print(f"NEXT: manual inputs saved to {mp}; add --manual {mp} to the run command."); sys.exit(0)
        P = rl["paths"]
        rn = argparse.Namespace(out=out, work=a.work, debug=a.debug, mode=rl["mode"], workbook=resolve(P["workbook"], out),
                                statements=[resolve(s, out) for s in P["statements"]], bundle=bpath,
                                actual=resolve(P.get("actual"), out), period_end=P.get("period_end_arg"), manual=mp,
                                company=None, company_id=None)
        run(rn)
    for l in (saves + sp_lines(cid, "company", [bpath], folder=False) if logged else saves):
        print(l)
    print(f"AMEND DONE: {cp['display_name']} ({cid}) | profile v{cp.get('profile_version')} | {approval_text(cp)}")
    print("NEXT: carry out the SHAREPOINT lines, then post the lines above unchanged. Stop.")
    sys.exit(0)


def selftest(a):
    t = os.path.join(HERE, "..", "tests")
    rc, o = sh([os.path.join(t, "run_engine_selftest.py")])
    rc2, o2 = sh([os.path.join(t, "run_pipeline_selftest.py")])
    print(o.strip()); print(o2.strip())
    sys.exit(0 if rc == 0 and rc2 == 0 else 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for n in ("selftest", "onboard", "run", "check", "amend"):
        p = sub.add_parser(n)
        p.add_argument("--out", default="/app/created" if os.path.isdir("/app") else os.getcwd())
        p.add_argument("--work", default="/tmp/valuation_work")
        p.add_argument("--debug", action="store_true")
    o_ = sub.choices["onboard"]
    o_.add_argument("--workbook", required=True); o_.add_argument("--statements", nargs="+", required=True)
    o_.add_argument("--company"); o_.add_argument("--company-id"); o_.add_argument("--bundle"); o_.add_argument("--period-end")
    o_.add_argument("--fresh", action="store_true", help="with --bundle: rediscover the structure, keep only the decisions log")
    o_.add_argument("--answers", help="the AI's answer to the one judgment question: one-line JSON or a path")
    r_ = sub.choices["run"]
    r_.add_argument("--mode", choices=["replay", "backtest", "refresh"], required=True)
    r_.add_argument("--workbook", required=True); r_.add_argument("--statements", nargs="+", required=True)
    r_.add_argument("--bundle", required=True)
    for f in ("--actual", "--period-end", "--manual", "--company", "--company-id"):
        r_.add_argument(f)
    c_ = sub.choices["check"]
    c_.add_argument("--values", help="the Run script result: '-' to read it from stdin (heredoc), or one-line JSON")
    c_.add_argument("--saved", help="fallback: the workbook saved by desktop Excel"); c_.add_argument("--run-log")
    m_ = sub.choices["amend"]
    m_.add_argument("--changes"); m_.add_argument("--bundle"); m_.add_argument("--run-log")
    a = ap.parse_args()
    for k in ("company", "company_id", "bundle", "run_log", "fresh", "answers", "values", "saved"):
        if not hasattr(a, k):
            setattr(a, k, None)
    {"selftest": selftest, "onboard": onboard, "run": run, "check": check, "amend": amend}[a.cmd](a)
