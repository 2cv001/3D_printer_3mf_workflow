# Copies sur le plateau : garder / supprimer, format QIDISlicer-Prusa (vrai projet PrusaSlicer --duplicate 3)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, FIX, OUT_ROOT

import os, re, sys, shutil, zipfile, subprocess
import FreeCAD, Part

S = OUT_ROOT
LOG = open(os.path.join(S, "test_copies_prusa.txt"), "w", encoding="utf-8")


def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")
    LOG.flush()



BASE = os.path.join(FIX, "prusa_copies.3mf")
PRUSA = r"C:/Program Files/Prusa3D/PrusaSlicer/prusa-slicer-console.exe"
OUT = os.path.join(S, "out_copies")
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
src = open(MACRO, encoding="utf-8").read()
src = re.sub(r"^run_macro\(\)\s*$", "pass", src, count=1, flags=re.M)

doc = FreeCAD.newDocument("CP")
A = doc.addObject("Part::Feature", "AdaptateurPhareHarley")   # même nom que l'objet du projet
A.Shape = Part.makeBox(30, 20, 10)
doc.recompute()
doc.saveAs(os.path.join(OUT, "proj.FCStd"))
FAILS = []
asked = []


def expect(c, m):
    log(("OK   " if c else "FAIL ") + m)
    if not c:
        FAILS.append(m)


def run(base3mf, answer):
    ns = {"__file__": MACRO, "__name__": "macro_under_test"}
    exec(compile(src, MACRO, "exec"), ns)
    ns["show_message"] = lambda t, m: None
    ns["ask_incompatible_slicer_dialog"] = lambda a, b: "cancel"
    ns["ask_losses_dialog"] = lambda l: True
    ns["ask_heavy_mesh_dialog"] = lambda n, s: True
    ns["ask_copies_dialog"] = lambda c, l=(): (asked.append(c), answer)[1]
    base = os.path.join(OUT, "AdaptateurPhareHarley")
    ns["prepare_environment"] = lambda: ({}, doc, [A], ["AdaptateurPhareHarley"], base, base + ".3mf",
                                         base + ".old.3mf", os.path.exists(base + ".3mf"))
    ns["get_user_options"] = lambda *a: (False, "C:/x/QIDISlicer/QIDISlicer.exe", base3mf, False,
                                         0.1, 0.3, False, [])
    ns["run_macro"]()
    return base + ".3mf"


def describe(path):
    z = zipfile.ZipFile(path)
    m = z.read("3D/3dmodel.model").decode()
    c = z.read("Metadata/Slic3r_PE_model.config").decode()
    objs = re.findall(r'<object id="(\d+)"[^>]*>', m)
    meshes = [o for o in re.findall(r'<object id="(\d+)"[^>]*>(?:(?!</object>).)*<mesh', m, re.S)]
    items = re.findall(r'<item objectid="(\d+)" transform="([^"]*)"', m)
    inst = re.findall(r'instances_count="(\d+)"', c)
    return objs, meshes, items, inst


def prusa_info(path):
    r = subprocess.run([PRUSA, "--datadir", os.path.join(S, "psdata"), "--info", path],
                       capture_output=True, text=True, timeout=120)
    return r.returncode, re.findall(r"size_x = ([\d.]+)", r.stdout), r.stdout.count("[")


log("base :", describe(BASE))
for answer in ("keep", "remove"):
    asked.clear()
    base_copy = os.path.join(OUT, f"base_{answer}.3mf")
    shutil.copy(BASE, base_copy)
    out = run(base_copy, answer)
    objs, meshes, items, inst = describe(out)
    log(f"--- {answer} : objets {objs}, maillages {meshes}, items {[i for i, _ in items]}, instances_count {inst}")
    for oid, t in items:
        log("     item", oid, t)
    expect(asked and asked[0][0][1] == 3, f"{answer} : question posée avec 3 exemplaires ({asked})")
    expect(meshes == ["1"], f"{answer} : le maillage partagé est toujours là")
    if answer == "keep":
        expect(len(items) == 3 and inst == ["3"], f"keep : 3 exemplaires gardés")
    else:
        expect(len(items) == 1 and inst == ["1"] and objs == ["1"], f"remove : un seul exemplaire")
    code, sizes, n = prusa_info(out)
    log(f"     PrusaSlicer --info : code {code}, size_x {sizes}")
    expect(code == 0 and sizes and all(abs(float(x) - 30) < 0.01 for x in sizes),
           f"{answer} : PrusaSlicer relit le fichier, nouvelle géométrie (30 mm)")
    shutil.copy(out, os.path.join(OUT, f"result_{answer}.3mf"))

# Objet inchangé : copies gardées sans question
asked.clear()
keep_out = os.path.join(OUT, "result_keep.3mf")
shutil.copy(keep_out, os.path.join(OUT, "AdaptateurPhareHarley.3mf"))
out = run(os.path.join(OUT, "AdaptateurPhareHarley.3mf"), "remove")
objs, meshes, items, inst = describe(out)
expect(not asked and len(items) == 3, f"inchangé : pas de question, 3 exemplaires gardés ({asked}, {len(items)})")

log("ÉCHECS :", FAILS if FAILS else "aucun")
