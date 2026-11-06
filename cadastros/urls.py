from django.urls import path
from . import views

app_name = 'cadastros'

urlpatterns = [
    path('cadastro_usuario/', views.cadastro_usuario, name='cadastro_usuario'),

    # CARONAS
    path('oferta_carona/', views.oferta_carona, name='oferta_carona'),
    path('listar_caronas/', views.listar_caronas, name='listar_caronas'),
    path('minhas_ofertas/', views.minhas_ofertas, name='minhas_ofertas'),
    path('cancelar_oferta/<int:oferta_id>/', views.cancelar_oferta, name='cancelar_oferta'),

    # RESERVAS
    path('reservar_carona/<int:oferta_id>/', views.reservar_carona, name='reservar_carona'),
    path('minhas_reservas/', views.minhas_reservas, name='minhas_reservas'),
    path('cancelar_reserva/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
    path('responder_reserva/<int:reserva_id>/', views.responder_reserva, name='responder_reserva'),

    # PERFIL DO USUARIO
    path('perfil_usuario/', views.perfil_usuario, name='perfil_usuario'),

    # EDITAR PERFIL
    path('editar_perfil/', views.editar_perfil, name='editar_perfil'),
    path('editar_usuario/', views.editar_usuario, name='editar_usuario'),  # confirma a edição do perfil
    path('editar_senha/', views.editar_senha, name='editar_senha'),
    path('mudar_senha/', views.mudar_senha, name='mudar_senha'),  # confirma edição de senha
    path('excluir_conta/', views.excluir_conta, name='excluir_conta'),
    path('apagar_conta/', views.apagar_conta, name='apagar_conta'),  # confirma exclusão de conta
]
