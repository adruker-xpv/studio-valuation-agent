# build_profile.py (v2) - builds the company mapping profile with EXECUTABLE rules
# Usage:
#   python build_profile.py <input_map.json> <matches.json> <concepts.json> --out-dir /app/created
#   add --approve "<ids>" --approver "<name>" ONLY when that person approved in chat (recorded, not required to test)
# Each automated concept gets an execution spec: discovered by reproduction (matches.json) or specified in
# concepts.json ("execution"). A concept is EXECUTABLE only if the refresh engine can run its spec.
# Statuses per concept: EXECUTABLE (spec + reproduced evidence), EXECUTABLE_UNVERIFIED (specified, not reproduced),
# MANUAL (manual/carry-forward modes), EXCEPTION (automated mode without a runnable spec).
# PROFILE STATUS: INVALID (exit 1) | REVIEW_REQUIRED (exit 3) | INPUT_REQUIRED (exit 0: complete, manual inputs
# needed each quarter) | READY (exit 0). Approvals are not required to replay; a named person certifies after a replay/backtest passes (review by exception).
import sys, json, argparse, datetime, os, hashlib
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wbutil import OPS, cells_of, ref

WRITE = {"replace_period_value", "roll_window", "carry_forward", "carry_forward_event_driven", "manual_input", "manual_review"}
PERIOD = {"month", "quarter_sum_of_months", "quarter_end_balance", "ltm_sum", "ytd", "ytd_difference",
          "point_in_time", "not_periodic", "uncertain"}
MISSING = {"block_and_flag", "carry_forward_and_flag", "manual_input"}
AUTOMATED = {"replace_period_value", "roll_window"}
STEP = {"month": 1, "quarter_sum_of_months": 3, "quarter_end_balance": 3, "ytd": 3, "ytd_difference": 3, "ltm_sum": 3}
C_FIELDS = {"concept_id", "name", "entity", "targets", "write_mode", "period_rule", "source_filename_pattern",
            "reconciliation_rule", "missing_source_behavior", "execution", "notes", "questions"}


def check_spec(sp, where):
    errs = []
    if not isinstance(sp, dict) or sp.get("operation") not in OPS:
        return [f"{where}: execution.operation must be one of {list(OPS)}"]
    if sp["operation"] == "components":
        if not sp.get("components"):
            errs.append(f"{where}: components needs a list of sub-specs")
        for i, c in enumerate(sp.get("components", [])):
            errs += check_spec(c, f"{where}.components[{i}]")
        return errs
    s = sp.get("source") or {}
    if not s.get("label"):
        errs.append(f"{where}: execution.source.label is required")
    if s.get("role", "current") not in ("current", "ytd", "prior_year"):
        errs.append(f"{where}: execution.source.role must be current, ytd or prior_year")
    if sp["operation"] == "sum_months" and int(sp.get("months", 0)) < 1:
        errs.append(f"{where}: sum_months needs months >= 1")
    return errs


def main(a):
    imap = json.load(open(a.input_map, encoding="utf-8"))
    mt = json.load(open(a.matches, encoding="utf-8"))
    matches = {b["id"]: b for b in mt["blocks"]}
    concepts = json.load(open(a.concepts, encoding="utf-8")).get("concepts", [])
    entries = {e["id"]: e for e in imap["inputs"]}
    need = {i for i, e in entries.items()
            if (e.get("material") and e.get("type") != "not_material") or e.get("reporting_required") == "yes"}
    template_fp = imap.get("template_fingerprint", "")
    prev_path = os.path.join(a.out_dir, "mapping_profile.json")
    prev = {}
    if os.path.exists(prev_path):
        prev = {c["concept_id"]: (c.get("approval"), c.get("approval_basis_hash")) for c in json.load(open(prev_path))["concepts"]}
    errs, owner = [], {}
    for i, c in enumerate(concepts):
        cid = c.get("concept_id")
        if not cid:
            errs.append(f"concept {i}: missing concept_id"); continue
        if set(c) - C_FIELDS:
            errs.append(f"{cid}: unknown fields {sorted(set(c) - C_FIELDS)}")
        if c.get("write_mode") not in WRITE:
            errs.append(f"{cid}: write_mode must be one of {sorted(WRITE)}")
        if c.get("period_rule") not in PERIOD:
            errs.append(f"{cid}: period_rule must be one of {sorted(PERIOD)}")
        if c.get("missing_source_behavior") not in MISSING:
            errs.append(f"{cid}: missing_source_behavior must be one of {sorted(MISSING)}")
        if c.get("execution") is not None:
            errs += check_spec(c["execution"], cid)
        for t in c.get("targets") or []:
            if t not in entries:
                errs.append(f"{cid}: target {t} is not an id in the input map")
            elif t in owner:
                errs.append(f"{cid}: target {t} already belongs to {owner[t]}")
            else:
                owner[t] = cid
        if not c.get("targets"):
            errs.append(f"{cid}: needs at least one target")
    errs += [f"{t}: in-scope input not assigned to any concept" for t in sorted(need - set(owner))]
    if errs:
        print("PROFILE STATUS: INVALID"); print("\n".join(f"- {x}" for x in errs[:100]))
        print("NEXT REQUIRED STEP: fix concepts.json for the problems above and re-run (max 3 attempts).")
        return 1

    approve = {x.strip() for x in (a.approve or "").split(",") if x.strip()}
    if approve and not a.approver:
        print("PROFILE STATUS: INVALID\n- --approve needs --approver"); return 1
    today = datetime.date.today().isoformat()
    out, resets = [], []
    for c in concepts:
        blocks = [matches.get(t) for t in c["targets"]]
        specs = {json.dumps(b["execution_spec"], sort_keys=True) for b in blocks if b and b.get("execution_spec")}
        auto = c["write_mode"] in AUTOMATED
        offsets, basis_of, operands = {}, {}, []
        for t, b in zip(c["targets"], blocks):
            cells = {x["cell"]: x for x in (b or {}).get("cells", [])}
            tcells = [ref(k) for k in cells_of(t)]
            for r_ in tcells:
                x = cells.get(r_, {})
                if x.get("result") == "reproduced":
                    offsets[r_], basis_of[r_] = x["offset_months"], "reproduced"
                    if len(operands) < 4:
                        operands.append(f"{r_} <- " + "; ".join(x.get("operands", [])))
            # infer offsets for other cells in a row block from layout (right-most known cell, step by period rule)
            known = [(r_, offsets[r_]) for r_ in tcells if r_ in offsets]
            step = STEP.get(c["period_rule"])
            if auto and known and step and c["write_mode"] == "roll_window":
                pos = {r_: i for i, r_ in enumerate(tcells)}
                anchor, off = known[-1]
                for r_ in tcells:
                    if r_ not in offsets:
                        offsets[r_] = off - step * (pos[anchor] - pos[r_]); basis_of[r_] = "inferred from layout"
            for r_ in tcells:
                offsets.setdefault(r_, None); basis_of.setdefault(r_, None)
        if c.get("execution") is not None:
            spec, spec_src = c["execution"], "specified in concepts.json"
            if auto and not any(v is not None for v in offsets.values()) and c["write_mode"] == "replace_period_value":
                offsets = {r_: 0 for r_ in offsets}; basis_of = {r_: "specified (current period)" for r_ in offsets}
        elif len(specs) == 1:
            spec, spec_src = json.loads(specs.pop()), "discovered by reproduction"
        else:
            spec, spec_src = None, ("conflicting rules across target blocks" if len(specs) > 1 else None)
        if not auto:
            status = "MANUAL"
        elif spec is None:
            status = "EXCEPTION"
        elif spec_src == "discovered by reproduction" or any(v == "reproduced" for v in basis_of.values()):
            status = "EXECUTABLE"
        else:
            status = "EXECUTABLE_UNVERIFIED"
        if auto and spec is not None and not any(v == 0 for v in offsets.values()):
            status = "EXCEPTION"; spec_src = (spec_src or "") + "; no target cell is mapped to the current period"
        basis = json.dumps({"targets": sorted(c["targets"]), "spec": spec, "offsets": offsets,
                            **{k: c.get(k) for k in ("write_mode", "period_rule", "missing_source_behavior")},
                            "template": template_fp}, sort_keys=True, default=str)
        bhash = hashlib.sha256(basis.encode()).hexdigest()[:16]
        old, oh = prev.get(c["concept_id"], (None, None))
        appr = {"status": "not_reviewed", "approved_by": None, "date": None}
        if old and old.get("status") == "approved":
            if oh == bhash:
                appr = old
            else:
                appr = dict(appr, note=f"approval reset: rule changed since {old.get('approved_by')} approved on {old.get('date')}")
                resets.append(c["concept_id"])
        if c["concept_id"] in approve:
            appr = {"status": "approved", "approved_by": a.approver, "date": today}
        out.append({**{k: c.get(k) for k in ("concept_id", "name", "entity", "targets", "write_mode", "period_rule",
                                             "source_filename_pattern", "reconciliation_rule", "missing_source_behavior",
                                             "notes", "questions")},
                    "status": status, "execution": spec, "execution_source": spec_src,
                    "cell_offsets_months": offsets, "offset_basis": basis_of, "evidence": operands,
                    "formula_preservation": "write hardcoded input cells only; never overwrite formulas",
                    "approval_basis_hash": bhash, "approval": appr})
    exc = [c["concept_id"] for c in out if c["status"] == "EXCEPTION"]
    unver = [c["concept_id"] for c in out if c["status"] == "EXECUTABLE_UNVERIFIED"]
    review = [c["concept_id"] for c in out if c["write_mode"] == "manual_review" or c["period_rule"] == "uncertain"]
    manual = [c["concept_id"] for c in out if c["write_mode"] == "manual_input"]
    ready = not exc and not review
    status = "REVIEW_REQUIRED" if not ready else ("INPUT_REQUIRED" if manual else "READY")
    os.makedirs(a.out_dir, exist_ok=True)
    json.dump({"version": 2, "workbook": imap.get("workbook"), "generated": today, "status": status,
               "template_fingerprint": template_fp, "period_end": mt.get("period_end"),
               "fiscal_year_start_month": mt.get("fiscal_year_start_month"), "key_outputs": imap.get("key_outputs", []),
               "statement_layout": mt.get("statement_layout", []), "layout_checks": mt.get("layout_checks", []),
               "concepts": out}, open(prev_path, "w", encoding="utf-8"), indent=1, default=str)
    md = [f"# Mapping profile: {imap.get('workbook')}", f"Status: **{status}** | concepts: {len(out)} | period end "
          f"{mt.get('period_end')} | fiscal year starts month {mt.get('fiscal_year_start_month')}", "",
          "| Concept | Status | Rule (executable) | Current-period cells | Earlier-period cells | If source missing | Approval |",
          "|---|---|---|---|---|---|---|"]
    order = sorted(out, key=lambda c: ["EXCEPTION", "EXECUTABLE_UNVERIFIED", "EXECUTABLE", "MANUAL"].index(c["status"]))
    for c in order:
        sp = c["execution"]
        rule = (f"{sp['operation']}{'(' + str(sp.get('months')) + ')' if sp.get('months') else ''} "
                f"'{sp.get('source', {}).get('label', 'components')}' x{sp.get('scale', 1)}") if sp else c["write_mode"]
        cur = sum(1 for v in c["cell_offsets_months"].values() if v == 0)
        earlier = sum(1 for v in c["cell_offsets_months"].values() if v is not None and v < 0)
        md.append(f"| {c['name']} | {c['status']} | {rule} | {cur} | {earlier} | {c['missing_source_behavior']} | {c['approval']['status']} |")
    rv = []
    U = {"EXCEPTION": 1.0, "EXECUTABLE_UNVERIFIED": 0.6, "MANUAL": 0.3, "EXECUTABLE": 0.1}
    for c in out:
        why = {"EXCEPTION": "no runnable rule: give the rule in words, or change its write mode",
               "EXECUTABLE_UNVERIFIED": "rule stated but not yet reproduced from the statements",
               "MANUAL": "entered or carried each quarter: confirm the source and cadence",
               "EXECUTABLE": "rule reproduced the workbook: confirm it is the intended source"}[c["status"]]
        qs = c.get("questions") or []
        pr = round(3 * max(U[c["status"]], 0.2 if qs else 0), 2)
        rv.append((pr, c["name"], "; ".join(qs) if qs else why))
    for x in mt.get("layout_checks", []):
        rv.append((0.6 if "layout" in x or "same month" in x or "missing" in x else 0.4, "statement pack", x))
    rv.sort(key=lambda x: -x[0])
    md[3:3] = ["", "## Review list (highest priority first: impact x uncertainty)", "| # | Priority | Item | Why |", "|---|---|---|---|"] + \
              [f"| {k} | {x[0]:.2f} | {x[1]} | {x[2]} |" for k, x in enumerate(rv, 1)] + [""]
    md += ["", "## Evidence (how each rule reproduced the workbook)"] + [f"- **{c['name']}**: {e}" for c in out for e in c["evidence"]]
    md += ["", "## Statement pack checks"] + ([f"- {x}" for x in mt.get("layout_checks", [])] or ["- OK"])
    md += ["", "## Questions for the analyst"] + ([f"- **{c['name']}**: {q}" for c in out for q in (c.get("questions") or [])] or ["(none)"])
    open(os.path.join(a.out_dir, "mapping_profile_review.md"), "w", encoding="utf-8").write("\n".join(md))
    print(f"PROFILE STATUS: {status}")
    print("concepts: " + ", ".join(f"{k}={v}" for k, v in Counter(c["status"] for c in out).items()))
    print(f"gate {'PASS' if not exc else 'FAIL'}: every automated concept has a runnable rule" + (f" (exceptions: {', '.join(exc)})" if exc else ""))
    print(f"gate {'PASS' if not review else 'FAIL'}: no unresolved meaning (manual_review or uncertain rules)" + (f" ({', '.join(review)})" if review else ""))
    if manual:
        print(f"note: {len(manual)} known manual inputs need a value each quarter (carried forward and flagged if not given): {', '.join(manual)}")
    if unver:
        print(f"note: specified but not reproduced from the sources, so the replay is their first test: {', '.join(unver)}")
    if resets:
        print(f"approvals reset because their rule changed: {', '.join(resets)}")
    print("note: approvals are not needed to replay; a named person certifies after the replay or backtest passes.")
    print(f"FILES WRITTEN:\n{prev_path}\n{os.path.join(a.out_dir, 'mapping_profile_review.md')}")
    print("NEXT REQUIRED STEP: " + ("save the profile files and give the final summary; the next action is a replay or backtest."
                                    if ready else "add an \"execution\" rule to concepts.json for each exception (from the "
                                    "analyst's words), or change its write_mode, and re-run; list what is missing in the summary."))
    return 0 if ready else 3


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("input_map"); ap.add_argument("matches"); ap.add_argument("concepts")
    ap.add_argument("--out-dir", default="/app/created"); ap.add_argument("--approve", default=""); ap.add_argument("--approver", default="")
    try:
        sys.exit(main(ap.parse_args()))
    except SystemExit:
        raise
    except Exception as e:
        print(f"PROFILE_ERROR: {type(e).__name__}: {e}"); sys.exit(1)
