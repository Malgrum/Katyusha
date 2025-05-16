import speech_recognition as sr
import pyttsx3
import json
import os
import requests

# Initialisation du moteur vocal
engine = pyttsx3.init()
engine.setProperty('rate', 150)

# Sélection de la voix (adapter l'index selon ta voix préférée)
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # voices[0] = 1ère voix (souvent féminine ou masculine selon système)

MEMOIRE_FILE = "memoire_katyusha.json"

def parler(texte):
    print("Katyusha:", texte)
    engine.say(texte)
    engine.runAndWait()

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
        parler("Désolé, je n'ai pas compris.")
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

    # Endpoint API pour la recherche
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
            # Titre de la première page trouvée
            titre = data["query"]["search"][0]["title"]
            titre_encoded = urllib.parse.quote(titre)

            # Récupérer l'extrait de cette page
            summary_url = f"https://fr.wikipedia.org/api/rest_v1/page/summary/{titre_encoded}"
            resp2 = requests.get(summary_url, timeout=5)
            if resp2.status_code == 200:
                extract = resp2.json().get("extract")
                if extract:
                    return extract
                else:
                    return "Je n'ai pas trouvé d'extrait pour cette page."
            else:
                return "Impossible de récupérer le résumé Wikipedia."
        else:
            return "Aucun résultat Wikipedia trouvé."
    except Exception as e:
        return f"Erreur lors de la recherche Wikipedia : {e}"


def traiter(commande, memoire):
    if commande in memoire:
        parler(memoire[commande])
    else:
        reponse_web = chercher_wikipedia(commande)
        if reponse_web and "introuvable" not in reponse_web.lower() and not reponse_web.startswith("Erreur"):
            parler("J'ai trouvé ceci sur Wikipedia :")
            # Parler la réponse par morceaux si trop longue (ex: 300 caractères max)
            for i in range(0, len(reponse_web), 300):
                parler(reponse_web[i:i+300])
            parler("Veux-tu que je mémorise cette réponse pour la prochaine fois ?")
            confirmation = ecouter()
            if "oui" in confirmation:
                memoire[commande] = reponse_web
                sauver_memoire(memoire)
                parler("Réponse enregistrée.")
            else:
                parler("D'accord, je n'enregistrerai pas cette réponse.")
        else:
            parler("Je ne connais pas la réponse et je n'ai rien trouvé sur Internet.")

def main():
    memoire = charger_memoire()
    parler("Bonjour, je suis Katyusha, votre assistante. Que puis-je faire ?")
    while True:
        commande = ecouter()
        if not commande:
            continue
        if "au revoir" in commande or "quitte" in commande:
            parler("Au revoir !")
            break
        traiter(commande, memoire)

if __name__ == "__main__":
    main()
