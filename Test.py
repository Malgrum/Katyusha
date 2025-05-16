from TTS.api import TTS
# Charge un modèle français féminin (exemple)
tts = TTS(model_name="tts_models/fr/mai/tacotron2-DDC")

# Synthèse vocale vers fichier
tts.tts_to_file(text="Bonjour, je suis Katyusha votre assistant vocal.", file_path="output.wav")

print("Fichier output.wav généré !")
