# Copies QIDIStudio (duplication = objets séparés de même nom, maillage partagé) : vrai fichier de l'utilisateur
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, FIX, OUT_ROOT

import os, re, sys, shutil, zipfile, subprocess
import FreeCAD, Part

S = OUT_ROOT
LOG = open(os.path.join(S, "test_copies_qidi.txt"), "w", encoding="utf-8")


def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")
    LOG.flush()



SRC = os.path.join(FIX, "qidistudio_copies.3mf")
BAMBU = r"C:/Program Files/Bambu Studio/bambu-studio.exe"
OUT = os.path.join(S, "out_copies_qidi")
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
BASE = os.path.join(OUT, "base_user.3mf")
shutil.copy(SRC, BASE)
src = open(MACRO, encoding="utf-8").read()
src = re.sub(r"^run_macro\(\)\s*$", "pass", src, count=1, flags=re.M)

doc = FreeCAD.newDocument("CQ")
A = doc.addObject("Part::Feature", "Body003")
A.Shape = Part.makeSphere(18)
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
    base = os.path.join(OUT, "Body003")
    ns["prepare_environment"] = lambda: ({}, doc, [A], ["Body003"], base, base + ".3mf",
                                         base + ".old.3mf", os.path.exists(base + ".3mf"))
    ns["get_user_options"] = lambda *a: (False, "C:/x/QIDIStudio/QIDIStudio.exe", base3mf, False,
                                         0.1, 0.3, False, [])
    ns["run_macro"]()
    return base + ".3mf"


def describe(path):
    z = zipfile.ZipFile(path)
    m = z.read("3D/3dmodel.model").decode()
    c = z.read("Metadata/model_settings.config").decode()
    return dict(
        objects=re.findall(r'<object id="(\d+)"', m),
        items=re.findall(r'<item objectid="(\d+)"[^>]*transform="([^"]*)"', m),
        cfg=re.findall(r'<object id="(\d+)">', c),
        plate=re.findall(r'key="object_id" value="(\d+)"', c),
        assemble=re.findall(r'<assemble_item object_id="(\d+)"', c))


def reread(path):
    """Bambu Studio relit le projet et le réenregistre : nombre d'objets placés."""
    out = path + ".bambu.3mf"
    subprocess.run([BAMBU, "--arrange", "0", "--export-3mf", out, path], capture_output=True, timeout=180)
    if not os.path.exists(out):
        return None
    m = zipfile.ZipFile(out).read("3D/3dmodel.model").decode()
    return len(re.findall(r"<item ", m))


log("base :", describe(BASE))
for answer in ("keep", "remove"):
    asked.clear()
    for f in os.listdir(OUT):
        if f.startswith("Body003"):
            os.remove(os.path.join(OUT, f))
    out = run(BASE, answer)
    d = describe(out)
    log(f"--- {answer} :", d)
    expect(asked and asked[0][0][1] == 3, f"{answer} : question avec 3 exemplaires ({asked})")
    n = 3 if answer == "keep" else 1
    expect(len(d["items"]) == n and len(d["cfg"]) == n and len(d["plate"]) == n and len(d["assemble"]) == n,
           f"{answer} : {n} exemplaire(s) partout (modèle, réglages, plateau, assemblage)")
    if answer == "keep":
        zs = {t.split()[-1] for _, t in d["items"]}
        expect(len(zs) == 1, f"keep : toutes les copies reposent sur le plateau ({zs})")
    cnt = reread(out)
    log(f"     Bambu Studio relit : {cnt} objet(s)")
    expect(cnt == n, f"{answer} : Bambu Studio relit {n} objet(s)")
    shutil.copy(out, os.path.join(OUT, f"result_{answer}.3mf"))

# Objet inchangé (même sphère que l'export « keep ») : pas de question, 3 exemplaires
asked.clear()
for f in os.listdir(OUT):
    if f.startswith("Body003"):
        os.remove(os.path.join(OUT, f))
shutil.copy(os.path.join(OUT, "result_keep.3mf"), os.path.join(OUT, "Body003.3mf"))
with zipfile.ZipFile(os.path.join(OUT, "Body003.3mf")) as z:
    before_entries = {n: z.read(n) for n in z.namelist()}
out = run(os.path.join(OUT, "Body003.3mf"), "remove")
d = describe(out)
expect(not asked and len(d["items"]) == 3, f"inchangé : pas de question, 3 exemplaires ({asked}, {len(d['items'])})")
def entries(path):
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist()}
expect(entries(out) == before_entries, "inchangé : contenu identique (fichier par fichier)")
log("ÉCHECS :", FAILS if FAILS else "aucun")
