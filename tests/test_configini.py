# Macro ConfigIni (commandes utilisateur) et leur lecture par la macro principale :
# variables %PROJECT%… dans le .ini, guillemets, délais, fenêtre ⚙️ sans effet sur
# les textes de la macro principale. Travaille sur des copies dans tests/out/.
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import MACRO, REPO, OUT_ROOT

import re, shutil, time
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", "C:/Windows/Fonts")
import FreeCAD
from PySide import QtGui, QtCore

S = OUT_ROOT
LOG = open(os.path.join(S, "test_configini.txt"), "w", encoding="utf-8")


def log(*a):
    LOG.write(" ".join(str(x) for x in a) + "\n")
    LOG.flush()


FAILS = []


def expect(c, m):
    log(("OK   " if c else "FAIL ") + m)
    if not c:
        FAILS.append(m)


app = QtGui.QApplication.instance() or QtGui.QApplication([])

OUT = os.path.join(S, "out_configini")
shutil.rmtree(OUT, ignore_errors=True)
os.makedirs(OUT)
CFG_NAME = "3D_Printer_3mf_Workflow_ConfigIni.FCMacro"
MAIN_COPY = os.path.join(OUT, os.path.basename(MACRO))
CFG_COPY = os.path.join(OUT, CFG_NAME)
shutil.copy(MACRO, MAIN_COPY)
shutil.copy(os.path.join(REPO, CFG_NAME), CFG_COPY)
INI = os.path.join(OUT, "3D_Printer_3mf_Workflow.ini")

cfg_src = open(CFG_COPY, encoding="utf-8").read()
cfg = {"__file__": CFG_COPY, "__name__": "configini_under_test"}
exec(compile(cfg_src, CFG_COPY, "exec"), cfg)
cfg["cfgini_language"] = lambda: "fr"

main_src = open(MAIN_COPY, encoding="utf-8").read()
main_src = re.sub(r"^run_macro\(\)\s*$", "pass", main_src, count=1, flags=re.M)


def load_main():
    ns = {"__file__": MAIN_COPY, "__name__": "macro_under_test"}
    exec(compile(main_src, MAIN_COPY, "exec"), ns)
    ns["get_user_language"] = lambda: "fr"
    return ns


# 1) Découpage / recollage des commandes
split, join = cfg["cfgini_split_command"], cfg["cfgini_join_command"]
cases_win = [
    ('calc.exe', ['calc.exe']),
    ('cmd /c copy /y "%EXPORT%.3mf" "C:\\Mes Projets\\b.3mf"',
     ['cmd', '/c', 'copy', '/y', '%EXPORT%.3mf', 'C:\\Mes Projets\\b.3mf']),
    ('C:\\tools\\x.exe  -a   ""', ['C:\\tools\\x.exe', '-a', '']),
    ('curl -d "k=1&a=on" http://h/x?id=0&on=true', ['curl', '-d', 'k=1&a=on', 'http://h/x?id=0&on=true']),
    ('echo "dit \\"oui\\""', ['echo', 'dit "oui"']),
]
for text, parts in cases_win:
    got = split(text, windows=True)
    expect(got == parts, f"Windows : {text!r} → {got}")
    back = split(join(parts, windows=True), windows=True)
    expect(back == parts, f"Windows : recollé puis redécoupé {parts} → {back}")
shown = join(['cmd', '/k', 'dir', '%EXPORT%.3mf'], windows=True)
expect(shown == 'cmd /k dir "%EXPORT%.3mf"', f"Windows : guillemets remis autour d'une variable ({shown})")
posix = ['cp', '%EXPORT%.3mf', '/home/a b/c.3mf', '%PROJECTDIR%/$x`y"z\\w']
shown = join(posix, windows=False)
expect(shown.startswith('cp "%EXPORT%.3mf" '), f"Linux : guillemets doubles autour d'une variable ({shown})")
expect(split(shown, windows=False) == posix, "Linux : aller-retour avec espace et caractères spéciaux")
try:
    split('echo "pas fermé', windows=True)
    expect(False, "guillemet non fermé : erreur attendue")
except ValueError:
    expect(True, "guillemet non fermé : erreur")
parse_delay = cfg["cfgini_parse_delay"]
expect(parse_delay("2,5") == 2.5 and parse_delay("") == 0 and parse_delay("3") == 3, "délais 2,5 / vide / 3")
for bad in ("abc", "-1"):
    try:
        parse_delay(bad)
        expect(False, f"délai {bad!r} refusé")
    except ValueError:
        expect(True, f"délai {bad!r} refusé")

# 2) Enregistrement avec %PROJECT%… : relu par ConfigIni et par la macro principale,
#    le reste du fichier (réglages, commentaires) est gardé
open(INI, "w", encoding="utf-8").write(
    "; commentaire gardé\n[Settings]\nslicer_exe = C:/x/QIDIStudio/QIDIStudio.exe\n"
    "recent_base3mf = D:/Données/a.3mf|D:/b.3mf\n\n"
    "[extra_commands]\nEXTRA_COMMANDS = [\n    (['calc.exe'], 'Calc', 0, False),\n    ]\n\n"
    "[Autre]\ncle = valeur\n")
commands = [
    (['cmd', '/c', 'copy', '/y', '%EXPORT%.3mf', '%PROJECTDIR%\\backup\\%EXPORTNAME%.3mf'], 'Copie à 100 %', 2.5, True),
    (['curl', 'http://h/start?job=%PROJECTNAME%'], 'Départ', 0, False),
]
cfg["cfgini_save_commands"](commands, INI)
text = open(INI, encoding="utf-8").read()
expect("; commentaire gardé" in text and "[Autre]\ncle = valeur" in text and "D:/Données/a.3mf" in text,
       "le reste du fichier est gardé")
expect("calc.exe" not in text and text.count("[extra_commands]") == 1, "ancienne section remplacée")
expect(cfg["cfgini_load_commands"](INI) == [(list(c), l, d, df) for c, l, d, df in commands],
       "relu par ConfigIni à l'identique")
main = load_main()
main["INI_FILE"] = INI
got = main["load_extra_commands_from_ini"](INI)
expect([c for c, *_ in got] == [c for c, *_ in commands] and got[0][2] == 2.5,
       f"relu par la macro principale : {got}")
conf = main["load_config"]()
expect(conf["recent_base3mf"] == ["D:/Données/a.3mf", "D:/b.3mf"], f"load_config en UTF-8 : {conf['recent_base3mf']}")

# 3) .ini sans [Settings] (créé par ConfigIni) : save_settings ajoute la section
os.remove(INI)
cfg["cfgini_save_commands"](commands, INI)
main["save_settings"](0.05, 0.05, "C:/x/s.exe", True)
text = open(INI, encoding="utf-8").read()
expect(text.startswith("[Settings]") and "slicer_exe = C:/x/s.exe" in text and "%EXPORT%" in text,
       "save_settings sur un .ini sans [Settings]")
expect(main["load_extra_commands_from_ini"](INI)[0][0][4] == "%EXPORT%.3mf", "commandes toujours lisibles")


# 4) Fenêtre : délai invalide refusé (fenêtre gardée ouverte), puis correction
def find(kind):
    return [w for w in QtGui.QApplication.topLevelWidgets() if isinstance(w, kind) and w.isVisible()]


events = []


def drive_dialog(steps):
    """Exécute les étapes (fonctions recevant la fenêtre) pendant que la fenêtre est ouverte."""
    def tick():
        boxes = find(QtGui.QMessageBox)
        if boxes:
            events.append(("message", boxes[0].text()))
            boxes[0].close()
            QtCore.QTimer.singleShot(50, tick)
            return
        dialogs = [d for d in find(QtGui.QDialog) if d.findChild(QtGui.QTableWidget)]
        if not dialogs or not steps:
            QtCore.QTimer.singleShot(50, tick) if steps else None
            return
        # Prochain passage programmé AVANT l'étape : un clic sur OK peut ouvrir
        # un message modal qui ne rend la main qu'une fois fermé
        QtCore.QTimer.singleShot(50, tick)
        steps.pop(0)(dialogs[0])
    QtCore.QTimer.singleShot(50, tick)


def set_delay(value):
    def step(d):
        d.findChild(QtGui.QTableWidget).item(0, 2).setText(value)
    return step


def press_ok(d):
    d.findChild(QtGui.QDialogButtonBox).button(QtGui.QDialogButtonBox.Ok).click()


def read_command(d):
    events.append(("cell", d.findChild(QtGui.QTableWidget).item(0, 0).text()))


events.clear()
drive_dialog([read_command, set_delay("abc"), press_ok, set_delay("1,5"), press_ok])
saved = cfg["show_extra_commands_dialog"](None, INI)
cell = [t for k, t in events if k == "cell"]
expect(cell == ['cmd /c copy /y "%EXPORT%.3mf" "%PROJECTDIR%\\backup\\%EXPORTNAME%.3mf"'],
       f"fenêtre rouverte : commande affichée avec ses guillemets ({cell})")
expect(any(k == "message" and "abc" in t for k, t in events), f"délai « abc » : message ({events})")
expect(saved and cfg["cfgini_load_commands"](INI)[0][2] == 1.5, "délai corrigé en 1,5 puis enregistré")
expect(cfg["cfgini_load_commands"](INI)[0][0][4] == "%EXPORT%.3mf", "la commande avec %EXPORT% est gardée")

# 5) Fichier illisible : message, rien n'est écrasé
open(INI, "w", encoding="utf-8").write("[extra_commands]\nEXTRA_COMMANDS = [ceci n'est pas du python\n")
before = open(INI, encoding="utf-8").read()
events.clear()
drive_dialog([])
saved = cfg["show_extra_commands_dialog"](None, INI)
expect(not saved and any(k == "message" for k, _ in events), "fichier illisible : message, fenêtre non ouverte")
expect(open(INI, encoding="utf-8").read() == before, "fichier illisible : pas modifié")

# 6) Bouton ⚙️ : ConfigIni exécuté à part, les textes de la macro principale restent bons
cfg["cfgini_save_commands"](commands, INI)
main = load_main()
title_before = main["tr"]("error_title")
events.clear()
drive_dialog([press_ok])
main["run_macro_if_exists"](CFG_NAME, "http://x", "http://x")
expect(main["tr"]("error_title") == title_before and "cfgini_tr" not in main,
       f"textes de la macro principale intacts ({main['tr']('error_title')!r})")
expect(main["reload_extra_commands"]()[0][1] == "Copie à 100 %", "commandes relues après ⚙️")

# 7) Délais : FreeCAD n'attend pas, les commandes partent dans l'ordre
launched = []
main["_launch_extra_command"] = lambda c: launched.append((time.time(), c))
t0 = time.time()
main["run_extra_commands"]([(True, ["a", "%EXPORTNAME%"], 0), (False, ["skip"], 0),
                            (True, ["b"], 0.3), (True, ["c"], 0.2)],
                           os.path.join(OUT, "proj.FCStd"), os.path.join(OUT, "Body"))
expect(time.time() - t0 < 0.2, f"run_extra_commands rend la main tout de suite ({time.time() - t0:.2f} s)")
expect([c for _, c in launched] == [["a", "Body"]], f"commande sans délai lancée tout de suite ({launched})")
end = time.time() + 2
while time.time() < end and len(launched) < 3:
    app.processEvents()
    time.sleep(0.02)
order = [c[0] for _, c in launched]
expect(order == ["a", "b", "c"], f"ordre a, b, c ({order})")
if len(launched) == 3:
    expect(launched[2][0] - t0 >= 0.45, f"délais cumulés : c après {launched[2][0] - t0:.2f} s")

log("ÉCHECS :", FAILS if FAILS else "aucun")
