# run_pipeline_selftest.py - end-to-end check of pipeline.py in THIS sandbox (fixtures stand in for the Excel step)
import os, sys, re, json, subprocess, tempfile, shutil, zipfile, glob
HERE = os.path.dirname(os.path.abspath(__file__)); PIPE = os.path.join(HERE, "..", "scripts", "pipeline.py")
F = os.path.join(HERE, "fixtures")
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))


def main():
    t = tempfile.mkdtemp(); o = os.path.join(t, "out"); w = os.path.join(t, "work"); cases = []
    G = ["--out", o, "--work", w]
    env = dict(os.environ, VALUATION_UPLOAD_ROOT=o)    # in the sandbox only /app/created is uploadable; here, the test folder
    run = lambda *args, stdin=None: (lambda p: (p.returncode, p.stdout + p.stderr))(
        subprocess.run([sys.executable, PIPE] + list(args) + G, capture_output=True, text=True, env=env, input=stdin))
    d = lambda n: os.path.join(F, "demo", n)
    changes = lambda obj: json.dump(obj, open(os.path.join(o, "changes.json"), "w"))
    base = os.path.join(t, "tricky_valuation.xlsx"); shutil.copy(d("base_q2.xlsx"), base)
    ob = ["onboard", "--workbook", base, "--statements", d("src_q2_statements.xlsx"), "--company", "Test Co"]

    rc, out = run(*ob)
    cases.append(("onboard: key outputs chosen by rule; one question at the end, about 1 input only", rc == 10 and
                  "C1 Inputs!B6" in out and "C2 " not in out and "K1" not in out))
    ans = json.dumps({"classifications": [{"id": "Inputs!B6", "type": "uncertain", "confidence": "low", "notes": "No label"}]})
    rc, out = run(*(ob + ["--answers", ans]))
    cases.append(("onboard completes: REVIEW_REQUIRED, company_id fixed from the name", rc == 0 and
                  "ONBOARD STATUS: REVIEW_REQUIRED" in out and "company_id test" in out))
    cases.append(("onboard leaves one deliverable (the company bundle)", sorted(os.listdir(o)) == ["test_company.zip"]))
    bundle = os.path.join(o, "test_company.zip")
    rp = ["run", "--mode", "replay", "--workbook", base, "--statements", d("src_q2_statements.xlsx"), "--bundle", bundle]
    rc, out = run(*rp)
    cases.append(("replay: draft saved to SharePoint, then one RECALC line and the check command", rc == 20 and
                  "PLAN STATUS: READY" in out and "name: test_2026-Q2_replay.xlsx" in out and "RECALC: Run script" in out
                  and "check --values -" in out and sorted(os.listdir(o)) ==
                  ["test_2026-Q2_replay.xlsx", "test_2026-Q2_replay_run_log.json", "test_company.zip"]))
    # what the Office Script returns: values of the key outputs and controls, plus error cells
    from openpyxl import load_workbook
    rl0 = json.load(open(os.path.join(o, "test_2026-Q2_replay_run_log.json")))
    sv = load_workbook(d("replay_saved_by_excel.xlsx"), data_only=True)
    val = lambda c: (lambda sh_, cell: sv[sh_][cell].value)(*c.replace("'", "").rsplit("!", 1))
    script_result = json.dumps({"values": {c: val(c) for c in rl0["recalc_cells"]}, "errors": []})
    rc, out = run("check", "--values", "-", stdin=script_result)
    cases.append(("check from the Office Script result: REPLAY_PASS, no Excel step, only the run log saved",
                  "CHECK STATUS: REPLAY_PASS" in out and "recalculated in SharePoint" in out
                  and "name: test_2026-Q2_replay_run_log.json" in out and out.count("Create file") == 1))
    rc, out = run("amend", "--changes", "-", stdin=json.dumps(
        {"by": "Test Analyst", "said": "Inputs!B6 is management's adjustment factor, it's entered each quarter",
         "classifications": [{"id": "Inputs!B6", "type": "assumption", "changes_each_quarter": "yes"}]}))
    cp = json.load(zipfile.ZipFile(bundle).open("company_profile.json"))
    dec = [x for x in cp["decisions"] if x["status"] == "active" and x["kind"] == "classification"]
    cases.append(("named correction with apostrophes (heredoc): logged with the reviewer, re-onboarded to INPUT_REQUIRED v2",
                  "DECISION LOGGED" in out and "INPUT_REQUIRED" in out and cp["profile_version"] == 2
                  and dec and dec[0]["by"] == "Test Analyst" and "it's" in dec[0]["said"]))
    rc, out = run("amend", "--changes", json.dumps({"by": "Test Analyst", "said": "approve the profile - Test Analyst",
                                                    "approve_profile": True}))
    cases.append(("named approval recorded on the profile version", "approved by Test Analyst" in out and "(v2)" in out))
    rc, out = run("run", "--mode", "refresh", "--workbook", d("replay_saved_by_excel.xlsx"), "--statements", d("src_q3_statements.xlsx"),
                  "--bundle", bundle, "--period-end", "2026-09-30")
    cases.append(("refresh needs no certification: INPUT_REQUIRED, not blocked", rc == 20 and "PLAN STATUS: INPUT_REQUIRED" in out))
    changes({"by": None, "said": "Q3 multiple 9.0, add-backs 150", "manual_inputs": {"Inputs!B3": 9.0, "Adjustments!B1": 150}})
    rc, out = run("amend")
    cases.append(("manual inputs given in words re-run the refresh", rc == 20 and "PLAN STATUS: INPUT_REQUIRED" in out))
    rc, out = run("check", "--saved", d("refresh_saved_by_excel.xlsx"))     # fallback path: desktop Excel + upload
    cases.append(("refresh check ranks the SG&A spike above carried-forward inputs", "DRAFT_READY_FOR_REVIEW" in out and
                  out.index("Quarterly!E4") < out.index("carried forward")))
    cases.append(("a review item on a decided cell shows that decision", bool(re.search(r"Inputs!B6 .*previous decision #\d+ .*Test Analyst", out))))
    cases.append(("fallback check saves the final workbook and run log only", "name: test_2026-Q3_refresh.xlsx" in out
                  and "name: test_2026-Q3_refresh_run_log.json" in out and out.count("Create file") == 2))
    changes({"by": "Jane Doe", "said": "Q3 draft reviewed - Jane Doe", "review_period": True})
    rc, out = run("amend")
    rl = json.load(open(os.path.join(o, "test_2026-Q3_refresh_run_log.json")))
    cases.append(("named period review recorded in the run log", rl.get("reviewed_by") == "Jane Doe"))
    changes({"by": "Test Analyst", "said": "LTM EBITDA is not a key output", "key_outputs": {"remove": ["Valuation!B1"]}})
    rc, out = run("amend")
    cases.append(("key-output decision applied", "Key outputs (3," in out))
    shutil.rmtree(w)                                   # a new chat: nothing but the uploaded bundle and files
    rc, out = run("onboard", "--workbook", base, "--statements", d("src_q2_statements.xlsx"), "--bundle", bundle)
    cases.append(("re-onboarding in a new chat from the bundle keeps everything", rc == 0 and "Key outputs (3," in out
                  and "INPUT_REQUIRED" in out and "company_id test" in out))
    rc, out = run("onboard", "--workbook", base, "--statements", d("src_q2_statements.xlsx"), "--bundle", bundle, "--fresh")
    cases.append(("fresh re-onboarding rediscovers structure and re-applies the decisions log (no AI question)", rc == 0
                  and "Key outputs (3," in out and "INPUT_REQUIRED" in out and "JUDGMENT" not in out))

    # a tie between two cells for a core metric: onboarding finishes first, then ONE question covers the tie and the inputs
    code = (
        "import sys, importlib.util, argparse, json\n"
        "spec = importlib.util.spec_from_file_location('pl', sys.argv[1]); pl = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(pl)\n"
        "real = pl.key_output_candidates\n"
        "def fake(schema):\n"
        "    sugg, qs = real(schema)\n"
        "    sugg = [x for x in sugg if x['cell'] not in (\"'Valuation'!B2\", \"'Valuation'!B4\")]\n"
        "    q = {'metric': 'enterprise value', 'options': {'A': 'Valuation!B2 Enterprise value', 'B': 'Valuation!B4 Equity value'},\n"
        "         '_cells': {'A': (\"'Valuation'!B2\", 'enterprise value'), 'B': (\"'Valuation'!B4\", 'enterprise value')}}\n"
        "    return sugg, qs + [q]\n"
        "pl.key_output_candidates = fake\n"
        "pl.onboard(argparse.Namespace(out=sys.argv[2], work=sys.argv[3], debug=False, workbook=sys.argv[4], statements=[sys.argv[5]],\n"
        "    company='Tie Co', company_id=None, bundle=None, period_end=None, fresh=False, answers=sys.argv[6] or None))\n")
    to, tw = os.path.join(t, "tie_out"), os.path.join(t, "tie_work"); os.makedirs(to)
    tie = lambda answers: (lambda p: (p.returncode, p.stdout + p.stderr))(subprocess.run(
        [sys.executable, "-c", code, PIPE, to, tw, base, d("src_q2_statements.xlsx"), answers], capture_output=True, text=True, env=env))
    rc, out = tie("")
    cases.append(("tie: onboarding runs to the end, then one question with the tie AND the unclear input",
                  rc == 10 and "K1 enterprise value" in out and "C1 Inputs!B6" in out and out.count("JUDGMENT NEEDED") == 1))
    rc, out = tie(json.dumps({"key_outputs": {"enterprise value": "A"},
                              "classifications": [{"id": "Inputs!B6", "type": "assumption", "confidence": "low", "notes": "factor"}]}))
    ko_lines = [l for l in out.splitlines() if l.startswith("- ")]
    cases.append(("tie answered: picked cell kept, the other candidate dropped, both answers logged",
                  rc == 0 and any("Valuation!B2" in l for l in ko_lines) and not any("Valuation!B4" in l for l in ko_lines)
                  and "AI picked 'Valuation'!B2" in out and "AI classified Inputs!B6 as assumption" in out))

    # a new Excel error in a key-output precedent fails the check
    rc, out = run(*rp)
    bad = os.path.join(t, "saved_with_ref_error.xlsx")
    zi, zo = zipfile.ZipFile(d("replay_saved_by_excel.xlsx")), zipfile.ZipFile(bad, "w", zipfile.ZIP_DEFLATED)
    for n in zi.namelist():
        b = zi.read(n)
        if n == "xl/worksheets/sheet4.xml":
            b = re.sub(rb'<c r="B4" s="1" t="n"><f aca="false">B2-B3</f><v>[^<]*</v></c>',
                       b'<c r="B4" s="1" t="e"><f aca="false">B2-B3</f><v>#REF!</v></c>', b)
        zo.writestr(n, b)
    zo.close()
    rc, out = run("check", "--saved", bad, "--run-log", os.path.join(o, "test_2026-Q2_replay_run_log.json"))
    cases.append(("new #REF! in a key-output precedent fails the check", "REPLAY_FAIL" in out and "#REF!" in out
                  and "no new Excel errors" in out))

    rc, out = run(*rp)
    bad_result = json.loads(script_result); bad_result["errors"] = ["Valuation!B4=#REF!"]
    bad_result["values"] = {k: ("#REF!" if k.replace("'", "") in ("Valuation!B4", "Valuation!B5") else v) for k, v in bad_result["values"].items()}
    rc, out = run("check", "--values", "-", stdin=json.dumps(bad_result))
    cases.append(("Office Script reports #REF! in a key-output precedent -> check fails", "REPLAY_FAIL" in out and "#REF!" in out))

    # files given by name are found in the chat uploads, including SharePoint downloads saved as name_1.xlsx
    up = os.path.join(t, "uploads"); os.makedirs(up); shutil.copy(base, os.path.join(up, "tricky_valuation_1.xlsx"))
    sys.argv = ["x"]
    import importlib.util as ilu
    sp_ = ilu.spec_from_file_location("pl0", PIPE); pl0 = ilu.module_from_spec(sp_); sp_.loader.exec_module(pl0)
    cases.append(("a file named in the chat is found as a SharePoint download (name_1.xlsx)",
                  pl0.find_file("tricky_valuation.xlsx", [up]) == os.path.join(up, "tricky_valuation_1.xlsx")))

    # an older bundle (input map + profile + certification) upgrades once to a fixed company_id
    lg = os.path.join(t, "Test_Co_company_files.zip")
    with zipfile.ZipFile(lg, "w") as z:
        z.write(d("input_map.json"), "base_q2_input_map.json"); z.write(d("mapping_profile.json"), "mapping_profile.json")
        z.writestr("certification.json", '{"status": "CERTIFIED"}')
    rc, out = run("run", "--mode", "replay", "--workbook", d("base_q2.xlsx"), "--statements", d("src_q2_statements.xlsx"), "--bundle", lg)
    cases.append(("older bundle upgraded once, run proceeds", rc == 20 and "older company bundle upgraded" in out))

    # key outputs: a closed question only when a core metric is genuinely ambiguous
    import importlib.util
    spec = importlib.util.spec_from_file_location("pl", PIPE); pl = importlib.util.module_from_spec(spec)
    sys.argv = ["x"]; spec.loader.exec_module(pl)
    sch = ("=== SHEET: Valuation Summary ===\nF20 [calc] Enterprise value =F18*F19 -> 1000\nF25 [output] Fair value =F20-F21 -> 800\n"
           "=== SHEET: LP Report ===\nD10 [calc] Enterprise value =D8*D9 -> 950\n")
    sugg, qs = pl.key_output_candidates(sch)
    cases.append(("two different 'Enterprise value' cells -> one closed question", len(qs) == 1 and qs[0]["metric"] == "enterprise value"
                  and len(qs[0]["options"]) == 2))
    sugg, qs = pl.key_output_candidates(sch.replace("-> 950", "-> 1000"))
    cases.append(("same value on two sheets is a duplicate, not a question", not qs and any("F20" in s["cell"] for s in sugg)))
    cases.append(("company_id rule: 'LuminUltra Technologies' -> luminultra", pl.company_slug("LuminUltra Technologies") == "luminultra"))
    tm = lambda lab: pl.title_matches(dict(pl.KEY_METRICS)["enterprise value"], lab)
    cases.append(("titles tidied: 'Enterprises  Value', 'EV' match; 'EV / EBITDA' does not",
                  tm("Enterprises  Value") and tm("EV") and tm("Total Enterprise Value (CAD)") and not tm("EV / EBITDA") and not tm("EV/EBITDA")))

    ok = all(c[1] for c in cases)
    print(f"PIPELINE SELFTEST: {'PASS' if ok else 'FAIL'}")
    for n, p in cases:
        print(f"- {'PASS' if p else 'FAIL'}: {n}")
    shutil.rmtree(t, ignore_errors=True)
    sys.exit(0 if ok else 1)


main()
