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
expect(cfg["cfgini_load_commands"](INI) == [(list(c), l, d, df, False) for c, l, d, df in commands],
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

# 8) Aide à la saisie : vérification de la commande
values = {"%PROJECT%": os.path.join(OUT, "Mon projet"), "%PROJECTDIR%": OUT,
          "%PROJECTNAME%": "Mon projet", "%EXPORT%": os.path.join(OUT, "Body"), "%EXPORTNAME%": "Body"}
analyze = lambda t: cfg["cfgini_analyze"](t, values, windows=True)
a = analyze('cmd /c copy /y "%EXPORT%.3mf" "%PROJECTDIR%\\b.3mf"')
expect(not a["errors"] and not a["warnings"] and a["program_path"]
       and a["parts"][4] == os.path.join(OUT, "Body") + ".3mf", f"cmd /c copy : correct, variables remplacées ({a})")
a = analyze('copy "%EXPORT%.3mf" b.3mf')
expect(any("cmd /c copy" in e for e in a["errors"]), f"copy seul : commande interne signalée ({a['errors']})")
a = analyze("programme_qui_n_existe_pas.exe")
expect(a["errors"] and "introuvable" in a["errors"][0], f"programme introuvable ({a['errors']})")
expect(analyze('echo "pas fermé')["errors"], "guillemet non fermé signalé")
a = analyze("curl 'http://h/x'")
expect(any("guillemets doubles" in w for w in a["warnings"]), f"guillemets simples signalés ({a['warnings']})")
a = analyze("curl http://h/x > out.txt")
expect(any("« > »" in w for w in a["warnings"]), f"redirection signalée ({a['warnings']})")
a = analyze("cmd /c echo %USERPROFILE% %EXPORTS%")
expect(len(a["warnings"]) == 1 and "%EXPORTS%" in a["warnings"][0],
       f"variable inconnue signalée, variable d'environnement acceptée pour cmd ({a['warnings']})")
a = analyze('curl -X POST "http://h:7125/printer/gcode/script?script=M140%20S60"')
expect(not a["errors"] and not a["warnings"], f"%20 dans une adresse : rien à signaler ({a})")
for key, command in cfg["cfgini_templates"](windows=True):
    if command is None:
        continue
    a = analyze(command)
    builtin = any("interne" in e for e in a["errors"])
    expect(not builtin and a["parts"], f"modèle {key} : {command} ({a['errors']} {a['warnings']})")
    if "<" in command:
        expect(any("À remplacer" in w for w in a["warnings"]), f"modèle {key} : parties à remplacer signalées")
tpl = dict(cfg["cfgini_templates"](windows=True))
expect(split(tpl["tpl_home_assistant"], windows=True) == [
    "curl", "--fail", "-X", "POST", "-H", "Authorization: Bearer <JETON>", "-H", "Content-Type: application/json",
    "-d", '{"entity_id":"switch.<NOM_DE_LA_PRISE>"}',
    "http://<ADRESSE_HOME_ASSISTANT>:8123/api/services/switch/turn_on"],
    f"Home Assistant : JSON passé intact ({split(tpl['tpl_home_assistant'], windows=True)})")
expect(split(tpl["tpl_jeedom"], windows=True) == [
    "curl", "--fail", "http://<ADRESSE_JEEDOM>/core/api/jeeApi.php?apikey=<CLE_API>&type=cmd&id=<ID_DE_LA_COMMANDE>"],
    "Jeedom : adresse en un seul argument")
expect(split(tpl["tpl_shelly_cloud"], windows=True)[-1] == "channel=0&turn=on&id=<ID_DE_LA_PRISE>&auth_key=<CLE_API>",
       "Shelly cloud : paramètres en un seul argument")
for key in ("tpl_home_assistant", "tpl_jeedom", "tpl_shelly_cloud"):
    parts = split(tpl[key], windows=True)
    expect(split(join(parts, windows=True), windows=True) == parts, f"{key} : aller-retour dans la fenêtre")
# Même remplacement que la macro principale au lancement
launched.clear()
main["run_extra_commands"]([(True, ["x", "%PROJECTDIR%\\%PROJECTNAME%_%EXPORTNAME%", "%PROJECT%|%EXPORT%"], 0)],
                           values["%PROJECT%"] + ".FCStd", values["%EXPORT%"])
expect(launched and launched[0][1] == cfg["cfgini_substitute"](
    ["x", "%PROJECTDIR%\\%PROJECTNAME%_%EXPORTNAME%", "%PROJECT%|%EXPORT%"], values),
    "aperçu identique au remplacement de la macro principale")

# Chemins « D:/… » donnés par FreeCAD : remis au format Windows (Explorateur, cmd)
launched.clear()
main["run_extra_commands"]([(True, ["explorer", "%PROJECTDIR%", "%EXPORT%.3mf"], 0)],
                           "D:/Datas/Imprimante 3D/proj.FCStd", "D:/Datas/Imprimante 3D/Body")
expect(launched and launched[0][1] == ["explorer", "D:\\Datas\\Imprimante 3D", "D:\\Datas\\Imprimante 3D\\Body.3mf"],
       f"macro principale : chemins avec \\ ({launched})")
cfg["CFGINI_CONTEXT"] = {"PROJECT": "D:/Datas/Imprimante 3D/proj", "EXPORT": "D:/Datas/Imprimante 3D/Body"}
ctx_values, _ = cfg["cfgini_context"]()
expect(ctx_values["%PROJECTDIR%"] == "D:\\Datas\\Imprimante 3D"
       and ctx_values["%EXPORT%"] == "D:\\Datas\\Imprimante 3D\\Body", f"ConfigIni : chemins avec \\ ({ctx_values})")
del cfg["CFGINI_CONTEXT"]

# 9) Tester : résultat du lancement
run_test, test_msg = cfg["cfgini_run_test"], cfg["cfgini_test_message"]
ok, msg = test_msg(["cmd"], run_test(["cmd", "/c", "exit", "0"]))
expect(ok and "sans erreur" in msg, f"code 0 : {msg}")
ok, msg = test_msg(["cmd"], run_test(["cmd", "/c", "exit", "3"]))
expect(not ok and "code 3" in msg, f"code 3 : {msg}")
ok, msg = test_msg(["x"], run_test(["programme_qui_n_existe_pas.exe"]))
expect(not ok and "impossible" in msg, f"lancement impossible : {msg}")
if shutil.which("curl"):
    ok, msg = test_msg(["curl"], run_test(["curl", "-s", "--max-time", "2", "http://127.0.0.1:9/"]))
    expect(not ok and ("refusée" in msg or "temps" in msg), f"curl sans réponse : {msg}")
ok, msg = test_msg(["ping"], run_test(["ping", "-n", "5", "127.0.0.1"], timeout=0.5), timeout=0.5)
expect(ok and "toujours en cours" in msg, f"programme encore en cours : {msg}")

# 10) Fenêtre : modèle, saisie, variable, test, enregistrement
open(INI, "w", encoding="utf-8").write("[Settings]\n")
cfg["CFGINI_CONTEXT"] = {"PROJECT": values["%PROJECT%"], "EXPORT": values["%EXPORT%"]}
seen = {}


def find_label(d, start):
    return [l.text() for l in d.findChildren(QtGui.QLabel) if l.text().startswith(start)]


def button(d, text):
    return [b for b in d.findChildren(QtGui.QPushButton) if b.text() == text][0]


def use_template(d):
    actions = button(d, "Ajouter un modèle").menu().actions()
    [a for a in actions if a.text().startswith("Allumer une prise Shelly Gen 2")][0].trigger()
    edit = d.findChild(QtGui.QLineEdit)
    seen["selected"] = edit.selectedText()
    edit.insert("192.168.1.50")
    seen["after_ip"] = edit.text()
    seen["cell"] = d.findChild(QtGui.QTableWidget).item(0, 0).text()
    seen["label"] = d.findChild(QtGui.QTableWidget).item(0, 1).text()
    seen["check1"] = [l.text() for l in d.findChildren(QtGui.QLabel) if "curl" in l.text()]


def add_with_variable(d):
    button(d, "Ajouter sans modèle").click()
    edit = d.findChild(QtGui.QLineEdit)
    edit.setText("cmd /c exit ")
    edit.setCursorPosition(len(edit.text()))
    actions = button(d, "Insérer une variable").menu().actions()
    [a for a in actions if a.text().startswith("%EXPORT%.3mf")][0].trigger()
    seen["with_var"] = edit.text()
    seen["check2"] = [l.text() for l in d.findChildren(QtGui.QLabel) if "Paramètres" in l.text()]
    # Espace ajouté après le programme, pas au milieu d'une adresse
    seen["spacing"] = []
    for start, var in (('"C:\\Program Files\\x.exe"', "%EXPORT%.3mf"), ("calc.exe", "%EXPORT%.3mf"),
                       ("curl http://h/?job=", "%PROJECTNAME%"), ('curl "http://h/?job=', "%PROJECTNAME%"),
                       ('cmd /c copy "a.3mf"', "%EXPORT%.3mf")):
        edit.setText(start)
        edit.setCursorPosition(len(start))
        [a for a in actions if a.text().startswith(var + " ")][0].trigger()
        seen["spacing"].append(edit.text())
    edit.setText("cmd /c exit 0")
    button(d, "Tester").click()


def read_test(d):
    """Renvoie False (étape à refaire) tant que le résultat du test n'est pas affiché."""
    seen["test"] = [l.text() for l in d.findChildren(QtGui.QLabel) if l.text().startswith(("✓", "✗"))]
    seen["read_tries"] = seen.get("read_tries", 0) + 1
    return bool(seen["test"]) or seen["read_tries"] > 50


def answer_yes(box):
    yes = box.button(QtGui.QMessageBox.Yes)
    if yes is not None:
        events.append(("confirm", box.text()))
        yes.click()
        return True
    return False


def drive_dialog_yes(steps):
    def tick():
        boxes = find(QtGui.QMessageBox)
        if boxes:
            if not answer_yes(boxes[0]):
                events.append(("message", boxes[0].text()))
                boxes[0].close()
            QtCore.QTimer.singleShot(50, tick)
            return
        dialogs = [d for d in find(QtGui.QDialog) if d.findChild(QtGui.QTableWidget)]
        if not dialogs or not steps:
            QtCore.QTimer.singleShot(50, tick) if steps else None
            return
        QtCore.QTimer.singleShot(300, tick)
        step = steps.pop(0)
        if step(dialogs[0]) is False:
            steps.insert(0, step)
    QtCore.QTimer.singleShot(50, tick)


events.clear()
drive_dialog_yes([use_template, add_with_variable, read_test, press_ok])
saved = cfg["show_extra_commands_dialog"](None, INI)
log("fenêtre :", seen, events)
expect(seen.get("selected") == "<IP_DE_LA_PRISE>", f"modèle : la partie à remplacer est sélectionnée ({seen.get('selected')})")
expect(seen.get("after_ip") == 'curl --fail "http://192.168.1.50/rpc/Switch.Set?id=0&on=true"'
       and seen.get("cell") == seen.get("after_ip"), f"saisie recopiée dans le tableau ({seen.get('cell')})")
expect(seen.get("label") == "Allumer une prise Shelly Gen 2", f"libellé du modèle ({seen.get('label')})")
expect(seen.get("check1") and "À remplacer" not in seen["check1"][0], f"plus rien à remplacer ({seen.get('check1')})")
expect(seen.get("with_var") == 'cmd /c exit "%EXPORT%.3mf"', f"variable insérée entre guillemets ({seen.get('with_var')})")
expect(seen.get("spacing") == ['"C:\\Program Files\\x.exe" "%EXPORT%.3mf"', 'calc.exe "%EXPORT%.3mf"',
                               'curl http://h/?job=%PROJECTNAME%', 'curl "http://h/?job=%PROJECTNAME%',
                               'cmd /c copy "a.3mf" "%EXPORT%.3mf"'],
       f"espace après le programme ou un argument entre guillemets ({seen.get('spacing')})")
expect(bool(seen.get("check2")) and "Body.3mf" in seen["check2"][0],
       f"aperçu avec le vrai chemin ({seen.get('check2')})")
expect(any(k == "confirm" and "cmd /c exit 0" in t for k, t in events), "Tester : confirmation demandée avec la commande")
expect(seen.get("test") and seen["test"][0].startswith("✓"), f"Tester : résultat affiché ({seen.get('test')})")
cmds = cfg["cfgini_load_commands"](INI)
expect(saved and [c for c, *_ in cmds] == [["curl", "--fail", "http://192.168.1.50/rpc/Switch.Set?id=0&on=true"],
                                           ["cmd", "/c", "exit", "0"]], f"enregistré : {cmds}")

# 11) Fin d'export : commandes lancées AVANT le message « terminé » (modal)
import math, Part
doc = FreeCAD.newDocument("Cfg")
box = doc.addObject("Part::Feature", "A")
box.Shape = Part.makeBox(10, 10, 10)
doc.recompute()
doc.saveAs(os.path.join(OUT, "proj.FCStd"))
for launch, slicer, expected_msg in ((False, "", "info_done"),
                                     (True, "C:/pas/de/slicer.exe", "error_invalid_slicer")):
    order = []
    ns = load_main()
    ns["show_message"] = lambda t, m: order.append(("message", m))
    ns["_launch_extra_command"] = lambda c: order.append(("command", c))
    base = os.path.join(OUT, "A")
    ns["prepare_environment"] = lambda: ({}, doc, [box], ["A"], base, base + ".3mf", base + ".old.3mf",
                                         os.path.exists(base + ".3mf"))
    ns["get_user_options"] = lambda *a: (False, slicer, "", launch, 0.1, math.radians(5), False,
                                         [(True, ["x", "%EXPORTNAME%"], 0)])
    ns["export_replace_geometry"]()
    msg_text = ns["tr"](expected_msg)
    expect([k for k, _ in order] == ["command", "message"] and order[0][1] == ["x", "A"]
           and msg_text.split("\n")[0] in order[1][1],
           f"lancer le slicer={launch} : commande puis message ({order})")

# 12) Commandes « avant l'export »
cmds5 = [(["avant1"], "Allumer", 0, True, True), (["apres1", "%EXPORTNAME%"], "Copier", 0, True, False),
         (["avant2"], "Préchauffer", 0, False, True)]
cfg["cfgini_save_commands"](cmds5, INI)
import configparser as _cp, ast as _ast
raw_ini = _cp.ConfigParser(interpolation=None)
raw_ini.read(INI, encoding="utf-8")
expect(_ast.literal_eval(raw_ini["extra_commands"]["EXTRA_COMMANDS"]) == [(["apres1", "%EXPORTNAME%"], "Copier", 0, True)],
       "EXTRA_COMMANDS : seulement les commandes après l'export, en 4 éléments (anciennes versions)")
expect(len(_ast.literal_eval(raw_ini["extra_commands"]["EXTRA_COMMANDS_BEFORE"])) == 2, "EXTRA_COMMANDS_BEFORE : 2 commandes")
expect([c[4] for c in cfg["cfgini_load_commands"](INI)] == [True, True, False], "ConfigIni relit : avant en premier")
main = load_main()
got = main["load_extra_commands_from_ini"](INI)
expect([(c[0][0], c[4]) for c in got] == [("avant1", True), ("avant2", True), ("apres1", False)],
       f"macro principale relit le moment ({[(c[0][0], c[4]) for c in got]})")
a = cfg["cfgini_analyze"]('cmd /c copy "%EXPORT%.3mf" x', values, windows=True, before=True)
expect(any("pas encore écrit" in w for w in a["warnings"]), f"avant l'export + %EXPORT% : avertissement ({a['warnings']})")
a = cfg["cfgini_analyze"]('cmd /c copy "%EXPORT%.3mf" x', values, windows=True, before=False)
expect(not a["warnings"], "après l'export + %EXPORT% : pas d'avertissement")

# Chemin complet collé derrière un dossier
a = cfg["cfgini_analyze"](r'cmd /c copy /y "%PROJECT%.FCStd" "C:\svg\%PROJECT%.FCStd"', values, windows=True)
expect(any("%PROJECTNAME%" in w for w in a["warnings"]), f"%PROJECT% derrière un dossier : avertissement ({a['warnings']})")
a = cfg["cfgini_analyze"]('cp "%EXPORT%.3mf" "/tmp/%EXPORT%.3mf"', values, windows=False)
expect(any("%EXPORTNAME%" in w for w in a["warnings"]), f"%EXPORT% derrière / : avertissement ({a['warnings']})")
for ok_cmd in (r'cmd /c copy /y "%EXPORT%.3mf" "%PROJECTDIR%\backup\%EXPORTNAME%.3mf"',
               r'cmd /c copy /y "%PROJECT%.FCStd" "C:\svg\%PROJECTNAME%.FCStd"',
               'curl --fail "http://h/?file=%EXPORT%.3mf"', 'prog --out=%EXPORT%.gcode'):
    a = cfg["cfgini_analyze"](ok_cmd, values, windows=True)
    expect(not any("chemin complet" in w for w in a["warnings"]), f"pas d'avertissement chemin complet : {ok_cmd} ({a['warnings']})")

# Chemin C:/… passé à cmd, dossier introuvable
a = cfg["cfgini_analyze"]('cmd /c copy /y "%EXPORT%.3mf" "C:/SVG_inexistant/%EXPORTNAME%.3mf"', values, windows=True)
expect(any("C:/SVG_inexistant" in w and "option" in w for w in a["warnings"]), f"C:/ passé à cmd : avertissement ({a['warnings']})")
expect(any("SVG_inexistant" in w and "n'existe pas" in w for w in a["warnings"]), f"dossier introuvable : avertissement ({a['warnings']})")
a = cfg["cfgini_analyze"]('cmd /c copy /y "%EXPORT%.3mf" "C:/SVG_inexistant/x.3mf"', values, windows=True, check_paths=False)
expect(not any("n'existe pas" in w for w in a["warnings"]), f"chemins d'exemple : dossiers non cherchés ({a['warnings']})")
a = cfg["cfgini_analyze"](f'cmd /c copy /y "%EXPORT%.3mf" "{OUT}\\copie.3mf"', values, windows=True)
expect(not a["warnings"], f"dossier existant, chemin avec \\ : aucun avertissement ({a['warnings']})")
a = cfg["cfgini_analyze"]('curl --fail "http://h/x" -o "<DOSSIER>\\x"', values, windows=True)
expect(not any("n'existe pas" in w for w in a["warnings"]), f"URL et partie à remplacer ignorées ({a['warnings']})")

# Programme donné par son chemin complet : affiché une seule fois
exe = sys.executable
h = cfg["cfgini_check_html"](cfg["cfgini_analyze"](f'"{exe}" -V', values), False)
expect(h.count(os.path.basename(exe)) == 1, f"chemin complet affiché une fois ({h})")
h = cfg["cfgini_check_html"](cfg["cfgini_analyze"]('cmd /c dir', values, windows=True), False)
expect("→" in h, f"nom court : nom → chemin trouvé ({h})")

order = []
ns = load_main()
ns["show_message"] = lambda t, m: order.append(("message", None))
ns["_launch_extra_command"] = lambda c: order.append(("command", c[0]))
launch_times = {}
_launch_cmd = ns["_launch_extra_command"]
ns["_launch_extra_command"] = lambda c: (launch_times.__setitem__(c[0], time.monotonic()), _launch_cmd(c))
real_export = ns["export_freecad_files"]
ns["export_freecad_files"] = lambda *a, **k: (order.append(("mesh", None)), real_export(*a, **k))[1]
base = os.path.join(OUT, "A")
ns["prepare_environment"] = lambda: ({}, doc, [box], ["A"], base, base + ".3mf", base + ".old.3mf",
                                     os.path.exists(base + ".3mf"))
ns["get_user_options"] = lambda *a: (False, "", "", False, 0.1, math.radians(5), False,
                                     [(True, ["avant1"], 0, True), (True, ["apres1"], 0, False),
                                      (True, ["avant2"], 0.5, True), (False, ["avant3"], 0, True)])
ns["export_replace_geometry"]()
expect([k if v is None else v for k, v in order] == ["avant1", "avant2", "mesh", "apres1", "message"],
       f"ordre : avant (avec délai attendu), maillage, après, message ({order})")
gap = launch_times.get("avant2", 0) - launch_times.get("avant1", 0)
expect(0.45 <= gap < 2, f"délai de 0,5 s attendu entre les deux commandes avant ({gap:.2f} s)")

# Dialogue : case « Avant l'export » enregistrée
events.clear()


def tick_before(d):
    d.findChild(QtGui.QTableWidget).cellWidget(2, 4).setChecked(True)  # « Copier » (3e ligne) passe avant


drive_dialog([tick_before, press_ok])
cfg["show_extra_commands_dialog"](None, INI)
expect([c[4] for c in cfg["cfgini_load_commands"](INI)] == [True, True, True], "case cochée dans la fenêtre : enregistrée")

# Dialogue : déplacer les lignes
cfg["cfgini_save_commands"]([(["un"], "Un", 0, True, False), (["deux"], "Deux", 2, False, True),
                             (["trois"], "Trois", 0, False, False)], INI)
move_state = {}


def button(d, key):
    return [b for b in d.findChildren(QtGui.QPushButton) if b.text() == cfg["cfgini_tr"](key)][0]


def move_steps(d):
    t = d.findChild(QtGui.QTableWidget)
    # Au chargement : « avant » d'abord → deux, un, trois
    t.setCurrentCell(0, 0)
    move_state["up_first"] = button(d, "btn_up").isEnabled()
    button(d, "btn_down").click()          # deux descend → un, deux, trois
    move_state["row1"] = (t.item(1, 0).text(), t.item(1, 2).text(), t.cellWidget(1, 4).isChecked(),
                          t.currentRow(), d.findChild(QtGui.QLineEdit).text())
    t.setCurrentCell(2, 0)
    move_state["down_last"] = button(d, "btn_down").isEnabled()
    button(d, "btn_up").click()            # trois monte → un, trois, deux
    button(d, "btn_up").click()            # encore → trois, un, deux


drive_dialog([move_steps, press_ok])
cfg["show_extra_commands_dialog"](None, INI)
expect(move_state.get("up_first") is False and move_state.get("down_last") is False,
       f"Monter désactivé en haut, Descendre en bas ({move_state})")
expect(move_state.get("row1") == ("deux", "2", True, 1, "deux"),
       f"ligne déplacée avec son délai, sa case et la sélection ({move_state.get('row1')})")
order_saved = [(c[0][0], c[4]) for c in cfg["cfgini_load_commands"](INI)]
expect(order_saved == [("deux", True), ("trois", False), ("un", False)],
       f"trois, un, deux enregistré : avant d'abord, puis trois, un ({order_saved})")

log("ÉCHECS :", FAILS if FAILS else "aucun")
