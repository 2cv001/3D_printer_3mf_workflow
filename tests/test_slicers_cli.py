# Scénarios multi-objets famille QIDIStudio / Bambu / Orca, à partir de projets
# enregistrés par l'interface, vérifiés en les faisant relire par les slicers (CLI).
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, FIX, OUT_ROOT

import os, re, sys, shutil, zipfile, subprocess, traceback
import FreeCAD, Part
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

S = OUT_ROOT
sys.path.insert(0, S)
import world



OUT = os.path.join(S, "out_multi_qidi")
EXES = {
    "QIDIStudio": r"C:\Program Files\QIDIStudio\qidi-studio.exe",
    "BambuStudio": r"C:\Program Files\Bambu Studio\bambu-studio.exe",
    "OrcaSlicer": r"C:\Program Files\OrcaSlicer\orca-slicer.exe",
}
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)

src = open(MACRO, encoding="utf-8").read()
src = re.sub(r"^run_macro\(\)\s*$", "pass", src, count=1, flags=re.M)

doc = FreeCAD.newDocument("Q")
A = doc.addObject("Part::Feature", "A")
A.Shape = Part.makeBox(30, 20, 10)
B = doc.addObject("Part::Feature", "B")
B.Shape = Part.makeCylinder(5, 15, FreeCAD.Vector(40, 0, 0))
P = doc.addObject("App::Part", "P")
P.Placement = FreeCAD.Placement(FreeCAD.Vector(100, 0, 0), FreeCAD.Rotation(90, 0, 0))
C = doc.addObject("Part::Feature", "C")
C.Shape = Part.makeBox(30, 10, 5)
P.addObject(C)
doc.recompute()
doc.saveAs(os.path.join(OUT, "proj.FCStd"))
OBJ = {"A": A, "B": B, "C": C}
losses_seen = []
FAILS = []


def run(names, keep=True, base3mf=None):
    ns = {"__file__": MACRO, "__name__": "macro_under_test"}
    exec(compile(src, MACRO, "exec"), ns)
    ns["show_message"] = lambda t, m: print("MSG:", t, "|", str(m)[:300])
    ns["ask_incompatible_slicer_dialog"] = lambda a, b: (print("DIALOG incompatible", a, b), "cancel")[1]
    ns["ask_copies_dialog"] = lambda c, l=(): (print("   DIALOG copies", c), "keep")[1]
    ns["ask_heavy_mesh_dialog"] = lambda n, s: True
    ns["ask_losses_dialog"] = lambda l: (losses_seen.append(l), print("   DIALOG pertes", l), True)[2]
    base = os.path.join(OUT, "_".join(names))
    ns["prepare_environment"] = lambda: ({}, doc, [OBJ[n] for n in names], list(names), base,
                                         base + ".3mf", base + ".old.3mf", os.path.exists(base + ".3mf"))
    ns["get_user_options"] = lambda cfg, fc, *a: (False, "C:/x/QIDIStudio/QIDIStudio.exe", base3mf or (fc if os.path.exists(fc) else ""), False,
                                             0.05, 0.1, not keep, [])
    ns["run_macro"]()
    return base + ".3mf"


def check(path, exes=("QIDIStudio",), expect=None):
    w = world.world(path)
    world.show(path)
    names = sorted(str(o["name"]) for o in w)
    if expect is not None and names != sorted(expect):
        FAILS.append(f"{os.path.basename(path)}: objets {names} au lieu de {sorted(expect)}")
    for o in w:
        if abs(o["min"][2]) > 1e-3:
            FAILS.append(f"{os.path.basename(path)}: {o['name']} pas posé (zmin={o['min'][2]})")
    for e in exes:
        out = path + f".{e}.3mf"
        r = subprocess.run([EXES[e], "--arrange", "0", "--export-3mf", out, path],
                           capture_output=True, text=True, errors="replace", timeout=240)
        ok = r.returncode == 0 and os.path.exists(out)
        print(f"   relu par {e} : {'OK' if ok else 'ÉCHEC (code %s)' % r.returncode}")
        if not ok:
            FAILS.append(f"{os.path.basename(path)} non relu par {e}")
        else:
            w2 = world.world(out)
            n2 = sorted(str(o["name"]) for o in w2)
            if n2 != names:
                FAILS.append(f"{e} relit {n2} au lieu de {names}")
                print("   ", e, "relit", n2)
    return w


def rename_objects(path, mapping):
    """Renomme des objets (id → nom) dans model_settings.config, comme l'aurait fait la macro."""
    z = zipfile.ZipFile(path)
    entries = {i.filename: z.read(i.filename) for i in z.infolist()}
    z.close()
    cfg = entries["Metadata/model_settings.config"].decode("utf-8")
    for oid, name in mapping.items():
        m = re.search(r'<object id="%s">.*?</object>' % oid, cfg, re.S)
        blk = re.sub(r'(key="name" value=")[^"]*(")', r'\g<1>%s\g<2>' % name, m.group(0))
        cfg = cfg[:m.start()] + blk + cfg[m.end():]
    entries["Metadata/model_settings.config"] = cfg.encode("utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zo:
        for k, v in entries.items():
            zo.writestr(k, v)


def section(t):
    print("\n=====", t)


try:
    # ---------- Projet QIDIStudio à 2 objets qui partagent le même maillage ----------
    section("QIDIStudio 2 objets (maillage partagé) renommés A et B")
    base = os.path.join(OUT, "A_B.3mf")
    shutil.copy(os.path.join(FIX, "qidistudio.3mf"), base)
    rename_objects(base, {"2": "A", "3": "B"})
    check(base)
    p = run(["A", "B"])
    section("1. A et B remplacés, positions gardées")
    w = check(p, expect=["A", "B"])
    sizes = {o["name"]: tuple(round(b - a, 2) for a, b in zip(o["min"], o["max"])) for o in w}
    print("   tailles :", sizes)
    if sizes.get("A") == sizes.get("B"):
        FAILS.append("A et B ont le même maillage (maillage partagé non séparé)")

    section("2. peinture sur B")
    z = zipfile.ZipFile(p)
    files = sorted(n for n in z.namelist() if n.startswith("3D/Objects/"))
    z.close()
    print("   fichiers de maillage :", files)
    entries = {}
    with zipfile.ZipFile(p) as z:
        entries = {i.filename: z.read(i.filename) for i in z.infolist()}
    tgt = files[-1]
    entries[tgt] = re.sub(rb'(<triangle v1="\d+" v2="\d+" v3="\d+")', rb'\1 paint_supports="4"',
                          entries[tgt], count=1)
    with zipfile.ZipFile(p, "w") as zo:
        for k, v in entries.items():
            zo.writestr(k, v)
    # B inchangé : sa peinture est gardée, sans avertissement
    losses_seen.clear()
    p_same = run(["A", "B"])
    print("   B inchangé, fenêtre pertes :", losses_seen)
    if losses_seen:
        FAILS.append("avertissement pour un objet inchangé (QIDIStudio)")
    # B modifié : avertissement pour B seulement
    B.Shape = Part.makeCylinder(6, 15, FreeCAD.Vector(40, 0, 0))
    doc.recompute()
    losses_seen.clear()
    p = run(["A", "B"])
    print("   B modifié, fenêtre pertes :", losses_seen)
    if not losses_seen or sorted({n for l in losses_seen for n, _ in l}) != ["B"]:
        FAILS.append("peinture de B modifié non détectée, ou A signalé à tort (QIDIStudio)")
    check(p, expect=["A", "B"])

    section("3. ajout de C (dans une App::Part tournée), base A_B.3mf")
    p3 = run(["A", "B", "C"], base3mf=p)
    w = check(p3, expect=["A", "B", "C"])
    c = [o for o in w if o["name"] == "C"][0]
    size = [round(b - a, 3) for a, b in zip(c["min"], c["max"])]
    print("   taille de C :", size, "(attendu 10 x 30 x 5)")
    if abs(size[0] - 10) > 0.01 or abs(size[1] - 30) > 0.01:
        FAILS.append("placement global de C incorrect")

    section("4. retrait de B, base A_B_C.3mf")
    p4 = run(["A", "C"], base3mf=p3)
    check(p4, expect=["A", "C"])

    section("5. position ignorée")
    p5 = run(["A", "C"], keep=False)
    check(p5, expect=["A", "C"])

    # ---------- Projet QIDIStudio à 9 objets ----------
    section("6. projet à 9 objets, 2 renommés A et B : les 7 autres sont retirés")
    base = os.path.join(OUT, "A_B.3mf")
    for f in os.listdir(OUT):
        if f.startswith("A_B"):
            os.remove(os.path.join(OUT, f))
    shutil.copy(os.path.join(FIX, "qidistudio9obj.3mf"), base)
    rename_objects(base, {"2": "A", "4": "B"})
    p = run(["A", "B"])
    check(p, expect=["A", "B"])
    with zipfile.ZipFile(p) as z:
        print("   fichiers de maillage restants :", sorted(n for n in z.namelist() if n.startswith("3D/Objects/")))

    # ---------- Projet Bambu Studio ----------
    section("7. projet Bambu Studio (1 objet renommé A) + B + C ajoutés")
    for f in os.listdir(OUT):
        if f.startswith("A"):
            os.remove(os.path.join(OUT, f))
    base = os.path.join(OUT, "A.3mf")
    shutil.copy(os.path.join(FIX, "bambu.3mf"), base)
    rename_objects(base, {"2": "A"})
    p = run(["A", "B", "C"], base3mf=base)
    check(p, exes=("BambuStudio", "OrcaSlicer", "QIDIStudio"), expect=["A", "B", "C"])

    # ---------- Objet repris sous un autre nom : renommé ----------
    section("8. projet QIDIStudio à 1 objet nommé « Truc », sélection A : Truc renommé A")
    for f in os.listdir(OUT):
        if f.startswith("A"):
            os.remove(os.path.join(OUT, f))
    base = os.path.join(OUT, "A.3mf")
    shutil.copy(os.path.join(FIX, "bambu.3mf"), base)
    rename_objects(base, {"2": "Truc"})
    p = run(["A"])
    check(p, exes=("QIDIStudio", "BambuStudio"), expect=["A"])
    with zipfile.ZipFile(p) as z:
        if b"Truc" in z.read("Metadata/model_settings.config"):
            FAILS.append("ancien nom resté dans model_settings.config")
    section("9. A+B avec A.3mf comme base : A reconnu par son nom (pas supprimé)")
    p = run(["A", "B"], base3mf=p)
    check(p, expect=["A", "B"])
except Exception:
    traceback.print_exc()
    FAILS.append("exception")

print("\n" + ("TOUS LES SCÉNARIOS SONT PASSÉS" if not FAILS else "ÉCHECS :\n  - " + "\n  - ".join(FAILS)))
