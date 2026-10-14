"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from api.views import CustomTokenObtainPairView

urlpatterns = [
    path('maintenance/admin/', admin.site.urls),
    path('maintenance/api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair_prod'),
    path('maintenance/api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh_prod'),
    path('maintenance/api/', include('api.urls')),
    
    # Local dev paths
    path('admin/', admin.site.urls),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('api.urls')),
]
