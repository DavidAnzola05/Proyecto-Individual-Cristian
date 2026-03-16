from google import genai 
client = genai.Client(api_key="AIzaSyCVGiBCe3vjMJARiE4GM2ZwV8JDz3vFjb0")
for m in client.models.list():
    print(f"Modelo Disponible: {m.name}" )