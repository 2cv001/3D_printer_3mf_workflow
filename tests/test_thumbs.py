import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, FIX, OUT_ROOT

import os, re, sys, shutil, math, time
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
import FreeCAD, Part
from PySide import QtGui, QtCore

S = OUT_ROOT
LOG = open(os.path.join(S, "test_thumbs.txt"), "w", encoding="utf-8")


def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")
    LOG.flush()


app = QtGui.QApplication.instance() or QtGui.QApplication([])


OUT = os.path.join(S, "out_thumbs")
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
for f in ("bambu.3mf", "cura.3mf", "freecad.3mf", "qidislicer.3mf", "qidistudio9obj.3mf", "superslicer.3mf"):
    shutil.copy(os.path.join(FIX, f), os.path.join(OUT, f))
open(os.path.join(OUT, "casse.3mf"), "w").write("pas un zip")

src = open(MACRO, encoding="utf-8").read()
src = re.sub(r"^run_macro\(\)\s*$", "pass", src, count=1, flags=re.M)
ns = {"__file__": MACRO, "__name__": "macro_under_test"}
exec(compile(src, MACRO, "exec"), ns)
ns["INI_FILE"] = os.path.join(OUT, "none.ini")
ns["get_user_language"] = lambda: "fr"

for f in sorted(os.listdir(OUT)):
    data = ns["base3mf_thumbnail"](os.path.join(OUT, f))
    log(f"{f:22} vignette : {len(data) if data else None}")

state = {}


def drive():
    dlg = [w for w in QtGui.QApplication.topLevelWidgets() if isinstance(w, QtGui.QDialog) and w.isVisible()]
    if not dlg:
        QtCore.QTimer.singleShot(50, drive)
        return
    dlg = dlg[0]
    combo = [c for c in dlg.findChildren(QtGui.QComboBox)][0]
    # attendre le chargement des icônes
    QtCore.QCoreApplication.processEvents()
    time.sleep(0.2)
    for _ in range(50):
        QtCore.QCoreApplication.processEvents()
    with_icon = []
    for i in range(combo.count()):
        ic = combo.itemIcon(i)
        img = ic.pixmap(40, 40).toImage()
        opaque = any(img.pixelColor(x, y).alpha() > 0 for x in range(0, 40, 4) for y in range(0, 40, 4))
        with_icon.append((combo.itemText(i).split("   ")[0], opaque))
    state["icons"] = with_icon
    dlg.adjustSize()
    dlg.grab().save(os.path.join(S, "thumbs_dialog.png"))
    combo.showPopup()
    for _ in range(20):
        QtCore.QCoreApplication.processEvents()
    combo.view().window().grab().save(os.path.join(S, "thumbs_popup.png"))
    combo.hidePopup()
    dlg.reject()


doc = FreeCAD.newDocument("T")
A = doc.addObject("Part::Feature", "A")
A.Shape = Part.makeBox(10, 10, 10)
doc.recompute()
QtCore.QTimer.singleShot(50, drive)
t0 = time.perf_counter()
ns["ask_user_options"]("C:/x/QIDIStudio/QIDIStudio.exe", 0.05, math.radians(3), False,
                       os.path.join(OUT, "A.3mf"), [], ["A"], [A])
log("fenêtre en", f"{time.perf_counter() - t0:.2f}s")
for name, has in state.get("icons", []):
    log(f"  {name:28} icône : {'oui' if has else 'non'}")
