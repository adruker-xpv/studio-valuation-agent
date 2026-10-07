# run_engine_selftest.py - proves the engine scripts work in THIS sandbox, using bundled fixtures.
# Two statement layouts: demo (one file, months across columns) and lumin (one file per month, current + YTD columns).
# The *_saved_by_excel.xlsx fixtures stand in for the "open in Excel and save" step.
import os, sys, subprocess, tempfile, shutil, glob

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
    t = tempfile.mkdtemp(); cases = []
    d = lambda n: os.path.join(F, "demo", n); l = lambda n: os.path.join(F, "lumin", n); o = lambda n: os.path.join(t, n)

    def cycle(mode, base, plan_args, result, extra_check=(), name="x"):
        out = run([f"{S}/plan_writes.py", "--mode", mode, "--workbook", base] + plan_args + ["--out", o(f"{name}_plan.json")])
        ps = status(out, "PLAN STATUS")
        run([f"{S}/apply_writes.py", "--workbook", base, "--plan", o(f"{name}_plan.json"), "--out", o(f"{name}.xlsx")])
        imap = plan_args[plan_args.index("--input-map") + 1]
        out2 = run([f"{S}/check_result.py", "--mode", mode, "--base", base, "--draft", o(f"{name}.xlsx"), "--input-map", imap,
                    "--plan", o(f"{name}_write_log.json"), "--result", result, "--out-json", o(f"{name}_check.json")] + list(extra_check))
        rep = open(o(f"{name}_check.json")).read() if os.path.exists(o(f"{name}_check.json")) else ""
        return ps, out, status(out2, "CHECK STATUS"), rep

    run([f"{S}/index_sources.py", d("src_q2_statements.xlsx"), "--out", o("d2.json")])
    run([f"{S}/index_sources.py", d("src_q3_statements.xlsx"), "--out", o("d3.json")])
    dm = ["--input-map", d("input_map.json"), "--profile", d("mapping_profile.json")]
    ps, _, cs, _ = cycle("replay", d("base_q2.xlsx"), dm + ["--sources-index", o("d2.json")], d("replay_saved_by_excel.xlsx"), name="d_replay")
    cases += [("demo: replay plan READY", ps == "READY"), ("demo: replay REPLAY_PASS", cs == "REPLAY_PASS")]
    _, _, cs, _ = cycle("replay", d("base_q2.xlsx"), dm + ["--sources-index", o("d2.json")], o("d_replay.xlsx"), name="d_replay2")
    cases.append(("demo: a file not recalculated in Excel fails", cs == "REPLAY_FAIL"))
    out = run([f"{S}/plan_writes.py", "--mode", "refresh", "--workbook", d("replay_saved_by_excel.xlsx")] + dm +
              ["--sources-index", o("d3.json"), "--period-end", "2026-09-30", "--out", o("x.json")])
    cases.append(("demo: refresh runs without a certification file", status(out, "PLAN STATUS") != "REFUSED"))
    ps, _, cs, rep = cycle("refresh", d("replay_saved_by_excel.xlsx"), dm + ["--sources-index", o("d3.json"), "--period-end", "2026-09-30",
                           "--manual", d("manual_inputs_q3.json")],
                           d("refresh_saved_by_excel.xlsx"), name="d_refresh")
    cases += [("demo: refresh plan READY", ps == "READY"), ("demo: refresh DRAFT_READY_FOR_REVIEW", cs == "DRAFT_READY_FOR_REVIEW"),
              ("demo: refresh flags the SG&A spike", "Quarterly!E4" in rep and "moved" in rep)]
    bt = dm + ["--sources-index", o("d2.json"), "--actual", d("base_q2.xlsx"), "--period-end", "2026-06-30"]
    ps, _, cs, _ = cycle("backtest", d("prior_q1.xlsx"), bt, d("backtest_saved_by_excel.xlsx"), ["--actual", d("base_q2.xlsx")], name="d_bt")
    cases.append(("demo: backtest BACKTEST_PASS", cs == "BACKTEST_PASS"))
    btw = [x if x != d("mapping_profile.json") else d("profile_wrong.json") for x in bt]
    _, _, cs, rep = cycle("backtest", d("prior_q1.xlsx"), btw, d("backtest_wrong_saved_by_excel.xlsx"), ["--actual", d("base_q2.xlsx")], name="d_btw")
    cases.append(("demo: a wrong rule fails the backtest, pinned to bs.net_debt", cs == "BACKTEST_FAIL" and "[bs.net_debt]" in rep))

    run([f"{S}/index_sources.py"] + sorted(glob.glob(l("q2/*.xlsx"))) + ["--out", o("l2.json")])
    run([f"{S}/index_sources.py"] + sorted(glob.glob(l("q3/*.xlsx"))) + ["--out", o("l3.json")])
    lm = ["--input-map", l("imap.json"), "--profile", l("mapping_profile.json")]
    ps, out, cs, rep = cycle("replay", l("LuminUltra_valuation_Q2-2026.xlsx"), lm + ["--sources-index", o("l2.json")],
                             l("replay_saved_by_excel.xlsx"), name="l_replay")
    cases += [("monthly files: replay READY with 0 exceptions", ps == "READY" and "exceptions: 0" in out),
              ("monthly files: YTD-difference and 3-month sums rebuilt by rule", "rebuilt by rule: 4" in out),
              ("monthly files: earlier quarter reported as historical, not proof", "historical kept: 2" in out),
              ("monthly files: replay REPLAY_PASS", cs == "REPLAY_PASS")]
    bt = lm + ["--sources-index", o("l3.json"), "--actual", l("LuminUltra_valuation_Q3-2026_actual.xlsx"), "--period-end", "2026-09-30"]
    ps, out, cs, _ = cycle("backtest", l("replay_saved_by_excel.xlsx"), bt, l("backtest_saved_by_excel.xlsx"),
                           ["--actual", l("LuminUltra_valuation_Q3-2026_actual.xlsx")], name="l_bt")
    cases += [("monthly files: backtest rolls last quarter forward", "rolled forward: 2" in out),
              ("monthly files: backtest BACKTEST_PASS", cs == "BACKTEST_PASS")]
    # statement layouts
    y = lambda n: os.path.join(F, "layouts", n)
    out = run([f"{S}/index_sources.py", y("LuminUltra_monthly_pack_Q2.xlsx"), "--out", o("y1.json")])
    cases.append(("layout: one sheet per month detected, repeated labels kept apart",
                  "sheet per month" in out and "kept apart" in out))
    out = run([f"{S}/plan_writes.py", "--mode", "replay", "--workbook", l("LuminUltra_valuation_Q2-2026.xlsx"), "--input-map",
               l("imap.json"), "--profile", y("pack_profile.json"), "--sources-index", o("y1.json"), "--out", o("y1p.json")])
    cases.append(("layout: sheet-per-month pack rebuilds from the consolidated block", "rebuilt by rule: 4" in out and "exceptions: 0" in out))
    out = run([f"{S}/plan_writes.py", "--mode", "replay", "--workbook", l("LuminUltra_valuation_Q2-2026.xlsx"), "--input-map",
               l("imap.json"), "--profile", y("pack_profile.json"), "--sources-index", o("l2.json"), "--out", o("y2p.json")])
    cases.append(("layout: next pack arrives as monthly files - rules follow, change noted",
                  "rebuilt by rule: 4" in out and "statement layout differs" in out))
    out = run([f"{S}/index_sources.py", y("TwoRowHeader_Co.xlsx"), "--out", o("y3.json")])
    import json as _j
    per = [v["period"] for v in _j.load(open(o("y3.json")))["values"]]
    cases.append(("layout: two-row headers (year above month) dated Jul-25..Jun-26", per[0] == "2025-07" and per[-1] == "2026-06"))
    out = run([f"{S}/index_sources.py", y("NoYear_June_30__2026.xlsx"), "--out", o("y4.json")])
    cases.append(("layout: month headers without a year are not used (no silent misdating)",
                  "not used" in out and all(not v["period"] for v in _j.load(open(o("y4.json")))["values"])))
    out = run([f"{S}/index_sources.py"] + sorted(glob.glob(y("X_Statements_*.xlsx"))) + ["--out", o("y5.json")])
    cases.append(("layout: duplicate month and missing month reported for review", "claim the same month" in out and "missing monthly" in out))
    # the draft must leave every non-cell part of the workbook untouched (drawings, charts, external links)
    import zipfile, hashlib
    run([f"{S}/plan_writes.py", "--mode", "replay", "--workbook", d("with_chart.xlsx"), "--input-map", d("input_map.json"),
         "--profile", d("mapping_profile.json"), "--sources-index", o("d2.json"), "--out", o("wc_plan.json")])
    run([f"{S}/apply_writes.py", "--workbook", d("with_chart.xlsx"), "--plan", o("wc_plan.json"), "--out", o("wc.xlsx")])
    za, zb = zipfile.ZipFile(d("with_chart.xlsx")), zipfile.ZipFile(o("wc.xlsx"))
    changed = [n for n in za.namelist() if hashlib.md5(za.read(n)).digest() != hashlib.md5(zb.read(n)).digest()]
    cases.append(("draft writing leaves charts and drawings byte-identical",
                  bool(changed) and all(n.startswith("xl/worksheets/sheet") or n == "xl/workbook.xml" for n in changed)
                  and any("chart" in n for n in za.namelist())))
    ok = all(c[1] for c in cases)
    print(f"SELFTEST: {'PASS' if ok else 'FAIL'}")
    for n, p in cases:
        print(f"- {'PASS' if p else 'FAIL'}: {n}")
    shutil.rmtree(t, ignore_errors=True)
    sys.exit(0 if ok else 1)


main()
