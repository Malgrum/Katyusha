# -*- coding: utf-8 -*-
"""
Assistant.py — Parsing et exécution des ordres assistant (analyse, SSH, ouverture d’URL).
"""
import re
import platform
import os
from urllib.parse import quote_plus
try:
    import paramiko
except Exception:
    paramiko = None

ASSISTANT_PREFIXES = [
    r"\bdit\s+katyusha\b",
    r"\bdis\s+katyusha\b",
    r"\bkatyusha\b"
]

LOCAL_PC_NAME = "Pravda"

PCS = {}

def parser_ordre_assistant(texte: str):
    t = " " + texte.strip() + " "
    if not re.search("|".join(ASSISTANT_PREFIXES), t, flags=re.I):
        return None
    m_pc = re.search(r"\bsur\s+([a-z0-9\-_]+)\b", t, flags=re.I)
    pc = m_pc.group(1) if m_pc else LOCAL_PC_NAME
    m_act = re.search(r"\b(lance|lancer|ouvre|ouvrir|joue|jouer)\b", t, flags=re.I)
    action = (m_act.group(1).lower() if m_act else "ouvre")
    action = {"lancer": "lance", "ouvrir": "ouvre", "jouer": "joue"}.get(action, action)
    m_plat = re.search(r"\bsur\s+(youtube|yt|spotify|deezer)\b", t, flags=re.I)
    plateforme = m_plat.group(1).lower() if m_plat else "youtube"
    if plateforme == "yt":
        plateforme = "youtube"
    req = None
    if m_plat:
        start = m_act.end() if m_act else 0
        end = m_plat.start()
        req = t[start:end].strip(" ,.:;!?")
    if not req:
        req = t[m_act.end():].strip() if m_act else t.strip()
    req = re.sub(r"\bsur\s+[a-z0-9\-_]+\b", "", req, flags=re.I)
    req = re.sub(r"\bsur\s+(youtube|yt|spotify|deezer)\b", "", req, flags=re.I)
    req = req.strip(" ,.:;!?")
    if not req:
        req = None
    return {
        "pc": pc,
        "action": action,
        "plateforme": plateforme,
        "requete": req
    }

def url_youtube_recherche(query: str) -> str:
    return f"https://www.youtube.com/results?search_query={quote_plus(query)}"

def commande_ouvrir_url_pour_os(url: str, os_name: str, forced_cmd: str = "") -> str:
    if forced_cmd:
        if forced_cmd.lower().startswith("start"):
            return f'cmd /c {forced_cmd} "{url}"' if ' ' in forced_cmd else f'cmd /c start "" "{url}"'
        else:
            return f'{forced_cmd} "{url}"'
    os_name = os_name.lower()
    if os_name.startswith("win"):
        return f'cmd /c start "" "{url}"'
    if os_name.startswith("mac"):
        return f'open "{url}"'
    return f'xdg-open "{url}"'

def ouvrir_url_local(url: str, forced_cmd: str = ""):
    import webbrowser
    if forced_cmd:
        try:
            os.system(commande_ouvrir_url_pour_os(url, platform.system(), forced_cmd))
            return True, None
        except Exception as e:
            return False, f"Erreur ouverture locale via commande '{forced_cmd}': {e}"
    else:
        try:
            webbrowser.open(url, new=2)
            return True, None
        except Exception as e:
            return False, f"Erreur ouverture locale: {e}"

def exec_ssh(host, user, command, password=None, key_path=None):
    if not paramiko:
        return False, "Paramiko n'est pas installé (pip install paramiko)."
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        if key_path:
            pkey = paramiko.RSAKey.from_private_key_file(os.path.expanduser(key_path))
            client.connect(hostname=host, username=user, pkey=pkey, timeout=6)
        else:
            client.connect(hostname=host, username=user, password=password, timeout=6)
        stdin, stdout, stderr = client.exec_command(command)
        out = stdout.read().decode("utf-8", errors="ignore")
        err = stderr.read().decode("utf-8", errors="ignore")
        client.close()
        if err.strip():
            return False, err.strip()
        return True, out.strip()
    except Exception as e:
        return False, f"SSH échec: {e}"

def executer_ordre_assistant(instruction: dict, memoire, PCS, LOCAL_PC_NAME, parler):
    pc = instruction["pc"]
    action = instruction["action"]
    plateforme = instruction["plateforme"]
    requete = instruction["requete"] or ""
    pc_info = PCS.get(pc)
    import platform
    if pc_info is None:
        if pc == LOCAL_PC_NAME:
            pc_info = {"is_local": True, "os": platform.system().lower(), "browser_cmd": ""}
        else:
            parler(f"Je ne connais pas ce PC « {pc} ». Utilise plutôt « {LOCAL_PC_NAME} » ou ajoute {pc} dans la configuration.", emotion="reflexion", memoire=memoire)
            return
    url = None
    if plateforme == "youtube":
        if not requete:
            parler("Tu veux que j’ouvre YouTube, mais il me faut ce que je dois chercher (ex: un titre de chanson).", emotion="reflexion", memoire=memoire)
            return
        url = url_youtube_recherche(requete)
    else:
        parler(f"La plateforme « {plateforme} » n’est pas encore gérée. Pour l’instant je gère « YouTube ».", emotion="reflexion", memoire=memoire)
        return
    if pc_info.get("is_local"):
        ok, err = ouvrir_url_local(url, forced_cmd=pc_info.get("browser_cmd", ""))
        if ok:
            parler(f"C’est parti ! J’ouvre « {requete} » sur {plateforme} sur {pc}.", emotion="heureux", memoire=memoire)
        else:
            parler(f"Je n’ai pas réussi à ouvrir l’URL localement : {err}", emotion="reflexion", memoire=memoire)
        return
    host = pc_info.get("host")
    user = pc_info.get("user")
    auth = pc_info.get("auth", "password")
    password = pc_info.get("password") if auth == "password" else None
    key_path = pc_info.get("key_path") if auth == "key" else None
    os_name = pc_info.get("os", "linux")
    forced_cmd = pc_info.get("browser_cmd", "")
    cmd = commande_ouvrir_url_pour_os(url, os_name, forced_cmd)
    ok, out_or_err = exec_ssh(host, user, cmd, password=password, key_path=key_path)
    if ok:
        parler(f"Commande envoyée à {pc} : j’ouvre « {requete} » sur {plateforme}.", emotion="heureux", memoire=memoire)
    else:
        parler(f"Échec sur {pc} : {out_or_err}", emotion="reflexion", memoire=memoire)
