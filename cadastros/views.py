from django.shortcuts import redirect, render
from django.contrib.auth import authenticate
from django.contrib import messages
from cadastros.models import OfertaCarona, Usuario
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.crypto import get_random_string
import os

def cadastro_usuario(request):
    if request.method == 'POST':
        acao = request.POST.get('btnAcao')
    
        if acao == "Novo_Usuario":
            nome = request.POST.get('txtNome')
            email = request.POST.get('txtEmail')
            senha = request.POST.get('txtSenha')
            telefone = request.POST.get('txtTelefone')
            
            # Verificando se o e-mail já está cadastrado
            if Usuario.objects.filter(email=email).exists():
                messages.error(request, 'Usuário já cadastrado com esse Email!')
                return redirect('cadastros:cadastro_usuario')
            
            confirmar_senha = request.POST.get('confirmar_senha')

            # Verificando se as senhas coincidem
            if senha != confirmar_senha:
                messages.error(request, 'As senhas não coincidem!')
                return redirect('cadastros:cadastro_usuario')

            # Criando uma nova instância do usuário com os campos obrigatórios
            usuario = Usuario(nome=nome, telefone=telefone, email=email, is_active=True, is_admin=False)
            
            # Salvando a senha de forma segura
            usuario.set_password(senha)
            try:
                usuario.save()
                messages.success(request, 'Usuário cadastrado com sucesso!')
                return redirect('autenticacao:login')
            except Exception as e:
                messages.error(request, f'Ocorreu um erro ao salvar o usuário: {str(e)}')
    
    return render(request, 'cadastro_usuario.html')

@login_required
def oferta_carona(request):
    if request.method == 'POST':
        acao = request.POST.get('btnAcao')
        if acao == "oferecer_carona":
            motorista = request.user  # Já temos o usuário autenticado, não precisa buscar de novo

            # Obtendo os dados do formulário
            origem = request.POST.get('txtOrigem')
            destino = request.POST.get('txtDestino')
            data = request.POST.get('txtData_hora')
            num_vagas = request.POST.get('txtVagas')
            descricao = request.POST.get('txtDescricao')

            # Criando a oferta de carona
            oferta = OfertaCarona(
                motorista=motorista,  # Agora corretamente associado ao usuário logado
                origem=origem,
                destino=destino,
                data_hora=data,
                vagas_ofertadas=num_vagas,
                descricao=descricao,
                status='Aberta'
            )
            oferta.save()

            messages.success(request, 'Oferta de Carona cadastrada com sucesso!')
            return redirect('core:main')  # Redirecionamento correto após o cadastro

    return render(request, 'oferta_carona.html')

def listar_caronas(request):
    ofertas = OfertaCarona.objects.filter(status='Aberta').exclude(motorista=request.user).order_by('data_hora')
    return render(request, 'lista_ofertas.html', {'ofertas': ofertas})

def home(request):
    return render(request, 'home.html')

#LOGIN
@login_required
def perfil_usuario(request):
    return render(request, 'perfil_usuario.html')

#EDITAR PERFIL
@login_required
def editar_perfil(request):
    return render(request, 'editar_perfil.html')

@login_required
def editar_usuario(request):
    usuario = request.user  # Obtém o usuário autenticado

    if request.method == 'POST':
        nome = request.POST.get('txtNome')
        email = request.POST.get('txtEmail')
        telefone = request.POST.get('txtTelefone')
        senha_confirmacao = request.POST.get('txtSenha')
        confirmacao = request.POST.get('confirmar_senha')
        foto = request.FILES.get('foto')  # Obtém a foto enviada no formulário

        # Verifica se a senha está correta
        usuario_autenticado = authenticate(request, username=usuario.email, password=senha_confirmacao)
        if usuario_autenticado is None:
            messages.error(request, 'Senha incorreta! As alterações não foram salvas.')
            return redirect('cadastros:editar_perfil')

        # Verifica se as senhas digitadas são iguais
        if senha_confirmacao != confirmacao:
            messages.error(request, 'Senhas diferentes!')
            return redirect('cadastros:editar_perfil')

        # Verifica se o e-mail já está cadastrado por outro usuário
        if Usuario.objects.filter(email=email).exclude(id=usuario.id).exists():
            messages.error(request, 'Este e-mail já está em uso por outro usuário!')
            return redirect('cadastros:editar_perfil')

        # Atualiza os dados do usuário autenticado
        usuario.nome = nome
        usuario.email = email
        usuario.telefone = telefone

        # Se uma nova foto foi enviada, renomeia com o e-mail do usuário
        if foto:
            # Renomeia o arquivo para o email do usuário
            foto.name = f"{usuario.email}.jpg"  # ou .png dependendo do formato da imagem
            if usuario.foto:  # Remove a foto antiga se já existir
                usuario.foto.delete(save=False)
            usuario.foto = foto  # Atualiza a foto

        try:
            usuario.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('cadastros:perfil_usuario')  # Redireciona para o perfil atualizado
        except Exception as e:
            messages.error(request, f'Ocorreu um erro ao atualizar o perfil: {str(e)}')

    return render(request, 'editar_perfil.html', {'user': usuario})

#EDITAR SENHA
@login_required
def editar_senha(request):
    return render(request, 'editar_senha.html')

@login_required
def mudar_senha(request):
    usuario = request.user

    if request.method == 'POST':
        nova_senha = request.POST.get('txtNovaSenha')
        senha_atual = request.POST.get('txtSenha')  # Renomeei para deixar mais claro
        confirmar_senha = request.POST.get('confirmar_senha')

        # Verifica se a senha atual está correta
        if not usuario.check_password(senha_atual):
            messages.error(request, 'Senha atual incorreta! As alterações não foram salvas.')
            return redirect('cadastros:editar_senha')
        
        # Verifica se as senhas são iguais
        if nova_senha == confirmar_senha:
            messages.error(request, 'As novas senhas não iguais!')
            return redirect('cadastros:editar_senha')
        
        if len(nova_senha) < 6:
            messages.error(request, 'A nova senha é muito curta!')
            return redirect('cadastros:editar_senha')
        
        # Altera a senha de forma segura
        usuario.set_password(nova_senha)

        try:
            usuario.save()
            messages.success(request, 'Senha atualizada com sucesso!')
            
            # Reautentica o usuário para evitar logout
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, usuario)

            return redirect('cadastros:perfil_usuario')  # Redireciona para o perfil atualizado
        except Exception as e:
            messages.error(request, f'Ocorreu um erro ao atualizar a senha: {str(e)}')

    return render(request, 'editar_senha.html', {'user': usuario})