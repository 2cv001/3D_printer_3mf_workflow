import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, FIX, OUT_ROOT

import ast, os, re, zipfile, time
src = open(r"D:/Datas/data/Imprimante 3D/FreecadAtelierMacros/3D_Printer_3mf_Workflow/3D_Printer_3mf_Workflow.FCMacro", encoding="utf-8").read()
tree = ast.parse(src)
ns = {"os": os, "re": re, "zipfile": zipfile}
want = {"base3mf_objects", "base3mf_object_names", "find_base3mf_with_names", "_xml_unescape", "_start_tag", "_attr"}
for n in tree.body:
    if isinstance(n, ast.FunctionDef) and n.name in want:
        exec(compile(ast.Module([n], []), "f", "exec"), ns)
    if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") in ("BAMBU_CONFIG", "PRUSA_CONFIG", "_OBJECT_RE", "_NAME_META_RE"):
        exec(compile(ast.Module([n], []), "f", "exec"), ns)
d = OUT_ROOT + r"/m"
os.makedirs(d, exist_ok=True)
bambu = '<config>\n<object id="2">\n <metadata key="name" value="{a}"/>\n <part id="1"><metadata key="name" value="{a}"/></part>\n</object>\n<object id="4">\n <metadata key="name" value="{b}"/>\n</object>\n</config>'
prusa = '<config>\n<object id="1" instances_count="1">\n <metadata type="object" key="name" value="{a}"/>\n <volume firstid="0" lastid="11"/>\n</object>\n</config>'
def mk(name, cfgname, txt):
    with zipfile.ZipFile(os.path.join(d, name), "w") as z:
        z.writestr("3D/3dmodel.model", "<model/>"); z.writestr(cfgname, txt)
    return os.path.join(d, name)
p1 = mk("Objet1_Objet2_Objet3.3mf", ns["BAMBU_CONFIG"], bambu.format(a="Objet1", b="Objet2"))
p2 = mk("Autre.3mf", ns["PRUSA_CONFIG"], prusa.format(a="Objet3 &amp; co"))
p3 = d + "/casse.3mf"; open(p3, "w").write("pas un zip")
print(ns["base3mf_object_names"](p1), ns["base3mf_object_names"](p2), ns["base3mf_object_names"](p3))
f = ns["find_base3mf_with_names"]
print(f([p3, p2, p1], ["Objet2"]))
print(f([p3, p2, p1], ["Objet3 & co"]))
print(f([p3, p2, p1], ["Objet9"]), f([p1], []))
