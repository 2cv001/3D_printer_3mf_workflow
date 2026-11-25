# Objets inchangés laissés tels quels : test sur de vrais projets QIDIStudio et QIDISlicer
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, FIX, OUT_ROOT

import os, re, sys, shutil, zipfile
import FreeCAD, Part
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass



OUT = os.path.join(OUT_ROOT, "out_unchanged")
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)

src = open(MACRO, encoding="utf-8").read()
src = re.sub(r"^run_macro\(\)\s*$", "pass", src, count=1, flags=re.M)

doc = FreeCAD.newDocument("U")
A = doc.addObject("Part::Feature", "A")
A.Shape = Part.makeBox(30, 20, 10)
B = doc.addObject("Part::Feature", "B")
B.Shape = Part.makeCylinder(5, 15, FreeCAD.Vector(40, 0, 0))
doc.recompute()
doc.saveAs(os.path.join(OUT, "proj.FCStd"))
OBJ = {"A": A, "B": B}
FAILS = []
SLICER = ["C:/x/QIDIStudio/QIDIStudio.exe"]
last_losses = []


def load():
    ns = {"__file__": MACRO, "__name__": "macro_under_test"}
    exec(compile(src, MACRO, "exec"), ns)
    return ns


def run(names, base3mf, keep=True):
    ns = load()
    last_losses.clear()
    ns["show_message"] = lambda t, m: print("   MSG:", t, "|", str(m)[:200])
    ns["ask_incompatible_slicer_dialog"] = lambda a, b: "cancel"
    ns["ask_losses_dialog"] = lambda l: (last_losses.extend(l), True)[1]
    base = os.path.join(OUT, "_".join(names))
    ns["prepare_environment"] = lambda: ({}, doc, [OBJ[n] for n in names], list(names), base,
                                         base + ".3mf", base + ".old.3mf", os.path.exists(base + ".3mf"))
    ns["get_user_options"] = lambda *a: (False, SLICER[0], base3mf, False,
                                         0.05, 0.1, not keep, [])
    ns["run_macro"]()
    return base + ".3mf"


def objects(path):
    ns = load()
    with zipfile.ZipFile(path) as z:
        entries = {n: z.read(n) for n in z.namelist()}
    return ns, entries, {so.name: so for so in ns["analyse_slicer_objects"](entries)}


def paint(path, name):
    """Ajoute un réglage sur les faces (attribut de triangle) à l'objet `name`."""
    ns, entries, objs = objects(path)
    so = objs[name]
    t = entries[so.mesh_file].decode("utf-8")
    start, end = ns["_find_block"](t, ns["_OBJECT_RE"], "id", so.mesh_id)
    block = re.sub(r' paint_supports="4"', '', t[start:end])
    block = re.sub(r'<triangle ', '<triangle paint_supports="4" ', block, count=3)
    entries[so.mesh_file] = (t[:start] + block + t[end:]).encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n, d in entries.items():
            z.writestr(n, d)


def expect(cond, msg):
    print(("   OK   " if cond else "   FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


for fixture in ("qidistudio.3mf", "qidislicer.3mf"):
    print(f"=== {fixture}")
    SLICER[0] = "C:/x/QIDISlicer/QIDISlicer.exe" if "qidislicer" in fixture else "C:/x/QIDIStudio/QIDIStudio.exe"
    for f in os.listdir(OUT):
        if f.endswith(".3mf"):
            os.remove(os.path.join(OUT, f))
    A.Shape = Part.makeBox(30, 20, 10)
    B.Shape = Part.makeCylinder(5, 15, FreeCAD.Vector(40, 0, 0))
    doc.recompute()

    # 1) Projet du slicer repris pour A + B (B nouveau)
    out = run(["A", "B"], os.path.join(FIX, fixture))
    paint(out, "A")
    paint(out, "B")
    _, _, objs = objects(out)
    expect(objs["A"].painted and objs["B"].painted, "A et B ont des réglages sur les faces")

    # 2) Réexport sans rien changer : aucune perte, rien de modifié
    before = open(out, "rb").read()
    with zipfile.ZipFile(out) as z:
        before_entries = {n: z.read(n) for n in z.namelist()}
    run(["A", "B"], out)
    expect(not last_losses, f"rien changé : pas de fenêtre de pertes ({last_losses})")
    with zipfile.ZipFile(out) as z:
        after_entries = {n: z.read(n) for n in z.namelist()}
    expect(after_entries == before_entries, "rien changé : contenu du 3MF identique")

    # 3) B modifié seulement : pertes pour B seulement, A intact
    B.Shape = Part.makeCylinder(6, 15, FreeCAD.Vector(40, 0, 0))
    doc.recompute()
    run(["A", "B"], out)
    names_lost = sorted({n for n, _ in last_losses})
    expect(names_lost == ["B"], f"B modifié : pertes pour B seulement ({names_lost})")
    _, _, objs = objects(out)
    expect(objs["A"].painted, "A garde ses réglages sur les faces")
    expect(not objs["B"].painted, "B remplacé (réglages sur les faces perdus)")
    expect(abs((max(v[0] for v in objs["B"].old_vertices) - min(v[0] for v in objs["B"].old_vertices)) - 12) < 0.01,
           "B a bien la nouvelle géométrie (diamètre 12)")

    # 4) Option « Ne pas récupérer la position » : tout est remplacé
    paint(out, "A")
    run(["A", "B"], out, keep=False)
    names_lost = sorted({n for n, _ in last_losses})
    expect("A" in names_lost, f"ignore_transform : A remplacé aussi ({names_lost})")

    # 5) Précision changée : A remplacé
    paint(out, "A")
    ns = load()

print()
print("ÉCHECS :", FAILS if FAILS else "aucun")
