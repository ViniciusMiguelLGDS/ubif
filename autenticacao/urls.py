from django.urls import path, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views
app_name = 'autenticacao'

urlpatterns = [
    path('', views.login, name='login'),
    path("verificar_usuario/", views.verificar_usuario, name="verificar_usuario"),
    path("logout/", views.logout, name="logout"),
    path('password_reset/', views.MyPasswordReset.as_view(),name='password_reset'),
    path('password_reset/done/', views.MyPasswordResetDone.as_view(),name='password_reset_done'),
    path(
        'reset/<uidb64>/<token>/', 
        auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html',
        success_url=reverse_lazy('autenticacao:password_reset_complete')
        ),
        name='password_reset_confirm'),
    path('reset/complete/',auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'),name='password_reset_complete'),
]
