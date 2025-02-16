from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'cadastros'

urlpatterns = [
    path('cadastro_usuario/', views.cadastro_usuario, name='cadastro_usuario'),
    path('oferta_carona/', views.oferta_carona, name='oferta_carona'),
    path('listar_caronas/', views.listar_caronas, name='listar_caronas'),

    #PERFIL DO USUARIO
    path('perfil_usuario/', views.perfil_usuario, name='perfil_usuario'),

    #EDITAR PERFIL
    path('editar_perfil/', views.editar_perfil, name='editar_perfil'),
    path('editar_usuario/', views.editar_usuario, name='editar_usuario'), #confirma a edição do perfil
    path('editar_senha/', views.editar_senha, name='editar_senha'),
    path('mudar_senha/', views.mudar_senha, name='mudar_senha'), #confirma edição de senha
]
