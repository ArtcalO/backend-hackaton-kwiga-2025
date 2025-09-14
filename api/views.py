from rest_framework import viewsets, permissions, mixins
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from .models import *
from .serializers import *
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.contenttypes.models import ContentType
from .utils import get_user_profile
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from django_filters import rest_framework as filters
from rest_framework.views import APIView
from rest_framework import status
from twilio.rest import Client
from rest_framework.decorators import api_view
import os
from dotenv import load_dotenv

load_dotenv()


class CustomTokenView(TokenObtainPairView):
	serializer_class = CustomTokenSerializer

class RootViewSet(viewsets.ViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	permission_classes = [permissions.IsAuthenticated]

	def list(self, request):
		profile = get_user_profile(request.user)
		files = File.objects.filter(uploaded_by=profile)

		return Response({
			"files":FileSerializer(files, many=True, context={'request': request}).data,
		})

class ProfileViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	queryset = Profile.objects.all()
	serializer_class = ProfileSerializer
	permission_classes = permissions.IsAuthenticated,
	lookup_field = 'uuid'


	def get_queryset(self):
		user = self.request.user
		queryset = Profile.objects.all()
		if(user.is_superuser):
			return queryset
		try:
			pk = vars(self.request)["parser_context"]["kwargs"]["pk"]
			return queryset.filter(id=pk)
		except Exception:
			return None 

class AcademicYearViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	queryset = AcademicYear.objects.all()
	serializer_class = AcademicYearSerializer
	permission_classes = permissions.IsAuthenticated,

class DegreeViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	queryset = Degree.objects.all()
	serializer_class = DegreeSerializer
	permission_classes = permissions.IsAuthenticated,

class UniversityViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	queryset = University.objects.all()
	serializer_class = UniversitySerializer
	permission_classes = permissions.IsAuthenticated,

class AcademicDegreeViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	queryset = AcademicDegree.objects.all()
	serializer_class = AcademicDegreeSerializer
	permission_classes = permissions.IsAuthenticated,

class FacultyViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	queryset = Faculty.objects.all()
	serializer_class = FacultySerializer
	permission_classes = permissions.IsAuthenticated,
	filter_backends = [filters.DjangoFilterBackend, ]
	filterset_fields = {
		'name': ['icontains'],
		'university':['exact'],
	}

class DepartmentViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	queryset = Department.objects.all()
	serializer_class = DepartmentSerializer
	permission_classes = permissions.IsAuthenticated,
	filter_backends = [filters.DjangoFilterBackend, ]
	filterset_fields = {
		'name': ['icontains'],
		'faculty':['exact'],
	}

class CourseViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	queryset = Course.objects.all()
	serializer_class = CourseSerializer
	permission_classes = permissions.IsAuthenticated,
	filterset_fields = {
		'name': ['icontains'],
		'faculty':['exact'],
		'department':['exact'],
	}


class FileViewSet(viewsets.ModelViewSet):
	authentication_classes = SessionAuthentication, JWTAuthentication
	serializer_class = FileSerializer
	permission_classes = [permissions.IsAuthenticated]
	parser_classes = [MultiPartParser, FormParser]
	lookup_field = 'uuid'
	filterset_fields = {
		'title': ['icontains'],
		'description': ['icontains'],
		'file_type': ['icontains'],
		'file_category': ['icontains'],
		'course':['exact'],
	}

	def get_queryset(self):
		profile = get_user_profile(self.request.user)
		qs = File.objects.filter(uploaded_by=profile)
		return qs

	def perform_create(self, serializer):
		profile = get_user_profile(self.request.user)
		serializer.save(uploaded_by=profile)


class SendWhatsAppMessage(APIView):
    def post(self, request):
        # Récupérer les données envoyées par le client
        to_number = request.data.get("to")
        message_text = request.data.get("message")

        if not to_number or not message_text:
            return Response({"error": "Numéro et message requis"}, status=status.HTTP_400_BAD_REQUEST)

        try:

            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                from_="whatsapp:+14155238886",  # Numéro sandbox Twilio
                body=message_text,
                to=f"whatsapp:{to_number}"
            )

            return Response({"status": "Message envoyé", "sid": message.sid})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
		
# class SendWhatsAppMessage(APIView):
def sendMessage(to, msg):
        # Récupérer les données envoyées par le client
        to_number = to
        message_text = msg

        if not to_number or not message_text:
            return Response({"error": "Numéro et message requis"}, status=status.HTTP_400_BAD_REQUEST)

        try:

            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                from_="whatsapp:+14155238886",  # Numéro sandbox Twilio
                body=message_text,
                to=f"whatsapp:{to_number}"
            )

            return Response({"status": "Message envoyé", "sid": message.sid})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


		
@api_view(["POST"])
def receive_whatsapp_message(request):
    """
    Réception d'un message WhatsApp via Twilio Webhook
    """
    from_number = request.data.get("From")
    message_body = request.data.get("Body")
    to_number = request.data.get("To")
    msg = f"📩 Nouveau message de {from_number}: {message_body}"
    sendMessage(from_number,msg)
    # Tu peux sauvegarder le message dans ta base de données ici
    print(f"📩 Nouveau message de {from_number}: {message_body}")

    # Exemple de réponse automatique
    return Response({
        "status": "message reçu",
        "from": from_number,
        "to": to_number,
        "body": message_body
    })