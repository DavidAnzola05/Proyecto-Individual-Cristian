import requests
import getpass
import time
from google import genai
from google.genai import types


def login_usuario():
    print("--- Login Usuario ---")

    email = input("Email: ")
    password = getpass.getpass("Contraseña: ")

    url_login = "http://127.0.0.1:8000/api/auth/login/"

    try:
        response = requests.post(
            url_login,
            json={"email": email, "password": password}
        )

        if response.status_code == 200:
            print("✅ Usuario logeado correctamente")
            return response.json().get("token")

        print(f"❌ Error: {response.json().get('error')}")

    except Exception as e:
        print("❌ Error de conexión:", e)

    return None


def consultar_mis_tareas(token):
    print("🔎 Consultando tus tareas...")

    url = "http://127.0.0.1:8000/api/tareas/"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        res = requests.get(url, headers=headers)
        return res.json()

    except Exception as e:
        return {"error": str(e)}


# 🔐 LOGIN
token = login_usuario()

# 🔑 API KEY GEMINI
API_KEY = "AIzaSyD6OnGFgma8ZBbgebczPWDNdwe3eG0FQvQ"

client = genai.Client(api_key=API_KEY)

modelo_id = "gemini-2.5-flash"


if token:

    print("\n🤖 Hola, soy tu agente IA")

    while True:

        user_input = input("\nTú: ")

        if user_input.lower() in ['salir', 'exit', 'chao', 'bye']:
            break

        # 🔹 Si el usuario pregunta por tareas
        if "tarea" in user_input.lower():

            tareas = consultar_mis_tareas(token)

            print("\n📋 Tus tareas:")
            print(tareas)

            continue

        prompt = (
            f"Contexto: El usuario tiene un sistema de tareas."
            f"Pregunta del usuario: {user_input}"
        )

        try:

            response = client.models.generate_content(
                model=modelo_id,
                contents=prompt
            )

            print(f"\nIA: {response.text}")

        except Exception as e:
            print("Error:", e)

            if "429" in error_str:
                print("⚠️ IA: agotamos las peticiones gratuitas por minuto, espera 20 segundos")
                time.sleep(20)

            elif "404" in error_str:
                print("⚠️ IA: modelo no encontrado")

            else:
                print("❌ Error:", e)