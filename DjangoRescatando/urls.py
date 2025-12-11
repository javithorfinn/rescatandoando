"""
URL configuration for DjangoRescatando project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from mainApp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register_usuario/', views.register_usuario, name='register_usuario'),
    path('ayudar/', views.ayudar, name='ayudar'),
    
    # Recuperación de contraseña
    path('recuperar-contrasena/', views.recuperar_contrasena, name='recuperar_contrasena'),
    path('resetear-contrasena/<str:token>/', views.resetear_contrasena, name='resetear_contrasena'),
    
    # Perfil de usuario
    path('perfil/', views.perfil, name='perfil'),
    path('mis_adopciones/', views.mis_adopciones, name='mis_adopciones'),
    
    # Gestión de animales (admin/voluntario)
    path('agregar_animal/', views.agregar_animal, name='agregar_animal'),
    path('gestionar_animales/', views.gestionar_animales, name='gestionar_animales'),
    path('api/ficha/<int:id_animal>/', views.obtener_ficha_medica, name='obtener_ficha_medica'),
    
    # Adopciones (público y admin/voluntario)
    path('solicitar_adopcion/<int:animal_id>/', views.solicitar_adopcion, name='solicitar_adopcion'),
    path('lista_adopciones/', views.lista_adopciones, name='lista_adopciones'),
    path('ver_solicitudes/', views.ver_solicitudes, name='ver_solicitudes'),
    path('registrar_entrevista/<int:adopcion_id>/', views.registrar_entrevista, name='registrar_entrevista'),
    
    # Donaciones (público)
    path('donacion/', views.realizar_donacion, name='realizar_donacion'),
    path('ver_comprobantes/', views.ver_comprobantes, name='ver_comprobantes'),
    
    # Voluntarios (público)
    path('inscripcion_voluntario/', views.inscripcion_voluntario, name='inscripcion_voluntario'),
    path('solicitar_voluntariado/', views.solicitar_voluntariado, name='solicitar_voluntariado'),
    
    # Gestión de usuarios (solo admin)
    path('gestionar_usuarios/', views.gestionar_usuarios_view, name='gestionar_usuarios'),
    path('cambiar_rol/<int:usuario_id>/', views.cambiar_rol_usuario, name='cambiar_rol_usuario'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)