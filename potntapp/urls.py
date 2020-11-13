from django.urls import path
from . import views
from rest_framework_simplejwt import views as jwt_views


urlpatterns = [
    path('signup', views.signup, name='signup'),
    path('<str:tenant>/login', views.login, name='login'),
    path('<str:tenant>/roads', views.roads, name='roads'),
    path('<str:tenant>/roads/<uuid:uuidRoad>/potholes', views.roadPotholes, name='roadPotholes'),
    path('<str:tenant>/pothole', views.pothole, name='pothole'),
    path('<str:tenant>/pothole/<uuid:uuidPothole>', views.potholeWithUuid, name='potholeWithUuid'),
    path('<str:tenant>/pothole/<uuid:uuidPothole>/image', views.potholeImage, name='potholeImage')
]