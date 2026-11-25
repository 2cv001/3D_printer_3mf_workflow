import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, FIX, OUT_ROOT

import os, re, sys, math, time
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import FreeCAD, Part
from PySide import QtGui, QtCore

S = OUT_ROOT
LOG = open(os.path.join(S, "test_colors.txt"), "w", encoding="utf-8")


def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")
    LOG.flush()


app = QtGui.QApplication.instance() or QtGui.QApplication([])

src = open(MACRO, encoding="utf-8").read()
src = re.sub(r"^run_macro\(\)\s*$", "pass", src, count=1, flags=re.M)
ns = {"__file__": MACRO, "__name__": "macro_under_test"}
exec(compile(src, MACRO, "exec"), ns)
ns["DEBUG"] = True


class Mat:
    def __init__(self, c):
        self.DiffuseColor = c


class VO:
    pass


class Fake:
    """Objet FreeCAD simulé : forme, placement global, vue (couleurs)."""

    def __init__(self, shape, vo, placement=None):
        self.Shape = shape
        self.Placement = FreeCAD.Placement()
        self._gp = placement or FreeCAD.Placement()
        self.ViewObject = vo

    def getGlobalPlacement(self):
        return self._gp


# 1) Apparence FreeCAD 1.x : un matériau pour tout l'objet (rouge)
vo1 = VO(); vo1.ShapeAppearance = [Mat((0.9, 0.1, 0.1, 0.0))]
box = Fake(Part.makeBox(40, 30, 20), vo1)
# 2) Apparence par face : 6 faces, dessus (face 6) en jaune, reste bleu
cube = Part.makeBox(25, 25, 25, FreeCAD.Vector(60, 0, 0))
vo2 = VO(); vo2.ShapeAppearance = [Mat((0.2, 0.4, 0.9, 0.0))] * 5 + [Mat((1.0, 0.85, 0.1, 0.0))]
cube_o = Fake(cube, vo2)
# 3) Ancienne propriété seulement (vert, entiers 0..255)
vo3 = VO(); vo3.ShapeColor = (40, 180, 60)
torus = Fake(Part.makeTorus(15, 5), vo3,
             FreeCAD.Placement(FreeCAD.Vector(20, 60, 10), FreeCAD.Rotation(0, 45, 0)))
# 4) Sans vue (gris)
sph = Fake(Part.makeSphere(10, FreeCAD.Vector(80, 60, 10)), None)

for o, label in ((box, "rouge"), (cube_o, "bleu+dessus jaune"), (torus, "vert"), (sph, "gris")):
    cols = ns["_face_colors"](o, len(o.Shape.Faces))
    log(f"{label:20} {len(cols)} faces, couleurs distinctes : {sorted(set(cols))}")

t0 = time.perf_counter()
pix = ns["render_selection_preview"]([box, cube_o, torus, sph])
log("aperçu", "ok" if pix else "ÉCHEC", f"{time.perf_counter() - t0:.3f}s")
if pix:
    pix.scaled(360, 260, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation).save(
        os.path.join(S, "preview_colors.png"))


# 5) Body PartDesign : Body gris par défaut, fonction visible colorée (comme dans FreeCAD 1.2)
class Feat:
    def __init__(self, color, visible, partdesign=True):
        self.ViewObject = VO()
        self.ViewObject.ShapeAppearance = [Mat(color)]
        self.ViewObject.Visibility = visible
        self._pd = partdesign

    def isDerivedFrom(self, t):
        return self._pd and t == "PartDesign::Feature"


class Body(Fake):
    def isDerivedFrom(self, t):
        return t == "PartDesign::Body"


sk = Feat((0.33, 0.67, 1.0, 1.0), False, partdesign=False)
pad_hidden = Feat((0.9, 0.1, 0.1, 1.0), False)
sphere_feat = Feat((0.18, 0.49, 0.51, 1.0), True)
vob = VO(); vob.ShapeAppearance = [Mat((0.8, 0.8, 0.9, 1.0))]
body = Body(Part.makeSphere(10), vob)
body.Group = [sk, pad_hidden, sphere_feat]
body.Tip = sphere_feat
log("Body (fonction visible) :", ns["_face_colors"](body, 1))
sphere_feat.ViewObject.Visibility = False
body.Tip = pad_hidden
log("Body (rien de visible → Tip) :", ns["_face_colors"](body, 1))
