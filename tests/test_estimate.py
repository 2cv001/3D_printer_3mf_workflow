import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, FIX, OUT_ROOT

import time, math, sys, ast, re, os
import FreeCAD, Part, MeshPart

OUT = open(os.path.join(OUT_ROOT, "test_estimate.txt"), "w", encoding="utf-8")


def log(*a):
    OUT.write(" ".join(str(x) for x in a) + "\n")
    OUT.flush()



src = open(MACRO, encoding="utf-8").read()
src = re.sub(r"^run_macro\(\)\s*$", "pass", src, count=1, flags=re.M)
ns = {"__file__": MACRO, "__name__": "macro_under_test"}
exec(compile(src, MACRO, "exec"), ns)
ns["DEBUG"] = True


def estimate(selection, d, a):
    model = ns["build_mesh_cost_model"](selection, d, a)
    return model.estimate(d, a) if model else (0, 0)


real = {}
txt = open(os.path.join(FIX, "mesh_scaling_ref.txt"), encoding="utf-8").read()
cur = None
for line in txt.splitlines():
    if line.startswith("=="):
        cur = line[3:].strip()
    m = re.search(r"d=([\d.]+)\s+ang=(\d)°\s+réel\s+(\d+) tri.*total\s+([\d.]+)s", line)
    if m:
        real[(cur, float(m.group(1)), int(m.group(2)))] = (int(m.group(3)), float(m.group(4)))

doc = FreeCAD.newDocument("E")
x = Part.makeBox(100, 60, 30)
shapes = {"sphere50": Part.makeSphere(50), "cyl20x100": Part.makeCylinder(20, 100),
          "torus40_10": Part.makeTorus(40, 10), "boxfillet": x.makeFillet(5, x.Edges)}
objs = {}
for n, sh in shapes.items():
    o = doc.addObject("Part::Feature", n)
    o.Shape = sh
    objs[n] = o
doc.recompute()

for (name, d, ang), (n_real, t_real) in sorted(real.items()):
    if name not in objs:
        continue
    t0 = time.perf_counter()
    n_est, t_est = estimate([objs[name]], d, math.radians(ang))
    dt = time.perf_counter() - t0
    warn = n_est > ns["HEAVY_MESH_TRIANGLES"] or t_est > ns["HEAVY_MESH_SECONDS"]
    log(f"{name:11} d={d:<6} {ang}°  réel {n_real:>7} {t_real:6.1f}s | estim {n_est:>7} {t_est:6.1f}s "
        f"ratio {n_est / n_real:4.2f} | estimation en {dt:.2f}s {'→ QUESTION' if warn else ''}"
        f"{'  (aurait dû demander)' if t_real > 30 and not warn else ''}")

# Cas extrêmes : l'estimation doit rester rapide
for name, d, ang in (("sphere50", 0.0001, 3), ("torus40_10", 0.01, 0.1), ("sphere50", 0.001, 0.2)):
    t0 = time.perf_counter()
    n_est, t_est = estimate([objs[name]], d, math.radians(ang))
    log(f"EXTRÊME {name} d={d} {ang}° : estim {n_est} tri {t_est:.0f}s, estimation en {time.perf_counter() - t0:.2f}s")
log("FIN")
