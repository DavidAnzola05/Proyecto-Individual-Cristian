from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .serializers import TareasSerializer
from backend.firebase_config import get_firestore_client
from firebase_admin import firestore
from .authentication import FirebaseAuthentication  
db = get_firestore_client()


class TareaAPIView(APIView):

    # Autenticación personalizada
    authentication_classes = [FirebaseAuthentication]
    permission_classes = [IsAuthenticated]

    """
    Endpoint para:
    - GET: listar tareas del usuario autenticado
    - POST: crear nueva tarea
    - PUT: actualizar tarea
    - DELETE: eliminar tarea
    """

    # 🔹 GET
    def get(self, request, tarea_id=None):

        uid_usuario = request.user.uid
        rol_usuario = request.user.rol

        # 🔹 1️⃣ DETALLE (buscar por ID)
        if tarea_id:
            doc_ref = db.collection('api_tareas').document(tarea_id)
            doc = doc_ref.get()

            if not doc.exists:
                return Response({"error": "No existe"}, status=404)

            data = doc.to_dict()
            data["id"] = doc.id
            return Response(data)

        # 🔹 2️⃣ LISTADO (AQUÍ VA LO QUE PREGUNTAS)

        # Obtener limit (default 10)
        limit = int(request.query_params.get("limit", 10))

        # Obtener last_doc_id
        last_doc_id = request.query_params.get("last_doc_id")

        # 🔹 3️⃣ Lógica por rol
        if rol_usuario == "instructor":
            query = db.collection("api_tareas")
        else:
            query = db.collection("api_tareas").where(
                "usuario_id", "==", uid_usuario
            )

        # 🔥 4️⃣ ORDER_BY OBLIGATORIO
        query = query.order_by("fecha_creacion")

        # 🔹 5️⃣ Paginación con cursor
        if last_doc_id:
            last_document = db.collection("api_tareas").document(last_doc_id).get()
            if last_document.exists:
                query = query.start_after(last_document)

        # 🔹 6️⃣ Aplicar limit
        docs = query.limit(limit).stream()

        tareas = []
        ultimo_id = None

        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            tareas.append(data)
            ultimo_id = doc.id

        return Response({
            "limite_usado": limit,
            "last_doc_id": ultimo_id,
            "datos": tareas
        })

    # 🔹 POST
    def post(self, request):
        serializer = TareasSerializer(data=request.data)

        if serializer.is_valid():
            datos_validados = serializer.validated_data
            datos_validados['usuario_id'] = request.user.uid
            datos_validados['fecha_creacion'] = firestore.SERVER_TIMESTAMP

            try:
                nuevo_doc = db.collection('api_tareas').add(datos_validados)
                id_generado = nuevo_doc[1].id

                return Response(
                    {
                        "mensaje": "La tarea fue creada correctamente",
                        "id": id_generado
                    },
                    status=status.HTTP_201_CREATED
                )

            except Exception as e:
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # 🔹 PUT
    def put(self, request, pk):
        doc_ref = db.collection('api_tareas').document(pk)
        doc = doc_ref.get()

        try:
            if not doc.exists:
                return Response(
                    {"error": "La tarea no existe"},
                    status=status.HTTP_404_NOT_FOUND
                )

            tarea_data = doc.to_dict()

            # ✅ corregido uid
            if tarea_data.get('usuario_id') != request.user.uid:
                return Response(
                    {"error": "No tienes permiso para editar esta tarea"},
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = TareasSerializer(data=request.data)

            if serializer.is_valid():
                doc_ref.update(serializer.validated_data)

                return Response(
                    {
                        "mensaje": f"La tarea {pk} fue actualizada correctamente",
                        "id": pk,
                        "datos": serializer.data
                    },
                    status=status.HTTP_200_OK
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # 🔹 DELETE
    def delete(self, request, pk):
        if not pk:
            return Response(
                {"error": "Se requiere el id de la tarea"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            tarea_ref = db.collection('api_tareas').document(pk)
            doc = tarea_ref.get()

            if not doc.exists:
                return Response(
                    {"error": "La tarea no existe"},
                    status=status.HTTP_404_NOT_FOUND
                )

            tarea_data = doc.to_dict()

            # ✅ Validar dueño antes de eliminar
            if tarea_data.get('usuario_id') != request.user.uid:
                return Response(
                    {"error": "No tienes permiso para eliminar esta tarea"},
                    status=status.HTTP_403_FORBIDDEN
                )

            tarea_ref.delete()

            return Response(
                {"mensaje": f"Tarea {pk} eliminada correctamente"},
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )