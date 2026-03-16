from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_admin import auth
from backend.firebase_config import get_firestore_client

db = get_firestore_client()


class FirebaseAuthentication(BaseAuthentication):

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        partes = auth_header.split()

        if len(partes) != 2 or partes[0].lower() != 'bearer':
            raise AuthenticationFailed("Formato de token inválido")

        token = partes[1]

        try:
            decoded_token = auth.verify_id_token(token)

            uid = decoded_token.get('uid')
            email = decoded_token.get('email')

            # 🔹 Buscar rol en Firestore
            user_profile = db.collection('perfiles').document(uid).get()

            if user_profile.exists:
                rol = user_profile.to_dict().get('rol', 'aprendiz')
            else:
                rol = 'aprendiz'

            # 🔹 Crear objeto usuario compatible con DRF
            class FirebaseUser:
                def __init__(self, uid, rol, email):
                    self.uid = uid
                    self.rol = rol
                    self.email = email
                    self.is_authenticated = True

            user = FirebaseUser(uid, rol, email)

            return (user, token)

        except Exception:
            raise AuthenticationFailed("Token no válido o expirado")