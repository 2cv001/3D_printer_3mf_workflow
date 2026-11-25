# Chemins communs aux bancs d'essai (exécutés avec freecadcmd, voir README.md)
import os

TESTS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TESTS)
MACRO = os.path.join(REPO, "3D_Printer_3mf_Workflow.FCMacro")
FIX = os.path.join(TESTS, "fixtures")          # 3MF de test enregistrés par les slicers
OUT_ROOT = os.path.join(TESTS, "out")          # résultats et journaux (ignoré par git)
os.makedirs(OUT_ROOT, exist_ok=True)
