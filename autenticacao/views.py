from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import JsonResponse
from django.urls import reverse_lazy
from cadastros.models import Usuario
from django.contrib.auth.views import PasswordResetView

def login(request):
    if request.method == 'POST':
        email = request.POST.get('txtEmail')
        senha = request.POST.get('txtSenha')

        try:
            usuario = Usuario.objects.get(email=email)  # Busca usuário pelo email
            usuario_autenticado = authenticate(request, username=usuario.email, password=senha)  
            
            if usuario_autenticado is not None:
                #limpa as sessoes do usuario
                request.session.flush()
                auth_login(request, usuario_autenticado)  # Faz login do usuário
                
                request.session['id_atual'] = usuario.id
                request.session['email_atual'] = usuario.email
                request.session['telefone'] = usuario.telefone
                #configura sessao para expirar em 4 horas
                request.session.set_expiry(14400)
                messages.success(request, 'Login realizado com sucesso.')
                return redirect('core:main')  # Redireciona para onde quiser
            else:
                messages.error(request, 'E-mail ou senha inválidos.')
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuário não encontrado.')

    return render(request, 'login.html')

def logout(request):
    #limpa a sessao ao deslogar
    request.session.flush()
    auth_logout(request)
    
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('autenticacao:login')

class MyPasswordReset(PasswordResetView):
    template_name = 'password_reset_form.html'
    email_template_name = 'password_reset_email.html'
    subject_template_name = 'password_reset_subject.txt'
    success_url = reverse_lazy('autenticacao:password_reset_done')

class MyPasswordResetDone(PasswordResetView):
    template_name = 'password_reset_done.html'
    

def verificar_usuario(request):
    email = request.GET.get('email', '').strip()
        
    if Usuario.objects.filter(email=email).exists():
        return JsonResponse({'usuario_existe': True})
    else:
        return JsonResponse({'usuario_existe': False})