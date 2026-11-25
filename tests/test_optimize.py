# Fenêtre d'options hors écran : estimation en direct, bouton « Optimiser la finesse »,
# puis export réel pour vérifier le recalage du temps.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, FIX, OUT_ROOT

import os, re, sys, shutil, math, time
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
import FreeCAD, Part
from PySide import QtGui, QtCore

S = OUT_ROOT
LOG = open(os.path.join(S, "test_optimize.txt"), "w", encoding="utf-8")


def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")
    LOG.flush()


app = QtGui.QApplication.instance() or QtGui.QApplication([])

OUT = os.path.join(S, "out_optimize")
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
INI = os.path.join(OUT, "test.ini")
open(INI, "w", encoding="utf-8").write("[Settings]\nslicer_exe = C:/x/QIDIStudio/QIDIStudio.exe\n")

src = open(MACRO, encoding="utf-8").read()
src = re.sub(r"^run_macro\(\)\s*$", "pass", src, count=1, flags=re.M)
ns = {"__file__": MACRO, "__name__": "macro_under_test"}
exec(compile(src, MACRO, "exec"), ns)
ns["INI_FILE"] = INI
ns["get_user_language"] = lambda: "fr"
FAILS = []


def expect(c, m):
    log(("OK   " if c else "FAIL ") + m)
    if not c:
        FAILS.append(m)


doc = FreeCAD.newDocument("O")
A = doc.addObject("Part::Feature", "A")
A.Shape = Part.makeSphere(50)
B = doc.addObject("Part::Feature", "B")
x = Part.makeBox(60, 40, 20)
B.Shape = x.makeFillet(4, x.Edges)
doc.recompute()
doc.saveAs(os.path.join(OUT, "proj.FCStd"))

# ---- Fenêtre : on pilote les widgets pendant qu'elle est ouverte ----
state = {}


def drive():
    dlg = [w for w in QtGui.QApplication.topLevelWidgets() if isinstance(w, QtGui.QDialog) and w.isVisible()]
    if not dlg:
        QtCore.QTimer.singleShot(50, drive)
        return
    dlg = dlg[0]
    labels = [l for l in dlg.findChildren(QtGui.QLabel) if "Temps export" in l.text()]
    spins = dlg.findChildren(QtGui.QDoubleSpinBox)
    spin_lin = next(sp for sp in spins if sp.maximum() == 10.0)
    spin_ang = next(sp for sp in spins if sp.maximum() == 90.0)
    target = dlg.findChildren(QtGui.QSpinBox)
    target = [t for t in target if not isinstance(t, QtGui.QDoubleSpinBox)][0]
    btn = [b for b in dlg.findChildren(QtGui.QPushButton) if b.text() == "Optimiser la finesse"][0]
    if not btn.isEnabled():
        QtCore.QTimer.singleShot(50, drive)
        return
    lbl = labels[0]
    if "triangles" not in lbl.text():
        QtCore.QTimer.singleShot(50, drive)
        return
    dlg.adjustSize()
    dlg.grab().save(os.path.join(S, "dialog_initial.png"))
    state["initial"] = (spin_lin.value(), spin_ang.value(), lbl.text(), lbl.styleSheet())
    # Changement en direct
    spin_ang.setValue(1.0)
    state["live_1deg"] = (lbl.text(), lbl.styleSheet())
    spin_ang.setValue(0.2)
    dlg.grab().save(os.path.join(S, "dialog_heavy.png"))
    spin_ang.setValue(3.0)
    # Optimisation pour 20 s puis 2 s puis 600 s
    for t in (20, 2, 600):
        target.setValue(t)
        btn.click()
        state[f"opt_{t}"] = (spin_lin.value(), spin_ang.value(), lbl.text())
    target.setValue(5)
    btn.click()
    state["final"] = (spin_lin.value(), spin_ang.value(), lbl.text())
    dlg.accept()


QtCore.QTimer.singleShot(50, drive)
t0 = time.perf_counter()
res = ns["ask_user_options"]("C:/x/QIDIStudio/QIDIStudio.exe", 0.05, math.radians(3), False,
                             os.path.join(OUT, "A_B.3mf"), [], ["A", "B"], [A, B])
log("dialogue en", f"{time.perf_counter() - t0:.2f}s")
for k, v in state.items():
    log(k, v)

expect("Temps export : ~" in state["initial"][2] and "triangles" in state["initial"][2], "estimation affichée à l'ouverture")
expect(state["live_1deg"][0] != state["initial"][2], "l'estimation change en direct (angle 1°)")
lin20, ang20, _ = state["opt_20"]
expect(lin20 >= 0.01 and ang20 >= 2.0, f"20 s : planchers respectés ({lin20} mm, {ang20}°)")
lin2, ang2, _ = state["opt_2"]
expect(lin2 >= lin20 and ang2 >= ang20, f"2 s : plus grossier que pour 20 s ({lin2}, {ang2})")
lin600, ang600, _ = state["opt_600"]
expect((lin600, ang600) == (0.01, 2.0), f"600 s : planchers atteints ({lin600}, {ang600})")
expect(res is not None and abs(res[4] - state["final"][0]) < 1e-9, "les valeurs optimisées sont celles renvoyées")
ini = open(INI, encoding="utf-8").read()
expect("target_export_seconds = 5" in ini, "temps visé mémorisé dans le ini")

# ---- Export réel avec les valeurs de l'optimisation à 5 s : temps réel vs estimé ----
lin, ang = state["final"][0], math.radians(state["final"][1])
model = ns["cached_mesh_cost_model"]([A, B])
n_est, t_est = model.estimate(lin, ang)
t0 = time.perf_counter()
parts, _ = ns["mesh_selection"]([A, B], ["A", "B"], lin, ang)
t_real = time.perf_counter() - t0
n_real = sum(len(p.triangles) for p in parts)
log(f"5 s visés → {lin} mm {math.degrees(ang):.2f}° : estimé {n_est} tri {t_est:.1f}s, réel {n_real} tri {t_real:.1f}s")
expect(t_real < 5 * 3, "le temps réel reste du même ordre que le temps visé")

# ---- Recalage ----
before = ns["get_mesh_time_factor"]()
ns["update_mesh_time_factor"](model, lin, ang, t_real)
after = ns["get_mesh_time_factor"]()
log(f"recalage : {before:.3f} → {after:.3f}")
expect("mesh_time_factor" in open(INI, encoding="utf-8").read() or t_est < 2,
       "facteur de recalage enregistré (si le maillage est assez long)")

log("ÉCHECS :", FAILS if FAILS else "aucun")
