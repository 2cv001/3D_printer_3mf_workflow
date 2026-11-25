# Lance tous les bancs d'essai avec freecadcmd et affiche le bilan.
# Usage : python tests/run_all.py [nom_du_test ...]
#   FREECADCMD=chemin\vers\freecadcmd.exe pour un autre FreeCAD.
import os, sys, glob, re, subprocess, time

TESTS = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(TESTS, "out")
CANDIDATES = [os.environ.get("FREECADCMD", ""),
              r"C:\Program Files\FreeCAD\bin\freecadcmd.exe",
              r"C:\Program Files\FreeCAD 1.1\bin\freecadcmd.exe",
              "/usr/bin/freecadcmd", "/usr/bin/FreeCADCmd"]
FREECADCMD = next((c for c in CANDIDATES if c and os.path.exists(c)), None)
if not FREECADCMD:
    sys.exit("freecadcmd introuvable : indiquez-le avec la variable FREECADCMD")

wanted = sys.argv[1:]
tests = sorted(glob.glob(os.path.join(TESTS, "test_*.py")))
if wanted:
    tests = [t for t in tests if any(w in os.path.basename(t) for w in wanted)]

os.makedirs(OUT, exist_ok=True)
summary = []
for t in tests:
    name = os.path.splitext(os.path.basename(t))[0]
    start = time.time()
    try:
        r = subprocess.run([FREECADCMD, t], capture_output=True, text=True, errors="replace", timeout=900)
        output = r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        output = "TIMEOUT"
    # Journaux écrits par le test pendant son exécution
    for log in glob.glob(os.path.join(OUT, "*.txt")):  # (les .log sont écrits par ce script)
        if os.path.getmtime(log) >= start:
            output += "\n" + open(log, encoding="utf-8", errors="replace").read()
    with open(os.path.join(OUT, name + ".log"), "w", encoding="utf-8") as f:
        f.write(output)
    fails = [l.strip() for l in output.splitlines() if l.strip().startswith("FAIL")]
    # Bilan sous forme de liste (« ÉCHECS :\n  - … »)
    for block in re.findall(r"ÉCHECS :\n((?:[ \t]+- .*(?:\n|$))+)", output):
        fails += ["FAIL " + l.strip()[2:] for l in block.splitlines() if l.strip()]
    crash = (output == "TIMEOUT" or any(k in output for k in ("Traceback", "Exception while processing file",
                                                             "Abnormal program termination")))
    status = "PLANTAGE" if crash else ("ÉCHEC" if fails else "ok")
    summary.append((name, status, len(fails), time.time() - start))
    print(f"{name:28} {status:9} {len(fails)} échec(s)  {time.time() - start:5.0f} s", flush=True)
    for f in fails[:10]:
        print("      " + f)
    if crash:
        for l in [l for l in output.splitlines() if any(k in l for k in ("Exception", "Error", "Abnormal", "QWidget"))][:5]:
            print("      " + l)

bad = [s for s in summary if s[1] != "ok"]
print()
print("Bilan :", "tout est bon" if not bad else f"{len(bad)} test(s) en échec : " + ", ".join(s[0] for s in bad))
sys.exit(1 if bad else 0)
