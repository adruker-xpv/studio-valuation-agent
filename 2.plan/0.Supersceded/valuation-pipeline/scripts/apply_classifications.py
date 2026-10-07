# apply_classifications.py - merges the agent's classifications into the skeleton (deterministic)
# Usage: python apply_classifications.py <stem>_inputs_skeleton.json <file> [<file> ...] --out <stem>_input_map.json
#        Each file is classifications.json or a saved <stem>_input_map.json (to reuse earlier decisions).
#        Later files override earlier ones for the same id.
# - Non-material blocks are set to not_material automatically (no LLM judgment needed).
# - Material blocks take type/expected_source/changes_each_quarter/confidence/notes from classifications.json.
# - Structural fields are always copied from the skeleton, so the agent cannot alter them.
# - Non-material blocks get reporting_required = unconfirmed, unless a scope file (--scope) or a reused
#   input map sets it: scope.json = {"reviewed_by": "<name>", "sheets": {"LP Report": "yes"},
#   "blocks": {"<id>": "no"}}  (blocks override sheets; only from an analyst's explicit instruction)
# classifications.json: {"classifications": [{"id": "...", "type": "...", "expected_source": "...",
#                        "changes_each_quarter": "...", "confidence": "high|medium|low", "notes": "..."}]}
import json, sys, argparse, copy

FIELDS = ("type", "expected_source", "changes_each_quarter", "confidence", "notes", "reviewed_by")
REPORTING = {"yes", "no", "unconfirmed"}


def main(skel_path, cls_paths, out, scope_path=None):
    skel = json.load(open(skel_path, encoding="utf-8"))
    by_id, problems, reuse_ids, prior_scope = {}, [], set(), {}
    ids = {e["id"] for e in skel["inputs"]}
    for cls_path in cls_paths:
        spec = json.load(open(cls_path, encoding="utf-8"))
        reuse = "inputs" in spec and "classifications" not in spec     # a saved input map, reused
        cls = spec.get("classifications") or [e for e in spec.get("inputs", []) if e.get("type") != "not_material"]
        if reuse:
            for e in spec.get("inputs", []):
                if e.get("type") == "not_material" and e.get("reporting_required") in ("yes", "no"):
                    prior_scope[e["id"]] = (e["reporting_required"], e.get("reviewed_by"))
        seen_here = set()
        for c in cls:
            cid = c.get("id")
            if cid not in ids:
                if not reuse:
                    problems.append(f"{cid}: not a skeleton id (copy ids exactly)")
                continue
            if cid in seen_here:
                problems.append(f"{cid}: classified twice in {cls_path}")
            seen_here.add(cid)
            by_id[cid] = c
            if reuse:
                reuse_ids.add(cid)
            else:
                reuse_ids.discard(cid)
    scope = json.load(open(scope_path, encoding="utf-8")) if scope_path else {}
    if scope and not scope.get("reviewed_by"):
        problems.append("scope file needs reviewed_by (the analyst who confirmed the scope)")
    for v in list(scope.get("sheets", {}).values()) + list(scope.get("blocks", {}).values()):
        if v not in ("yes", "no"):
            problems.append(f"scope values must be yes or no, got {v!r}")
    m = copy.deepcopy(skel)
    auto = filled = missing = 0
    for e in m["inputs"]:
        if not e["material"]:
            rr, who = prior_scope.get(e["id"], ("unconfirmed", None))
            if e["id"] in scope.get("blocks", {}) or e["sheet"] in scope.get("sheets", {}):
                rr = scope.get("blocks", {}).get(e["id"]) or scope["sheets"][e["sheet"]]
                who = scope.get("reviewed_by")
            e.update(type="not_material", expected_source=None, changes_each_quarter=None,
                     confidence="high", reviewed_by=who, reporting_required=rr,
                     notes="auto: not upstream of any key output; may still need refresh for reporting "
                           "or disclosure (analyst to confirm scope)")
            auto += 1
            if e["id"] in by_id and e["id"] not in reuse_ids:
                problems.append(f"{e['id']}: not material; remove it from classifications.json")
            continue
        c = by_id.get(e["id"])
        if not c:
            missing += 1
            problems.append(f"{e['id']}: material block missing from classifications.json")
            continue
        for f in FIELDS:
            e[f] = c.get(f)
        e["reporting_required"] = None      # valuation-material blocks are always in scope
        filled += 1
    m["generated_by"] = skel.get("generated_by", "") + " + apply_classifications.py"
    json.dump(m, open(out, "w", encoding="utf-8"), indent=1)
    print(f"MERGED: material classified {filled}, material missing {missing}, auto not_material {auto}")
    for p in problems[:100]:
        print(f"- {p}")
    print(f"FILE WRITTEN: {out}")
    print("NEXT REQUIRED STEP (P3): run validate_input_map.py on the skeleton and this input map."
          + (" Fix classifications.json first if problems are listed above." if problems else ""))
    return 1 if problems else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("skeleton"); ap.add_argument("classifications", nargs="+"); ap.add_argument("--out", required=True)
    ap.add_argument("--scope", default=None, help="scope.json with the analyst's reporting_required decisions")
    a = ap.parse_args()
    sys.exit(main(a.skeleton, a.classifications, a.out, a.scope))
