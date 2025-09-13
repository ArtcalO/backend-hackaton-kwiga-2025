from django.urls import path, include
from rest_framework import routers
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView

router = routers.DefaultRouter()

router.register(r'folders', FolderViewSet, basename='folders')
router.register(r'files', FileViewSet, basename='files')
router.register(r'shared', SharedFileViewSet, basename='shared')
router.register(r'galleries', GalleryViewSet)
router.register(r'shared-galleries', SharedGalleryViewSet)
router.register(r'root', RootViewSet,  basename='root')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', CustomTokenView.as_view()),
    path('refresh/', TokenRefreshView.as_view()),
    path('api-auth/', include('rest_framework.urls')),
]