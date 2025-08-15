# -*- coding: utf-8 -*-
"""
Katyusha v2.0 — Assistante + côté humain + exécution d'ordres sur PC locaux/distants.

Fonctions clés :
- Ton humain (émotions, hésitations, humeur évolutive).
- Mode "assistant" : compréhension d'ordres du type :
    "Dit Katyusha, sur PC1 lance Ciel de Gims sur YouTube"
- Exécution locale OU via SSH (Paramiko) selon le PC ciblé.
- Compatibilité Windows / Linux / macOS (commande navigateur configurable par PC).

Dépendances supplémentaires :
    pip install paramiko

À FAIRE (par toi) :
- Remplir le dict PCS avec les infos de tes machines (host, user, auth...).
- Activer/installer OpenSSH sur les PC distants si nécessaire.
"""

import speech_recognition as sr
import json
import os
import requests
import re
import random
import webbrowser
import platform
from urllib.parse import quote_plus
from datetime import datetime
import warnings
import sys

# ---- SSH (pour l'exécution distante)
try:
    import paramiko
except Exception:
    paramiko = None  # On gèrera le cas où Paramiko n'est pas installé

# ---- Hygiène console
warnings.filterwarnings("ignore")
sys.stderr = open(os.devnull, 'w')
os.environ["PYTHONWARNINGS"] = "ignore"

MEMOIRE_FILE = "memoire.json"

# =========================
# CONFIGURATION DES PCS
# =========================
# Remplis ce dict avec tes machines. Tu peux dupliquer l'exemple.
PCS = {
    # "PC1": {
    #     "is_local": False,                # True si c'est le PC local où tourne Katyusha
    #     "host": "192.168.1.20",
    #     "user": "ton_user",
    #     "auth": "password",               # "password" ou "key"
    #     "password": "ton_mot_de_passe",   # si auth == "password"
    #     "key_path": "~/.ssh/id_rsa",      # si auth == "key"
    #     "os": "windows",                  # "windows" | "linux" | "mac"
    #     # Commande pour ouvrir une URL sur ce PC :
    #     # Laisse vide pour auto (windows: start, linux: xdg-open, mac: open),
    #     # ou force une appli (ex: 'start microsoft-edge:' / 'start chrome' / 'xdg-open' / 'open')
    #     "browser_cmd": ""
    # },
    # "PC2": {
    #     "is_local": True,
    #     "os": "linux",
    #     "browser_cmd": ""  # vide => auto
    # }
}

# Si tu veux que le PC local soit reconnu par un nom (ex: "PCLocal")
LOCAL_PC_NAME = "PCLocal"  # à utiliser dans tes ordres "sur PCLocal ..."

# =========================
# CŒUR "HUMAIN"
# =========================

def afficher(texte):
    print("Katyusha:", texte)

def charger_memoire():
    if os.path.exists(MEMOIRE_FILE):
        try:
            with open(MEMOIRE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Valeurs par défaut si anciennes structures
            data.setdefault("humeur", "neutre")
            data.setdefault("humeur_score", 0)
            return data
        except Exception:
            return {"humeur": "neutre", "humeur_score": 0}
    else:
        return {"humeur": "neutre", "humeur_score": 0}

def sauver_memoire(memoire):
    with open(MEMOIRE_FILE, "w", encoding="utf-8") as f:
        json.dump(memoire, f, indent=4, ensure_ascii=False)

def classer_ton_utilisateur(texte_utilisateur: str) -> str:
    """
    Très simple "détection" d'attitude de l'utilisateur.
    Tu pourras améliorer avec un vrai modèle plus tard.
    """
    t = texte_utilisateur.lower()
    if any(g in t for g in ["merci", "bravo", "bien joué", "génial", "super"]):
        return "positif"
    if any(g in t for g in ["nul", "idiote", "ferme-la", "stupide", "conne", "dégage"]):
        return "negatif"
    return "neutre"

def mettre_a_jour_humeur(memoire, ton_utilisateur: str):
    score = memoire.get("humeur_score", 0)
    if ton_utilisateur == "positif":
        score += 1
    elif ton_utilisateur == "negatif":
        score -= 2  # on blesse plus vite qu'on ne félicite 😉
    memoire["humeur_score"] = max(-5, min(5, score))
    # Discrétisation
    if score >= 3:
        memoire["humeur"] = "joyeuse"
    elif score <= -3:
        memoire["humeur"] = "vexée"
    else:
        memoire["humeur"] = "neutre"

def parler(texte, emotion=None, memoire=None):
    """
    Parle avec un style humain : micro-hésitations, interjections, emojis selon l'humeur/émotion.
    """
    reactions_chaleureuses = ["😊", "😉", "✨", "👍", "😄"]
    reactions_surprises = ["Oh !", "Tiens donc...", "Ah, intéressant !", "Oh, ça alors !"]
    reactions_reflexion = ["Hmm...", "Voyons voir...", "Attends une seconde...", "Laisse-moi réfléchir..."]
    reactions_vexee = ["Bon...", "Très bien.", "Comme tu veux.", "D'accord."]

    # Petite hésitation aléatoire
    if random.random() < 0.12:
        texte = random.choice(["Euh...", "Mmh...", "Alors..."]) + " " + texte

    # Ajustement par émotion ponctuelle
    if emotion == "heureux":
        texte = random.choice(reactions_chaleureuses) + " " + texte
    elif emotion == "surpris":
        texte = random.choice(reactions_surprises) + " " + texte
    elif emotion == "reflexion":
        texte = random.choice(reactions_reflexion) + " " + texte

    # Teinte globale par l'humeur persistante
    if memoire:
        h = memoire.get("humeur", "neutre")
        if h == "joyeuse" and random.random() < 0.25 and emotion not in ("heureux",):
            texte = random.choice(reactions_chaleureuses) + " " + texte
        elif h == "vexée" and random.random() < 0.25:
            texte = random.choice(reactions_vexee) + " " + texte

    afficher(texte)

# =========================
# ÉCOUTE
# =========================

def ecouter():
    choix = input("🎧 Tapez [v] pour vocal ou [t] pour texte : ").strip().lower()

    if choix == "t":
        texte = input("✍️ Vous : ")
        return texte

    elif choix == "v":
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("🎤 Katyusha écoute...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)
        try:
            texte = recognizer.recognize_google(audio, language="fr-FR")
            print("🗣️ Vous avez dit :", texte)
            return texte
        except Exception:
            print("⚠️ Désolé, je n'ai pas compris.")
            return ""

    else:
        print("❓ Option invalide. Tapez 'v' ou 't'.")
        return ecouter()

# =========================
# UTILITAIRES (heure, météo, calcul)
# =========================

def convertir_en_expression(texte):
    # lower sans toucher aux nombres
    t = texte.lower()
    remplacements = {
        "puissance": "**", "fois": "*", "multiplié par": "*", "divisé par": "/",
        "sur": "/", "plus": "+", "moins": "-", "parenthèse ouvrante": "(", 
        "parenthèse fermante": ")", "égal": "=", "virgule": ".", "et": "+",
        "zéro": "0", "un": "1", "deux": "2", "trois": "3", "quatre": "4", 
        "cinq": "5", "six": "6", "sept": "7", "huit": "8", "neuf": "9",
        "dix": "10", "onze": "11", "douze": "12", "treize": "13", 
        "quatorze": "14", "quinze": "15", "seize": "16", "vingt": "20", 
        "trente": "30", "quarante": "40", "cinquante": "50", 
        "soixante": "60", "soixante-dix": "70", "quatre-vingt": "80", 
        "quatre-vingt-dix": "90", "cent": "100", "mille": "1000"
    }
    for mot, symbole in remplacements.items():
        t = t.replace(mot, f" {symbole} ")
    t = re.sub(r"[^0-9\.\+\-\*\/\(\)\s\**]", "", t)
    return t

def evaluer_expression(expression):
    try:
        result = eval(expression, {"__builtins__": None}, {})
        return f"Le résultat est : {result}"
    except Exception:
        return "Je n'ai pas réussi à calculer cela."

def donner_heure():
    maintenant = datetime.now()
    return maintenant.strftime("Il est %H heure %M")

def meteo(ville="Strasbourg"):
    try:
        api_key = "6fcecbe2c35649f290a161321252306"  # ⚠️ remplace si besoin
        url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={quote_plus(ville)}&lang=fr"
        response = requests.get(url, timeout=5)
        data = response.json()

        if "current" in data:
            temp = data["current"]["temp_c"]
            condition = data["current"]["condition"]["text"]
            return f"À {ville}, il fait {temp}°C avec {condition.lower()}."
        else:
            return "Je n'ai pas pu obtenir la météo pour cette ville."
    except Exception as e:
        return f"Erreur météo : {e}"

def extraire_ville(commande):
    mots = commande.split()
    for i in range(len(mots)):
        if mots[i].lower() == "à" and i + 1 < len(mots):
            return mots[i + 1]
    return "Strasbourg"

# =========================
# MODE ASSISTANT : PARSING
# =========================

ASSISTANT_PREFIXES = [
    r"\bdit\s+katyusha\b",
    r"\bdis\s+katyusha\b",
    r"\bkatyusha\b"
]

def parser_ordre_assistant(texte: str):
    """
    Exemples compris :
      - "Dit Katyusha, sur PC1 lance Ciel de Gims sur youtube"
      - "Katyusha sur PC1 ouvre Ciel de Gims sur YouTube"
      - "Katyusha lance Ciel de Gims sur YouTube" (pas de PC => local)
    Sortie:
      dict | None
      {
        "pc": "PC1" | LOCAL_PC_NAME,
        "action": "ouvrir"|"lancer"|"jouer",
        "plateforme": "youtube",
        "requete": "Ciel de Gims"
      }
    """
    t = " " + texte.strip() + " "
    # Doit commencer par un des préfixes
    if not re.search("|".join(ASSISTANT_PREFIXES), t, flags=re.I):
        return None

    # PC cible (optionnel)
    m_pc = re.search(r"\bsur\s+([a-z0-9\-_]+)\b", t, flags=re.I)
    pc = m_pc.group(1) if m_pc else LOCAL_PC_NAME

    # Action
    m_act = re.search(r"\b(lance|lancer|ouvre|ouvrir|joue|jouer)\b", t, flags=re.I)
    action = (m_act.group(1).lower() if m_act else "ouvre")
    action = {"lancer": "lance", "ouvrir": "ouvre", "jouer": "joue"}.get(action, action)

    # Plateforme
    m_plat = re.search(r"\bsur\s+(youtube|yt|spotify|deezer)\b", t, flags=re.I)
    plateforme = m_plat.group(1).lower() if m_plat else "youtube"
    if plateforme == "yt":
        plateforme = "youtube"

    # Requête (le morceau entre l'action et 'sur <plateforme>' si présent)
    # On tente d'extraire un bloc textual utile
    # 1) Entre action et "sur <plateforme>"
    req = None
    if m_plat:
        start = m_act.end() if m_act else 0
        end = m_plat.start()
        req = t[start:end].strip(" ,.:;!?")
    # 2) Sinon : après action jusqu'à la fin
    if not req:
        req = t[m_act.end():].strip() if m_act else t.strip()
    # Nettoyage
    # Retire connecteurs de PC et plateforme résiduels
    req = re.sub(r"\bsur\s+[a-z0-9\-_]+\b", "", req, flags=re.I)
    req = re.sub(r"\bsur\s+(youtube|yt|spotify|deezer)\b", "", req, flags=re.I)
    req = req.strip(" ,.:;!?")
    # Si vide, on met None
    if not req:
        req = None

    return {
        "pc": pc,
        "action": action,
        "plateforme": plateforme,
        "requete": req
    }

# =========================
# MODE ASSISTANT : EXÉCUTION
# =========================

def url_youtube_recherche(query: str) -> str:
    return f"https://www.youtube.com/results?search_query={quote_plus(query)}"

def commande_ouvrir_url_pour_os(url: str, os_name: str, forced_cmd: str = "") -> str:
    """
    Renvoie la commande shell pour ouvrir une URL selon l'OS cible.
    Si "forced_cmd" est fourni, on l'utilise (ex: 'start', 'start chrome', 'xdg-open', 'open').
    """
    if forced_cmd:
        # ex: windows: 'start "" "<url>"' ou 'start chrome "<url>"'
        #     linux: 'xdg-open "<url>"'
        #     mac:   'open "<url>"'
        if forced_cmd.lower().startswith("start"):
            # Windows
            return f'cmd /c {forced_cmd} "{url}"' if ' ' in forced_cmd else f'cmd /c start "" "{url}"'
        else:
            return f'{forced_cmd} "{url}"'

    os_name = os_name.lower()
    if os_name.startswith("win"):
        return f'cmd /c start "" "{url}"'
    if os_name.startswith("mac"):
        return f'open "{url}"'
    # linux par défaut
    return f'xdg-open "{url}"'

def ouvrir_url_local(url: str, forced_cmd: str = ""):
    """
    Ouvre l'URL localement. Si forced_cmd est vide, use webbrowser (fallback auto).
    """
    if forced_cmd:
        # Exécute une commande locale
        try:
            # Evite d'importer subprocess tout en restant simple : webbrowser fait déjà le job le plus souvent
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

def executer_ordre_assistant(instruction: dict, memoire):
    """
    Exécute l'ordre assistant sur le PC ciblé.
    Pour l'instant : action = lance/ouvre/joue + plateforme youtube => ouvrir URL de recherche.
    """
    pc = instruction["pc"]
    action = instruction["action"]
    plateforme = instruction["plateforme"]
    requete = instruction["requete"] or ""

    # Par défaut : si PC inconnu, on considère local
    pc_info = PCS.get(pc)
    if pc_info is None:
        # Permet d'utiliser un nom local arbitraire (LOCAL_PC_NAME)
        if pc == LOCAL_PC_NAME:
            pc_info = {"is_local": True, "os": platform.system().lower(), "browser_cmd": ""}
        else:
            parler(f"Je ne connais pas ce PC « {pc} ». Utilise plutôt « {LOCAL_PC_NAME} » ou ajoute {pc} dans la configuration.", emotion="reflexion", memoire=memoire)
            return

    # Construit l'URL selon plateforme
    url = None
    if plateforme == "youtube":
        if not requete:
            parler("Tu veux que j’ouvre YouTube, mais il me faut ce que je dois chercher (ex: un titre de chanson).", emotion="reflexion", memoire=memoire)
            return
        url = url_youtube_recherche(requete)
    else:
        parler(f"La plateforme « {plateforme} » n’est pas encore gérée. Pour l’instant je gère « YouTube ».", emotion="reflexion", memoire=memoire)
        return

    # Exécution locale ou distante
    if pc_info.get("is_local"):
        ok, err = ouvrir_url_local(url, forced_cmd=pc_info.get("browser_cmd", ""))
        if ok:
            parler(f"C’est parti ! J’ouvre « {requete} » sur {plateforme} sur {pc}.", emotion="heureux", memoire=memoire)
        else:
            parler(f"Je n’ai pas réussi à ouvrir l’URL localement : {err}", emotion="reflexion", memoire=memoire)
        return

    # Sinon, exécution distante via SSH
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

# =========================
# WIKIPEDIA
# =========================

def chercher_wikipedia(question):
    import urllib.parse
    search_url = "https://fr.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "search",
        "srsearch": question,
        "format": "json",
        "srlimit": 1,
    }
    try:
        response = requests.get(search_url, params=params, timeout=5)
        data = response.json()
        if data.get("query", {}).get("search"):
            titre = data["query"]["search"][0]["title"]
            titre_encoded = urllib.parse.quote(titre)
            summary_url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{titre_encoded}"
            resp2 = requests.get(summary_url, timeout=5)
            if resp2.status_code == 200:
                extract = resp2.json().get("extract")
                return extract if extract else "Je n'ai pas trouvé d'extrait pour cette page."
            else:
                return "Impossible de récupérer le résumé Wikipedia."
        else:
            return "Aucun résultat Wikipedia trouvé."
    except Exception as e:
        return f"Erreur lors de la recherche Wikipedia : {e}"

# =========================
# ROUTAGE DES COMMANDES
# =========================

def traiter(commande_brute, memoire):
    """
    Route soit vers le mode assistant (si préfixes reconnus),
    soit vers les outils classiques (météo, heure, calcul, wikipedia/mémoire).
    """
    # Met à jour l'humeur selon le ton du message
    ton = classer_ton_utilisateur(commande_brute)
    mettre_a_jour_humeur(memoire, ton)
    sauver_memoire(memoire)

    # Détection "mode assistant"
    instruction = parser_ordre_assistant(commande_brute)
    if instruction:
        executer_ordre_assistant(instruction, memoire)
        return

    commande = commande_brute.lower()

    # Fonctions classiques
    if "météo" in commande or "temps" in commande:
        ville = extraire_ville(commande)
        reponse = meteo(ville)
        parler("🌦️ " + reponse, emotion="heureux", memoire=memoire)

    elif any(mot in commande for mot in ["calcule", "combien", "font", "fait", "résultat"]):
        expression = convertir_en_expression(commande)
        reponse_calcul = evaluer_expression(expression)
        parler(reponse_calcul, emotion="reflexion", memoire=memoire)
    
    elif "heure" in commande:
        reponse = donner_heure()
        parler(reponse, emotion="heureux", memoire=memoire)

    elif commande in memoire:
        parler(memoire[commande], emotion="heureux", memoire=memoire)

    else:
        reponse_web = chercher_wikipedia(commande_brute)
        if reponse_web and "introuvable" not in reponse_web.lower() and not reponse_web.startswith("Erreur"):
            parler("J'ai trouvé ceci sur Wikipedia :", emotion="surpris", memoire=memoire)
            for i in range(0, len(reponse_web), 600):
                parler(reponse_web[i:i+600], memoire=memoire)
            parler("Veux-tu que je mémorise cette réponse pour la prochaine fois ?", emotion="reflexion", memoire=memoire)
            confirmation = ecouter()
            if confirmation and "oui" in confirmation.lower():
                memoire[commande] = reponse_web
                sauver_memoire(memoire)
                parler("Réponse enregistrée.", emotion="heureux", memoire=memoire)
            else:
                parler("D'accord, je n'enregistrerai pas cette réponse.", emotion="reflexion", memoire=memoire)
        else:
            parler("Je ne connais pas la réponse et je n'ai rien trouvé sur Internet.", emotion="reflexion", memoire=memoire)

# =========================
# MAIN
# =========================

def main():
    memoire = charger_memoire()
    # Enregistre le nom du PC local comme connu (si tu veux)
    if LOCAL_PC_NAME and LOCAL_PC_NAME not in PCS:
        PCS[LOCAL_PC_NAME] = {
            "is_local": True,
            "os": platform.system().lower(),
            "browser_cmd": ""
        }

    parler("Bonjour, je suis Katyusha. Dis-moi ce que je peux faire pour toi.", emotion="heureux", memoire=memoire)
    while True:
        commande = ecouter()
        if not commande:
            continue
        if any(x in commande.lower() for x in ["au revoir", "quitte", "exit", "bye"]):
            parler("Au revoir !", emotion="heureux", memoire=memoire)
            break
        traiter(commande, memoire)

if __name__ == "__main__":
    main()
