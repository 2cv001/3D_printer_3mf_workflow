# Document jamais enregistré (enregistrer / dossier temporaire / annuler), récupération
# du 3MF après enregistrement, ménage des dossiers temporaires, et dossier du projet
# inaccessible (bug FreeCAD d'« Enregistrer sous » refusé)
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, FIX, OUT_ROOT

import re, shutil
import FreeCAD, Part

OUT = os.path.join(OUT_ROOT, "out_unsaved")
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
LOG = open(os.path.join(OUT_ROOT, "test_unsaved.txt"), "w", encoding="utf-8")
FAILS = []


def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")
    LOG.flush()


def expect(c, m):
    log(("OK   " if c else "FAIL ") + m)
    if not c:
        FAILS.append(m)


src = open(MACRO, encoding="utf-8").read()
src = re.sub(r"^run_macro\(\)\s*$", "pass", src, count=1, flags=re.M)
messages = []


class FakeGui:
    """Remplace FreeCADGui : « Enregistrer sous » simulé."""
    def __init__(self, doc, target):
        self.doc, self.target = doc, target

    def runCommand(self, name, arg=0):
        if name == "Std_SaveAs" and self.target:
            self.doc.saveAs(self.target)


def load(doc, obj, answer, save_target=None):
    ns = {"__file__": MACRO, "__name__": "macro_under_test"}
    exec(compile(src, MACRO, "exec"), ns)
    ns["show_message"] = lambda t, m: messages.append(m)
    ns["ask_unsaved_dialog"] = lambda d: answer
    ns["get_valid_selection"] = lambda: [obj]
    ns["ask_heavy_mesh_dialog"] = lambda n, s: True
    ns["FreeCADGui"] = FakeGui(doc, save_target)
    ns["get_user_options"] = lambda *a: (False, "C:/x/QIDIStudio/QIDIStudio.exe",
                                         "", False, 0.1, 0.3, False, [])
    ns["launch_slicer_if_needed"] = lambda *a: None
    return ns


# ---------- 1) Document jamais enregistré → dossier temporaire ----------
doc = FreeCAD.newDocument("Essai_non_enregistre")
A = doc.addObject("Part::Feature", "Cube")
A.Shape = Part.makeBox(10, 10, 10)
doc.recompute()
FreeCAD.setActiveDocument(doc.Name)
ns = load(doc, A, "temp")
temp_dir = ns["temporary_folder"](doc)
shutil.rmtree(temp_dir, ignore_errors=True)
expect(os.path.basename(temp_dir).startswith(f"{os.getpid()}_"), f"dossier temporaire propre à la session ({temp_dir})")
env = ns["prepare_environment"]()
expect(env is not None and os.path.dirname(env[5]) == temp_dir, "temporaire : 3MF prévu dans le dossier temporaire")
ns["export_replace_geometry"]()
expect(os.path.exists(os.path.join(temp_dir, "Cube.3mf")), "temporaire : 3MF créé dans le dossier temporaire")
expect(ns["project_path"](doc).startswith(temp_dir), "temporaire : %PROJECT% pointe vers le dossier temporaire")
env = load(doc, A, "temp")["prepare_environment"]()
expect(env is not None and env[7], "temporaire : un nouvel export retrouve le 3MF existant")

# ---------- 2) Annuler ----------
expect(load(doc, A, "cancel")["prepare_environment"]() is None, "annuler : la macro s'arrête")

# ---------- 3) Enregistrement puis relance : récupération ----------
def temp_work(name):
    """Nouveau document « name » exporté dans son dossier temporaire (objet « Cube »)."""
    d = FreeCAD.newDocument(name)
    o = d.addObject("Part::Feature", "Cube")
    o.Shape = Part.makeBox(10, 10, 10)
    d.recompute()
    FreeCAD.setActiveDocument(d.Name)
    n = load(d, o, "temp")
    shutil.rmtree(n["temporary_folder"](d), ignore_errors=True)
    n["export_replace_geometry"]()
    return d, o, n["temporary_folder"](d)


def object_names(path):
    n = load(doc, A, "temp")
    return sorted(so.name for so in n["analyse_slicer_objects"](n["read_3mf_entries"](path)))


def save_folder(tag, with_old):
    d = os.path.join(OUT, tag)
    os.makedirs(d)
    if with_old:
        with open(os.path.join(d, "Cube.3mf"), "wb") as f:
            f.write(b"ancien")
    return d


# a) Sans conflit : récupération directe
d1, o1, t1 = temp_work("Sans_conflit")
dest1 = save_folder("sans_conflit", False)
n = load(d1, o1, "save", os.path.join(dest1, "Doc.FCStd"))
messages.clear()
env = n["prepare_environment"]()
expect(env is not None and os.path.exists(os.path.join(dest1, "Cube.3mf")) and not os.path.exists(t1),
       "sans conflit : 3MF récupéré à côté du fichier, dossier temporaire effacé")
expect(messages and "Cube.3mf" in messages[-1], "sans conflit : message de récupération")
expect(env is not None and env[7], "sans conflit : l'export reprend ce 3MF (et ses réglages)")

# b) Conflit → Annuler : rien ne change, le travail reste en temporaire
d2, o2, t2 = temp_work("Conflit_annule")
dest2 = save_folder("conflit_annule", True)
n = load(d2, o2, "save", os.path.join(dest2, "Doc.FCStd"))
asked = []
n["ask_recover_conflict_dialog"] = lambda names: (asked.append(names), "cancel")[1]
expect(n["prepare_environment"]() is None, "conflit, annuler : la macro s'arrête")
expect(asked and asked[0] == ["Cube.3mf"], f"conflit : le fichier en conflit est nommé ({asked})")
expect(os.path.exists(os.path.join(t2, "Cube.3mf")), "conflit, annuler : le travail reste dans le dossier temporaire")
expect(open(os.path.join(dest2, "Cube.3mf"), "rb").read() == b"ancien", "conflit, annuler : l'ancien 3MF est intact")

# c) … puis l'objet est renommé dans FreeCAD : 3MF et objet renommés, plus de conflit
o2.Label = "Support"
d2.recompute()
n = load(d2, o2, "temp")
n["ask_recover_conflict_dialog"] = lambda names: (asked.append(("encore", names)), "cancel")[1]
asked.clear()
messages.clear()
env = n["prepare_environment"]()
expect(not asked, "renommé : plus de conflit")
support = os.path.join(dest2, "Support.3mf")
expect(os.path.exists(support) and object_names(support) == ["Support"],
       f"renommé : Support.3mf créé, objet renommé à l'intérieur ({object_names(support) if os.path.exists(support) else '-'})")
expect(open(os.path.join(dest2, "Cube.3mf"), "rb").read() == b"ancien", "renommé : l'ancien Cube.3mf est intact")
expect(not os.path.exists(t2), "renommé : dossier temporaire effacé")
expect(messages and "Support.3mf" in messages[-1], "renommé : le message indique Cube.3mf → Support.3mf")

# d) Conflit → Remplacer l'ancien : l'ancien est gardé en sauvegarde datée
d3, o3, t3 = temp_work("Conflit_remplace")
dest3 = save_folder("conflit_remplace", True)
n = load(d3, o3, "save", os.path.join(dest3, "Doc.FCStd"))
n["ask_recover_conflict_dialog"] = lambda names: "replace"
n["prepare_environment"]()
olds = [f for f in os.listdir(dest3) if f.startswith("Cube.old.") and f != "Cube.old.3mf"]
expect(open(os.path.join(dest3, "Cube.3mf"), "rb").read() != b"ancien", "remplacer : le travail temporaire remplace l'ancien")
expect(olds and open(os.path.join(dest3, olds[0]), "rb").read() == b"ancien", f"remplacer : l'ancien est en sauvegarde ({olds})")
expect(not os.path.exists(t3), "remplacer : dossier temporaire effacé")

# e) Conflit → Garder l'ancien : le travail temporaire est abandonné
d4, o4, t4 = temp_work("Conflit_garde")
dest4 = save_folder("conflit_garde", True)
n = load(d4, o4, "save", os.path.join(dest4, "Doc.FCStd"))
n["ask_recover_conflict_dialog"] = lambda names: "keep_old"
n["prepare_environment"]()
expect(open(os.path.join(dest4, "Cube.3mf"), "rb").read() == b"ancien", "garder l'ancien : l'ancien est intact")
expect(not os.path.exists(t4), "garder l'ancien : dossier temporaire effacé")

temp_dir = ns["temporary_folder"](doc)

# ---------- 4) Ménage des dossiers temporaires ----------
root = ns["TEMP_ROOT"]
stale = os.path.join(root, "999999_Unnamed")          # session fermée (processus inexistant)
mine = os.path.join(root, f"{os.getpid()}_Autre")      # cette session
for d in (stale, mine):
    os.makedirs(d, exist_ok=True)
ns["cleanup_stale_temp_folders"]()
expect(not os.path.exists(stale), "ménage : dossier d'une session fermée effacé")
expect(os.path.exists(mine), "ménage : dossier de la session en cours gardé")
ns["remove_session_temp_folders"]()
expect(not os.path.exists(mine) and not os.path.exists(temp_dir), "fermeture de FreeCAD : dossiers de la session effacés")

# ---------- 5) Dossier du projet disparu / inaccessible ----------
doc2 = FreeCAD.newDocument("Perdu")
B = doc2.addObject("Part::Feature", "Cube")
B.Shape = Part.makeBox(5, 5, 5)
doc2.recompute()
lost = os.path.join(OUT, "perdu", "Perdu.FCStd")
os.makedirs(os.path.dirname(lost))
doc2.saveAs(lost)
shutil.rmtree(os.path.dirname(lost))
FreeCAD.setActiveDocument(doc2.Name)
messages.clear()
ns = load(doc2, B, "temp")
expect(ns["prepare_environment"]() is None and messages and "perdu" in messages[-1],
       "dossier inaccessible : message et arrêt")
expect(not ns["folder_is_writable"](os.path.join(OUT, "n_existe_pas")), "dossier inexistant : non accessible")
expect(ns["folder_is_writable"](OUT), "dossier normal : accessible")
expect(not [f for f in os.listdir(OUT) if f.startswith(".3mf_workflow_write_test")], "aucun fichier d'essai laissé")

log("ÉCHECS :", FAILS if FAILS else "aucun")
