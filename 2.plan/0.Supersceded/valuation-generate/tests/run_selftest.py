# run_selftest.py - proves valuation-generate works in THIS sandbox, using bundled fixtures.
import os, sys, subprocess, tempfile, shutil, json
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.join(HERE, "..", "scripts"); F = os.path.join(HERE, "fixtures")


def run(args):
    p = subprocess.run([sys.executable] + args, capture_output=True, text=True)
    return p.stdout + p.stderr


def status(out, key):
    for line in out.splitlines():
        if line.startswith(key):
            return line.split(":", 1)[1].split("|")[0].strip()
    return "?"


def main():
    t = tempfile.mkdtemp(); f = lambda n: os.path.join(F, n); o = lambda n: os.path.join(t, n); cases = []
    run([f"{S}/index_sources.py", f("src_q2_statements.xlsx"), "--out", o("idx.json")])
    out = run([f"{S}/map_financials.py", "--sources-index", o("idx.json"), "--out", o("m0.json")])
    cases.append(("no answers: builds anyway, assumptions listed for the end", status(out, "MAPPING STATUS") == "READY_WITH_ASSUMPTIONS" and "ASSUMPTION:" in out))
    out = run([f"{S}/map_financials.py", "--sources-index", o("idx.json"), "--answers", f("answers.json"), "--out", o("m.json")])
    cases.append(("mapping READY with answers", status(out, "MAPPING STATUS") == "READY"))
    cases.append(("EBITDA derived from revenue - COGS - opex", "revenue + cogs + opex" in out))
    out = run([f"{S}/build_workbook.py", "--mapping", o("m.json"), "--answers", f("answers.json"), "--out", o("TestCo.xlsx")])
    cases.append(("workbook BUILT", status(out, "BUILD STATUS") == "BUILT"))
    out = run([f"{S}/compare_to_actual.py", "--generated", f("gen_saved.xlsx"), "--outputs", o("TestCo_outputs.json"),
               "--actual", f("actual_workbook.xlsx"), "--actual-cells", f("actual_cells.json"), "--out-dir", t])
    cases.append(("comparison finds the difference", status(out, "COMPARE STATUS") == "GENERATED_DIFFERS"))
    cases.append(("EV gap attributed to the multiple (-3,372.50)", "Multiple effect" in out and "-3,372.50" in out))
    run([f"{S}/index_sources.py", f("alt_statements.xlsx"), "--out", o("idx_alt.json")])
    out = run([f"{S}/map_financials.py", "--sources-index", o("idx_alt.json"), "--answers", f("answers_alt.json"), "--out", o("ma.json")])
    cases.append(("alt layout: quarterly headers, YTD/budget ignored, EBITDA line used", "EBITDA route: ebitda" in out))
    cases.append(("alt layout: two debt lines summed and flagged", "FLAG: debt is the SUM" in out))
    # the one-command wrapper the agent uses
    g = os.path.join(S, "generate.py"); go = o("gout"); G = ["--out", go, "--work", o("gwork")]
    gen = lambda *x, stdin=None: (lambda p: (p.returncode, p.stdout + p.stderr))(subprocess.run(
        [sys.executable, g] + list(x) + G, capture_output=True, text=True, input=stdin, env=dict(os.environ, VALUATION_UPLOAD_ROOT=go)))
    os.makedirs(go)
    rc, out = gen("build", "--statements", f("src_q2_statements.xlsx"), "--company", "Test Co", "--answers", "-",
                  stdin=open(f("answers.json")).read())
    cases.append(("wrapper build (answers via heredoc): Excel step, workbook + log only", rc == 20 and sorted(os.listdir(go)) ==
                  ["test_2026-Q2_generate_log.json", "test_2026-Q2_generated.xlsx"]))
    rc, out = gen("compare", "--saved", f("gen_saved.xlsx"))
    cases.append(("wrapper values without an actual workbook", rc == 0 and "VALUES STATUS: READ" in out))
    rc, out = gen("compare", "--saved", f("gen_saved.xlsx"), "--actual", f("actual_workbook.xlsx"))
    js = json.load(open(os.path.join(go, "judgment.json"))) if rc == 10 else {}
    cases.append(("wrapper asks only about the ambiguous metric (EBITDA)", rc == 10 and [q["metric"] for q in js["questions"]] == ["valuation_ebitda"]))
    json.dump({"valuation_ebitda": "A"}, open(os.path.join(go, "actual_cell_picks.json"), "w"))
    rc, out = gen("compare", "--saved", f("gen_saved.xlsx"), "--actual", f("actual_workbook.xlsx"))
    cases.append(("wrapper compare explains the EV gap (-3,372.50)", rc == 0 and "GENERATED_DIFFERS" in out and "-3,372.50" in out))
    ok = all(c[1] for c in cases)
    print(f"SELFTEST: {'PASS' if ok else 'FAIL'}")
    for n, p in cases:
        print(f"- {'PASS' if p else 'FAIL'}: {n}")
    shutil.rmtree(t, ignore_errors=True)
    sys.exit(0 if ok else 1)


main()
