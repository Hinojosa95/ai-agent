# mini_test_audio.py
from app import generar_audio_elevenlabs

texto = "Hola, soy Bryan y esta es una prueba con mi voz clonada"
archivo = "prueba_clonada.mp3"

url = generar_audio_elevenlabs(texto, archivo)
print("✅ Audio generado. URL:", url)