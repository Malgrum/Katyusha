# -*- coding: utf-8 -*-
"""
Calcule.py — Fonctions utilitaires (calcul, heure, météo, Wikipedia).
"""
import re
from datetime import datetime
import requests
from urllib.parse import quote_plus, urlencode

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
        api_key = "6fcecbe2c35649f290a161321252306"
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

def chercher_wikipedia(question):
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
            titre_encoded = quote_plus(titre)
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