import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, FIX, OUT_ROOT

import os, re, sys, math, time
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
import FreeCAD, Part
from PySide import QtGui, QtCore

S = OUT_ROOT
LOG = open(os.path.join(S, "test_preview.txt"), "w", encoding="utf-8")


def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")
    LOG.flush()


app = QtGui.QApplication.instance() or QtGui.QApplication([])

src = open(MACRO, encoding="utf-8").read()
src = re.sub(r"^run_macro\(\)\s*$", "pass", src, count=1, flags=re.M)
ns = {"__file__": MACRO, "__name__": "macro_under_test"}
exec(compile(src, MACRO, "exec"), ns)
ns["DEBUG"] = True

doc = FreeCAD.newDocument("P")
# Support percé avec congés
base = Part.makeBox(80, 50, 10)
base = base.cut(Part.makeCylinder(6, 20, FreeCAD.Vector(20, 25, -5)))
base = base.cut(Part.makeCylinder(6, 20, FreeCAD.Vector(60, 25, -5)))
wall = Part.makeBox(10, 50, 40, FreeCAD.Vector(0, 0, 10))
bracket = base.fuse(wall).removeSplitter()
A = doc.addObject("Part::Feature", "Support")
A.Shape = bracket
# Tore dans une App::Part tournée
P = doc.addObject("App::Part", "Assemblage")
P.Placement = FreeCAD.Placement(FreeCAD.Vector(120, 0, 0), FreeCAD.Rotation(0, 45, 0))
B = doc.addObject("Part::Feature", "Anneau")
B.Shape = Part.makeTorus(20, 6)
P.addObject(B)
C = doc.addObject("Part::Feature", "Boule")
C.Shape = Part.makeSphere(15, FreeCAD.Vector(40, 80, 15))
doc.recompute()

for name, sel in (("un", [A]), ("trois", [A, B, C])):
    t0 = time.perf_counter()
    pix = ns["render_selection_preview"](sel)
    log(f"{name}: {'ok' if pix else 'ÉCHEC'} en {time.perf_counter() - t0:.3f}s")
    if pix:
        pix.scaled(360, 260, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation).save(
            os.path.join(S, f"preview_{name}.png"))

# Fenêtre complète
def drive():
    dlg = [w for w in QtGui.QApplication.topLevelWidgets() if isinstance(w, QtGui.QDialog) and w.isVisible()]
    if not dlg:
        QtCore.QTimer.singleShot(50, drive)
        return
    for _ in range(30):
        QtCore.QCoreApplication.processEvents()
    dlg[0].adjustSize()
    dlg[0].grab().save(os.path.join(S, "preview_dialog.png"))
    dlg[0].reject()

ns["INI_FILE"] = os.path.join(S, "none.ini")
ns["get_user_language"] = lambda: "fr"
QtCore.QTimer.singleShot(50, drive)
t0 = time.perf_counter()
ns["ask_user_options"]("C:/x/QIDIStudio/QIDIStudio.exe", 0.05, math.radians(3), False,
                       os.path.join(S, "Anneau_Boule_Support.3mf"), [],
                       ["Anneau", "Boule", "Support"], [B, C, A])
log("fenêtre en", f"{time.perf_counter() - t0:.2f}s")
