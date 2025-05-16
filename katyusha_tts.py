from TTS.api import TTS
import simpleaudio as sa

tts = TTS(model_name="tts_models/fr/mai/vits")

def parler(texte):
    tts.tts_to_file(text=texte, file_path="output.wav")
    wave_obj = sa.WaveObject.from_wave_file("output.wav")
    play_obj = wave_obj.play()
    play_obj.wait_done()

parler("Bonjour, je suis Katyusha avec une voix naturelle.")
