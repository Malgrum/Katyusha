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