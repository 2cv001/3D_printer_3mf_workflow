import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, FIX, OUT_ROOT

import ast, os, re, zipfile
src = open(r"D:/Datas/data/Imprimante 3D/FreecadAtelierMacros/3D_Printer_3mf_Workflow/3D_Printer_3mf_Workflow.FCMacro", encoding="utf-8").read()
tree = ast.parse(src)
ns = {"os": os, "re": re, "zipfile": zipfile}
want = {"base3mf_objects", "base3mf_object_names", "_short_name_list", "describe_base3mf",
        "_xml_unescape", "_start_tag", "_attr"}
texts = None
for n in tree.body:
    if isinstance(n, ast.FunctionDef) and n.name in want:
        exec(compile(ast.Module([n], []), "f", "exec"), ns)
    if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("BAMBU_CONFIG", "PRUSA_CONFIG", "_OBJECT_RE", "_NAME_META_RE"):
        exec(compile(ast.Module([n], []), "f", "exec"), ns)
    if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "TEXTS":
        texts = eval(compile(ast.Expression(n.value), "t", "eval"))
if texts is None:
    for n in ast.walk(tree):
        if isinstance(n, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "fr" for k in n.keys):
            texts = eval(compile(ast.Expression(n), "t", "eval"))
            break
lang = os.environ.get("LANGT", "fr")
ns["tr"] = lambda k: texts[lang][k]

d = OUT_ROOT + r"/i"
os.makedirs(d, exist_ok=True)
def mk(name, objs, cfg=True):
    body = "".join(f'<object id="{i}">\n <metadata key="name" value="{o}"/>\n</object>\n' for i, o in enumerate(objs, 1))
    with zipfile.ZipFile(os.path.join(d, name), "w") as z:
        z.writestr("3D/3dmodel.model", "<model/>")
        if cfg:
            z.writestr(ns["BAMBU_CONFIG"], "<config>\n" + body + "</config>")
    return os.path.join(d, name)
three = mk("Objet1_Objet2_Objet3.3mf", ["Objet1", "Objet2", "Objet3"])
o2 = mk("Objet2.3mf", ["Objet2"])
abc = mk("A_B_C.3mf", ["A", "B", "D"])
autre = mk("Autre.3mf", ["Cylindre", "Cone"])
nocfg = mk("Brut.3mf", [], cfg=False)
big = mk("Big.3mf", list("ABCDEFG"))
D = ns["describe_base3mf"]
cases = [
    ("Pas de base, Objet2.3mf existe", "", o2, ["Objet2"]),
    ("Pas de base, rien", "", d + "/X.3mf", ["X"]),
    ("3MF de la sélection, 1 objet", o2, o2, ["Objet2"]),
    ("3MF de la sélection, plusieurs", abc, abc, ["A", "B", "C"]),
    ("Autre 3MF, noms trouvés", three, d + "/Objet2_Objet4.3mf", ["Objet2", "Objet4"]),
    ("Autre 3MF, 1 objet trouvé", three, d + "/Objet2_x.3mf", ["Objet2"]),
    ("Autre, aucun nom, 1 objet", autre, d + "/Cube.3mf", ["Cube"]),
    ("Autre, aucun nom, plusieurs", autre, d + "/Cube_Tore.3mf", ["Cube", "Tore"]),
    ("Sans réglages", nocfg, d + "/Cube.3mf", ["Cube"]),
    ("Noms longs", big, d + "/z.3mf", list("ABCDEFGHI")),
]
for title, base, fc, sel in cases:
    t, w, tip = D(base, fc, sel)
    print(f"--- {title}{'  [ORANGE]' if w else ''}")
    print(t)
    if tip:
        print("  (infobulle) " + tip.replace("\n", " | "))
