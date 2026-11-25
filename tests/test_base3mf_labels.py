import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, FIX, OUT_ROOT

import ast, os, re, sys
from PySide import QtCore
src = open(r"D:/Datas/data/Imprimante 3D/FreecadAtelierMacros/3D_Printer_3mf_Workflow/3D_Printer_3mf_Workflow.FCMacro", encoding="utf-8").read()
tree = ast.parse(src)
ns = {"os": os, "re": re, "QtCore": QtCore}
for n in tree.body:
    if isinstance(n, ast.FunctionDef) and n.name == "base3mf_other_labels":
        exec(compile(ast.Module([n], []), "f", "exec"), ns)
S = OUT_ROOT + r"/t"
for l in ns["base3mf_other_labels"]([S+"/A/Proj1/Body.3mf", S+"/B/Proj1/Body.3mf", S+"/Proj2/Body.3mf"]):
    print(l)
