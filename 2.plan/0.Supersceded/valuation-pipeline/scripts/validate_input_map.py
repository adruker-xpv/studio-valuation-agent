# validate_input_map.py - gates an input map against the extractor's skeleton (v3)
# Usage: python validate_input_map.py <stem>_inputs_skeleton.json <stem>_input_map.json
# STATUS: INVALID (exit 1) | BLOCKED (exit 4) | REVIEW_REQUIRED (exit 3) | COMPLETE (exit 0)
# BLOCKED = a blocking control fails, or an error/external link feeds a key output.
# COMPLETE = structurally complete, no unresolved items, key outputs set. It is NOT proof that the
# classifications are right or that a new workbook can be generated; every classification is proposed.
import json, sys

TYPES = {"financial_statement", "assumption", "prior_period", "constant",
         "carry_forward_event_driven", "reference_data", "not_material", "uncertain"}
CHANGES = {"yes", "no", "on_event", "uncertain"}
CONF = {"high", "medium", "low"}
FILL = {"type", "expected_source", "changes_each_quarter", "confidence", "notes", "reviewed_by", "reporting_required"}
REPORTING = {"yes", "no", "unconfirmed"}
LOCKED = ("sheet", "range", "label", "header", "n_cells", "sample_values",
          "material", "feeds_key_outputs", "paths_to_key_outputs", "flags")


def evaluate(skel_path, map_path):
    skel = json.load(open(skel_path, encoding="utf-8"))
    try:
        m = json.load(open(map_path, encoding="utf-8"))
    except json.JSONDecodeError as e:
        return {"status": "INVALID", "errors": [f"input map is not valid JSON: {e}"], "skel": skel}
    sk = {e["id"]: e for e in skel["inputs"]}
    errs, seen = [], {}
    for i, e in enumerate(m.get("inputs", [])):
        if not isinstance(e, dict) or "id" not in e:
            errs.append(f"entry {i}: must be an object with an id"); continue
        eid = e["id"]
        if eid not in sk:
            errs.append(f"{eid}: not in the skeleton"); continue
        if eid in seen:
            errs.append(f"{eid}: duplicate entry")
        seen[eid] = e
        extra = set(e) - FILL - set(LOCKED) - {"id"}
        if extra:
            errs.append(f"{eid}: unknown fields {sorted(extra)}")
        for f in LOCKED:
            if e.get(f) != sk[eid].get(f):
                errs.append(f"{eid}: '{f}' differs from the skeleton")
        t, ch = e.get("type"), e.get("changes_each_quarter")
        if t not in TYPES:
            errs.append(f"{eid}: type must be one of {sorted(TYPES)}")
        elif t == "not_material":
            if sk[eid]["material"]:
                errs.append(f"{eid}: not_material but it feeds a key output")
            if e.get("reporting_required") not in REPORTING:
                errs.append(f"{eid}: reporting_required must be one of {sorted(REPORTING)}")
        else:
            if ch not in CHANGES:
                errs.append(f"{eid}: changes_each_quarter must be one of {sorted(CHANGES)}")
            if t == "carry_forward_event_driven" and ch not in ("on_event", "uncertain"):
                errs.append(f"{eid}: carry_forward_event_driven needs changes_each_quarter 'on_event'")
            if t == "financial_statement" and not e.get("expected_source"):
                errs.append(f"{eid}: financial_statement needs expected_source")
            if e.get("confidence") not in CONF:
                errs.append(f"{eid}: confidence must be one of {sorted(CONF)}")
            if sk[eid]["material"] and not e.get("notes"):
                errs.append(f"{eid}: material input needs notes citing cells")
    for eid in sk:
        if eid not in seen:
            errs.append(f"{eid}: missing from the input map")
    tot = skel["totals"]
    recon = (f"reconciliation: blocks {len(seen)}/{tot['blocks']}, cells "
             f"{sum(sk[i]['n_cells'] for i in seen)}/{tot['cells']} (material cells {tot['material_cells']})")
    if errs:
        return {"status": "INVALID", "errors": errs, "recon": recon, "skel": skel}
    unresolved = [i for i, e in seen.items() if e["type"] == "uncertain" or e.get("changes_each_quarter") == "uncertain"]
    low = [i for i, e in seen.items() if e.get("confidence") == "low" and i not in unresolved]
    material = [i for i in seen if sk[i]["material"]]
    medium = [i for i in material if seen[i].get("confidence") == "medium" and i not in unresolved]
    reviewed = [i for i in material if seen[i].get("reviewed_by")]
    cadence = [i for i in material if seen[i].get("changes_each_quarter") in ("yes", "no", "on_event")
               and not seen[i].get("reviewed_by")]
    auto_nm = [i for i, e in seen.items() if e["type"] == "not_material"]
    flagged = [(i, x) for i in seen for x in sk[i]["flags"]]
    blocking = skel.get("blocking_issues", [])
    controls = skel.get("controls", [])
    ctrl_block = [c for c in controls if c["result"] != "PASS" and c["severity"] == "blocking"]
    ctrl_warn = [c for c in controls if c["result"] != "PASS" and c["severity"] == "warning"]
    scope_open = [i for i, e in seen.items() if e["type"] == "not_material" and e.get("reporting_required") == "unconfirmed"]
    scope_yes = [i for i, e in seen.items() if e["type"] == "not_material" and e.get("reporting_required") == "yes"]
    gates = {"key outputs set": bool(skel.get("key_outputs")),
             "blocking controls pass": not ctrl_block,
             "warning controls pass": not ctrl_warn,
             "no unresolved entries": not unresolved,
             "no blocking issues": not blocking,
             "flags addressed in notes": all(seen[i].get("notes") for i, _ in flagged)}
    business = "CONFIRMED" if material and len(reviewed) == len(material) and not scope_open else "PENDING"
    status = "BLOCKED" if (ctrl_block or blocking) else ("COMPLETE" if all(gates.values()) else "REVIEW_REQUIRED")
    return {"status": status, "errors": [], "recon": recon, "controls": controls,
            "scope_open": scope_open, "scope_yes": scope_yes,
            "gates": gates, "unresolved": unresolved, "low_conf": low, "medium_conf": medium,
            "reviewed": reviewed, "material": material, "cadence_unconfirmed": cadence,
            "auto_not_material": auto_nm, "business": business, "blocking": blocking,
            "flagged": flagged, "entries": seen, "skel": skel,
            "counts": {t: sum(1 for e in seen.values() if e["type"] == t) for t in sorted(TYPES)},
            "broken_names": [n for n in skel.get("named_ranges", []) if n["category"] in ("broken", "external")]}


def main(skel_path, map_path):
    r = evaluate(skel_path, map_path)
    print(f"STATUS: {r['status']}")
    if r["status"] != "INVALID":
        print(f"technical status: {r['status']} | business review: {r['business']} "
              f"({len(r['reviewed'])}/{len(r['material'])} material blocks confirmed by an analyst)")
    if r.get("recon"):
        print(r["recon"])
    if r["status"] == "INVALID":
        print("\n".join(f"- {x}" for x in r["errors"][:100]))
        print("NEXT REQUIRED STEP: fix classifications.json for the problems above, re-run apply_classifications.py, "
              "then this validator (max 3 attempts; then run build_report.py anyway).")
        return 1
    for g, ok in r["gates"].items():
        print(f"gate {'PASS' if ok else 'FAIL'}: {g}")
    for c in r["controls"]:
        print(f"control {c['result']}: {c['cell']} value {c['value']} expected {c['expected']} ({c['severity']})")
    print(f"reporting scope: {len(r['scope_yes'])} non-material blocks reporting-required, "
          f"{len(r['scope_open'])} unconfirmed")
    print("types: " + ", ".join(f"{k}={v}" for k, v in r["counts"].items() if v))
    print(f"unresolved: {len(r['unresolved'])}" + (": " + ", ".join(r["unresolved"][:60]) if r["unresolved"] else ""))
    print(f"low confidence: {len(r['low_conf'])}" + (": " + ", ".join(r["low_conf"][:60]) if r["low_conf"] else ""))
    print(f"medium confidence: {len(r['medium_conf'])}" + (": " + ", ".join(r["medium_conf"][:60]) if r["medium_conf"] else ""))
    print(f"cadence proposed, not confirmed: {len(r['cadence_unconfirmed'])} material blocks")
    print(f"blocking issues: {len(r['blocking'])}" + "".join(f"\n- {b}" for b in r["blocking"][:30]))
    print("note: technical COMPLETE = structurally complete and machine checks pass. It is not business correctness; "
          "that needs business review CONFIRMED.")
    print("NEXT REQUIRED STEP (P4): run build_report.py. Do not ask the user anything; open items go in the report.")
    return {"COMPLETE": 0, "REVIEW_REQUIRED": 3, "BLOCKED": 4}[r["status"]]


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python validate_input_map.py <skeleton.json> <input_map.json>"); sys.exit(2)
    sys.exit(main(sys.argv[1], sys.argv[2]))
