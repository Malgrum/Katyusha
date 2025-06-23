import speech_recognition as sr
import json
import os
import requests
import re
from datetime import datetime

MEMOIRE_FILE = "memoire.json"
CLE_METEO = "6fcecbe2c35649f290a161321252306"  # 🔁 remplace par clé OpenWeather

def afficher(texte):
    print("Katyusha:", texte)

def ecouter():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Katyusha écoute...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        texte = recognizer.recognize_google(audio, language="fr-FR")
        print("🗣️ Vous avez dit :", texte)
        return texte.lower()
    except Exception:
        afficher("Désolé, je n'ai pas compris.")
        return ""

def charger_memoire():
    if os.path.exists(MEMOIRE_FILE):
        with open(MEMOIRE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}

def sauver_memoire(memoire):
    with open(MEMOIRE_FILE, "w", encoding="utf-8") as f:
        json.dump(memoire, f, indent=4, ensure_ascii=False)

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
        if data["query"]["search"]:
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

def convertir_en_expression(texte):
    remplacements = {
        "puissance": "**",
        "fois": "*",
        "multiplié par": "*",
        "divisé par": "/",
        "sur": "/",
        "plus": "+",
        "moins": "-",
        "parenthèse ouvrante": "(",
        "parenthèse fermante": ")",
        "égal": "=",
        "virgule": ".",
        "et": "+",
        "zéro": "0", "un": "1", "deux": "2", "trois": "3", "quatre": "4",
        "cinq": "5", "six": "6", "sept": "7", "huit": "8", "neuf": "9",
        "dix": "10", "onze": "11", "douze": "12", "treize": "13", "quatorze": "14",
        "quinze": "15", "seize": "16", "vingt": "20", "trente": "30", "quarante": "40",
        "cinquante": "50", "soixante": "60", "soixante-dix": "70", "quatre-vingt": "80",
        "quatre-vingt-dix": "90", "cent": "100", "mille": "1000"
    }
    for mot, symbole in remplacements.items():
        texte = texte.replace(mot, f" {symbole} ")
    texte = re.sub(r"[^0-9\.\+\-\*\/\(\)\s\**]", "", texte)
    return texte

def evaluer_expression(expression):
    try:
        result = eval(expression, {"__builtins__": None}, {})
        return f"Le résultat est : {result}"
    except Exception:
        return "Je n'ai pas réussi à calculer cela."

def donner_heure():
    maintenant = datetime.now()
    return maintenant.strftime("Il est %H heure %M")

def obtenir_meteo(ville="Strasbourg"):
    url = url = f"http://api.weatherapi.com/v1/current.json?key={api_key}&q={ville}&lang=fr"
    try:
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
        if mots[i] == "à" and i + 1 < len(mots):
            return mots[i + 1]
    return "Strasbourg"

def traiter(commande, memoire):
    if "météo" in commande or "temps" in commande:
    ville = "Strasbourg"  
    mots = commande.split()
    for i, mot in enumerate(mots):
        if mot == "à" and i + 1 < len(mots):
            ville = mots[i + 1]
            break
    reponse = meteo(ville)
    print("🌦️", reponse)

    elif any(mot in commande for mot in ["calcule", "combien", "font", "fait", "résultat"]):
        expression = convertir_en_expression(commande)
        reponse_calcul = evaluer_expression(expression)
        afficher(reponse_calcul)
    
    elif "heure" in commande:
        reponse = donner_heure()
        print(reponse)

    elif commande in memoire:
        afficher(memoire[commande])

    else:
        reponse_web = chercher_wikipedia(commande)
        if reponse_web and "introuvable" not in reponse_web.lower() and not reponse_web.startswith("Erreur"):
            afficher("J'ai trouvé ceci sur Wikipedia :")
            for i in range(0, len(reponse_web), 600):
                afficher(reponse_web[i:i+600])
            afficher("Veux-tu que je mémorise cette réponse pour la prochaine fois ?")
            confirmation = ecouter()
            if "oui" in confirmation:
                memoire[commande] = reponse_web
                sauver_memoire(memoire)
                afficher("Réponse enregistrée.")
            else:
                afficher("D'accord, je n'enregistrerai pas cette réponse.")
        else:
            afficher("Je ne connais pas la réponse et je n'ai rien trouvé sur Internet.")

def main():
    memoire = charger_memoire()
    afficher("Bonjour, je suis Katyusha, votre assistante. Que puis-je faire ?")
    while True:
        commande = ecouter()
        if not commande:
            continue
        if "au revoir" in commande or "quitte" in commande:
            afficher("Au revoir !")
            break
        traiter(commande, memoire)

if __name__ == "__main__":
    main()