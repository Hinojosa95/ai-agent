from app import generar_audio_elevenlabs

texto = "Hi, my name is Bryan and this is a test using my cloned voice in English."
archivo = "test_cloned_voice_en.mp3"

url = generar_audio_elevenlabs(texto, archivo)
print("✅ Audio generado. URL:", url)