# -*- coding: utf-8 -*-
"""
Katyusha v2.0 — Assistante + côté humain + exécution d'ordres sur PC locaux/distants.

Fonctions clés :
- Ton humain (émotions, hésitations, humeur évolutive).
- Mode "assistant" : compréhension d'ordres du type :
    "Dit Katyusha, sur PC1 lance Ciel de Gims sur YouTube"
- Exécution locale OU via SSH (Paramiko) selon le PC ciblé.
- Compatibilité Windows / Linux / macOS (commande navigateur configurable par PC).

À FAIRE :
- Remplir le dict PCS avec les infos des machines (host, user, auth...).
- Activer/installer OpenSSH sur les PC distants si nécessaire.
"""

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
from Coeur import afficher, charger_memoire, sauver_memoire, classer_ton_utilisateur, mettre_a_jour_humeur, parler
from Option import convertir_en_expression, evaluer_expression, donner_heure, meteo, extraire_ville, chercher_wikipedia
from Assistant import parser_ordre_assistant, executer_ordre_assistant, PCS, LOCAL_PC_NAME

# ---- Hygiène console
warnings.filterwarnings("ignore")
sys.stderr = open(os.devnull, 'w')
os.environ["PYTHONWARNINGS"] = "ignore"

MEMOIRE_FILE = "memoire.json"

# =========================
# CONFIGURATION DES PCS
# =========================
# Remplis ce dict avec les machines.
PCS = {
    # "PC1": {
    #     "is_local": True,                # True si c'est le PC local où tourne Katyusha
    #     "host": "192.168.1.20",
    #     "user": "mon_user",
    #     "auth": "password",               # "password" ou "key"
    #     "password": "mon_mot_de_passe",   # si auth == "password"
    #     "key_path": "~/.ssh/id_rsa",      # si auth == "key"
    #     "os": "linux",                  # "windows" | "linux" | "mac"
    #     # Commande pour ouvrir une URL sur ce PC :
    #     # Laisse vide pour auto (windows: start, linux: xdg-open, mac: open),
    #     # ou force une appli (ex: 'start microsoft-edge:' / 'start chrome' / 'xdg-open' / 'open')
    #     "browser_cmd": ""
    # },
    # "PC2": {
    #     "is_local": False,
    #     "host": "192.168.1.20",
    #     "user": "mon_user",
    #     "auth": "password",               # "password" ou "key"
    #     "password": "mon_mot_de_passe",   # si auth == "password"
    #     "key_path": "~/.ssh/id_rsa", 
    #     "os": "windows",
    #     "browser_cmd": ""  # vide => auto
    # }
}

# Le PC local soit reconnu par un nom (ex: "PCLocal")
LOCAL_PC_NAME = "Pravda"  # à utiliser dans les ordres "sur PCLocal ..."

# =========================
# CŒUR "HUMAIN"
# =========================

def ecouter():
    choix = input("🎧 Tapez [v] pour vocal ou [t] pour texte : ").strip().lower()
    if choix == "t":
        texte = input("✍️ Vous : ")
        return texte
    elif choix == "v":
        import speech_recognition as sr
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
# ROUTAGE DES COMMANDES
# =========================

def traiter(commande_brute, memoire):
    ton = classer_ton_utilisateur(commande_brute)
    mettre_a_jour_humeur(memoire, ton)
    sauver_memoire(memoire)

    commande = commande_brute.lower()

    # --- Réactions émotionnelles immédiates ---
    if any(mot in commande for mot in ["merci", "super", "génial", "bravo"]):
        parler(random.choice([
            "Avec plaisir !",
            "Ça me fait plaisir de t'aider !",
            "Merci à toi aussi !",
            "Toujours là pour toi !"
        ]), emotion="heureux", memoire=memoire)
        return

    if any(mot in commande for mot in ["nulle", "idiote", "stupide", "mauvaise", "incompétente"]):
        parler(random.choice([
            "Oh... ça fait mal ce que tu dis.",
            "D'accord... je vais essayer de faire mieux.",
            "Je pensais bien faire pourtant...",
            "Tu es dur avec moi..."
        ]), emotion="triste", memoire=memoire)
        return

    instruction = parser_ordre_assistant(commande_brute)
    if instruction:
        executer_ordre_assistant(instruction, memoire, PCS, LOCAL_PC_NAME, parler)
        return
    commande = commande_brute.lower()
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