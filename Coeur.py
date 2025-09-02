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
    Pourras améliorer avec un vrai modèle plus tard.
    """
    t = texte_utilisateur.lower()
    if any(g in t for g in ["merci", "bravo", "bien joué", "génial", "super", "excellent"]):
        return "positif"
    if any(g in t for g in ["nul", "idiote", "ferme-la", "stupide", "conne", "dégage", "chier"]):
        return "negatif"
    return "neutre"

def mettre_a_jour_humeur(memoire, ton_utilisateur: str):
    score = memoire.get("humeur_score", 0)
    if ton_utilisateur == "positif":
        score += 1
    elif ton_utilisateur == "negatif":
        score -= 2  # on blesse plus vite qu'on ne félicite

    memoire["humeur_score"] = max(-5, min(5, score))
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