import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("❌ No se encontró la clave OPENAI_API_KEY en el entorno.")

def get_response(messages):
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"❌ Error al obtener respuesta de OpenAI: {e}")
        return "Lo siento, hubo un problema procesando tu solicitud. ¿Podrías repetir por favor?"
