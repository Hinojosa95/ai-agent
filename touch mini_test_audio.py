# mini_test_audio.py
from app import generar_audio_elevenlabs

url = generar_audio_elevenlabs("Hola, soy Bryan y esta es una prueba", "prueba_clonada.mp3")
print("✅ URL generada:", url)