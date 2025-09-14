from django.urls import path, include
from rest_framework import routers
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

router = routers.DefaultRouter()

router.register(r'files', FileViewSet, basename='files')
router.register(r'academic-years', AcademicYearViewSet, basename='academic-years')
router.register(r'degrees', DegreeViewSet, basename='degrees')
router.register(r'universities', UniversityViewSet, basename='universities')
router.register(r'academic-degrees', AcademicDegreeViewSet, basename='academic-degrees')
router.register(r'faculties', FacultyViewSet, basename='faculties')
router.register(r'departments', DepartmentViewSet, basename='departments')
router.register(r'courses', CourseViewSet, basename='courses')
router.register(r'root', RootViewSet,  basename='root')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', CustomTokenView.as_view()),
    path('refresh/', TokenRefreshView.as_view()),
    path('api-auth/', include('rest_framework.urls')),
    path('send', SendWhatsAppMessage.as_view()),
    path('webhook', receive_whatsapp_message),
]