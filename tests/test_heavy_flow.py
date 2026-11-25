import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, FIX, OUT_ROOT

import os, re, sys, shutil, math
import FreeCAD, Part

S = OUT_ROOT
LOG = open(os.path.join(S, "test_heavy_flow.txt"), "w", encoding="utf-8")


def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")
    LOG.flush()



OUT = os.path.join(S, "out_heavy")
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
src = open(MACRO, encoding="utf-8").read()
src = re.sub(r"^run_macro\(\)\s*$", "pass", src, count=1, flags=re.M)

doc = FreeCAD.newDocument("H")
A = doc.addObject("Part::Feature", "A")
A.Shape = Part.makeSphere(20)
doc.recompute()
doc.saveAs(os.path.join(OUT, "proj.FCStd"))
FAILS = []


def expect(c, m):
    log(("OK   " if c else "FAIL ") + m)
    if not c:
        FAILS.append(m)


def load(lang):
    ns = {"__file__": MACRO, "__name__": "macro_under_test"}
    exec(compile(src, MACRO, "exec"), ns)
    ns["get_user_language"] = lambda: lang
    return ns


# 1) Textes du message (FR, EN, DE) pour quelques estimations
for lang in ("fr", "en", "de"):
    ns = load(lang)
    for n, sec in ((4_800_000, 190), (501_248, 51), (1_294_467_072, 6_722_269), (89_386_010, 121_979 / 30)):
        text = ns["tr"]("heavy_mesh_text").format(
            tri=ns["_format_triangles"](n), size=ns["_format_size"](n * ns["BYTES_PER_TRIANGLE"]),
            time=ns["_format_duration"](sec))
        log(f"[{lang}] {text.splitlines()[0]}")

# 2) Déroulement : estimation lourde → question
asked = []


def run(answer, linear):
    ns = load("fr")
    ns["show_message"] = lambda t, m: None
    ns["ask_heavy_mesh_dialog"] = lambda n, s: (asked.append((n, s)), answer)[1]
    base = os.path.join(OUT, "A")
    ns["prepare_environment"] = lambda: ({}, doc, [A], ["A"], base, base + ".3mf", base + ".old.3mf",
                                         os.path.exists(base + ".3mf"))
    ns["get_user_options"] = lambda *a: (False, "C:/x/QIDIStudio/QIDIStudio.exe", "", False,
                                         linear, math.radians(3), False, [])
    return ns["export_replace_geometry"](), os.path.exists(base + ".3mf")


asked.clear()
result, written = run(False, 0.0005)
expect(len(asked) == 1, f"précision 0,0005 : la question est posée (estimation {asked})")
expect(result == "restart" and not written, f"Revenir aux options : retour aux options, rien d'écrit ({result}, {written})")

asked.clear()
result, written = run(True, 0.05)
expect(not asked and written, "précision normale 0,05 : pas de question, 3MF écrit")

log("ÉCHECS :", FAILS if FAILS else "aucun")
