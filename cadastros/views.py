import os
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.views.decorators.http import require_POST

from cadastros.models import OfertaCarona, ReservaCarona, Usuario


# ----------------------------------------------------------------------
# CADASTRO DE USUARIO
# ----------------------------------------------------------------------
def cadastro_usuario(request):
    if request.method == 'POST':
        acao = request.POST.get('btnAcao')

        if acao == "Novo_Usuario":
            nome = request.POST.get('txtNome')
            email = request.POST.get('txtEmail')
            senha = request.POST.get('txtSenha')
            telefone = request.POST.get('txtTelefone')
            confirmar_senha = request.POST.get('confirmar_senha')

            if Usuario.objects.filter(email=email).exists():
                messages.error(request, 'Usuário já cadastrado com esse Email!')
                return redirect('cadastros:cadastro_usuario')

            if senha != confirmar_senha:
                messages.error(request, 'As senhas não coincidem!')
                return redirect('cadastros:cadastro_usuario')

            if len(senha or '') < 6:
                messages.error(request, 'A senha deve ter pelo menos 6 caracteres!')
                return redirect('cadastros:cadastro_usuario')

            usuario = Usuario(nome=nome, telefone=telefone, email=email, is_active=True, is_admin=False)
            usuario.set_password(senha)
            try:
                usuario.save()
                messages.success(request, 'Usuário cadastrado com sucesso!')
                return redirect('autenticacao:login')
            except Exception as e:
                messages.error(request, f'Ocorreu um erro ao salvar o usuário: {str(e)}')

    return render(request, 'cadastro_usuario.html')


# ----------------------------------------------------------------------
# OFERTAS DE CARONA
# ----------------------------------------------------------------------
def _converte_valor(texto):
    """Converte 'R$ 1.234,50' ou '25.50' em Decimal. Levanta InvalidOperation se inválido."""
    texto = (texto or '').replace('R$', '').strip()
    if ',' in texto:
        texto = texto.replace('.', '').replace(',', '.')
    valor = Decimal(texto)
    if valor < 0:
        raise InvalidOperation
    return valor


@login_required
def oferta_carona(request):
    if request.method == 'POST' and request.POST.get('btnAcao') == "oferecer_carona":
        origem = (request.POST.get('txtOrigem') or '').strip()
        destino = (request.POST.get('txtDestino') or '').strip()
        descricao = request.POST.get('txtDescricao')

        try:
            data_hora = parse_datetime(request.POST.get('txtData_hora') or '')
        except ValueError:
            data_hora = None
        if data_hora is None:
            messages.error(request, 'Data e hora inválidas!')
            return redirect('cadastros:oferta_carona')
        if timezone.is_naive(data_hora):
            data_hora = timezone.make_aware(data_hora)
        if data_hora <= timezone.now():
            messages.error(request, 'A data e hora da carona devem estar no futuro!')
            return redirect('cadastros:oferta_carona')

        try:
            vagas = int(request.POST.get('txtVagas'))
            if vagas < 1:
                raise ValueError
        except (TypeError, ValueError):
            messages.error(request, 'Informe um número de vagas válido (mínimo 1)!')
            return redirect('cadastros:oferta_carona')

        try:
            valor = _converte_valor(request.POST.get('txtValor'))
        except InvalidOperation:
            messages.error(request, 'Valor da vaga inválido!')
            return redirect('cadastros:oferta_carona')

        OfertaCarona.objects.create(
            motorista=request.user,
            origem=origem,
            destino=destino,
            data_hora=data_hora,
            vagas_ofertadas=vagas,
            valor=valor,
            descricao=descricao,
            status='aberta',
        )

        messages.success(request, 'Oferta de Carona cadastrada com sucesso!')
        return redirect('cadastros:minhas_ofertas')

    return render(request, 'oferta_carona.html')


@login_required
def listar_caronas(request):
    ofertas = (OfertaCarona.objects
               .filter(status='aberta', data_hora__gte=timezone.now())
               .exclude(motorista=request.user)
               .select_related('motorista')
               .order_by('data_hora'))

    origem = request.GET.get('origem', '').strip()
    destino = request.GET.get('destino', '').strip()
    data = request.GET.get('data', '').strip()
    passageiros = request.GET.get('passageiros', '').strip()

    if origem:
        ofertas = ofertas.filter(origem__icontains=origem)
    if destino:
        ofertas = ofertas.filter(destino__icontains=destino)
    if data:
        try:
            data_obj = parse_date(data)
        except ValueError:
            data_obj = None
        if data_obj:
            ofertas = ofertas.filter(data_hora__date=data_obj)

    ofertas = list(ofertas)
    if passageiros.isdigit() and int(passageiros) > 0:
        ofertas = [o for o in ofertas if o.vagas_disponiveis() >= int(passageiros)]

    return render(request, 'lista_ofertas.html', {
        'ofertas': ofertas,
        'filtros': {'origem': origem, 'destino': destino, 'data': data, 'passageiros': passageiros},
    })


@login_required
def minhas_ofertas(request):
    ofertas = (OfertaCarona.objects.filter(motorista=request.user)
               .prefetch_related('reservas__passageiro')
               .order_by('-data_hora'))
    return render(request, 'minhas_ofertas.html', {'ofertas': ofertas})


@login_required
@require_POST
def cancelar_oferta(request, oferta_id):
    oferta = get_object_or_404(OfertaCarona, id=oferta_id, motorista=request.user)
    if oferta.status != 'aberta':
        messages.error(request, 'Esta oferta não está mais aberta.')
        return redirect('cadastros:minhas_ofertas')

    with transaction.atomic():
        oferta.status = 'cancelada'
        oferta.save()
        oferta.reservas.filter(status__in=['pendente', 'confirmada']).update(status='cancelada')

    messages.success(request, 'Oferta cancelada. As reservas dela também foram canceladas.')
    return redirect('cadastros:minhas_ofertas')


# ----------------------------------------------------------------------
# RESERVAS
# ----------------------------------------------------------------------
@login_required
def reservar_carona(request, oferta_id):
    oferta = get_object_or_404(OfertaCarona.objects.select_related('motorista'), id=oferta_id)

    if oferta.motorista_id == request.user.id:
        messages.error(request, 'Você não pode reservar uma carona que você mesmo oferece.')
        return redirect('cadastros:listar_caronas')

    if oferta.status != 'aberta' or oferta.data_hora <= timezone.now():
        messages.error(request, 'Esta carona não está mais disponível.')
        return redirect('cadastros:listar_caronas')

    if request.method == 'POST':
        with transaction.atomic():
            # trava a oferta para duas pessoas não pegarem a última vaga ao mesmo tempo
            oferta = OfertaCarona.objects.select_for_update().get(id=oferta_id)

            if oferta.vagas_disponiveis() <= 0:
                messages.error(request, 'Não há mais vagas disponíveis nesta carona.')
                return redirect('cadastros:listar_caronas')

            reserva, criada = ReservaCarona.objects.get_or_create(
                oferta=oferta, passageiro=request.user, defaults={'status': 'pendente'}
            )
            if not criada:
                if reserva.status in ('pendente', 'confirmada'):
                    messages.warning(request, 'Você já possui uma reserva nesta carona.')
                    return redirect('cadastros:minhas_reservas')
                reserva.status = 'pendente'  # reativa uma reserva que havia sido cancelada
                reserva.save()

        messages.success(request, 'Reserva realizada! Aguarde a confirmação do motorista.')
        return redirect('cadastros:minhas_reservas')

    return render(request, 'reserva_carona.html', {'oferta': oferta})


@login_required
def minhas_reservas(request):
    reservas = (ReservaCarona.objects.filter(passageiro=request.user)
                .select_related('oferta', 'oferta__motorista')
                .order_by('-data_reserva'))
    return render(request, 'minhas_reservas.html', {'reservas': reservas})


@login_required
@require_POST
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(ReservaCarona, id=reserva_id, passageiro=request.user)
    if reserva.status in ('pendente', 'confirmada'):
        reserva.status = 'cancelada'
        reserva.save()
        messages.success(request, 'Reserva cancelada.')
    else:
        messages.error(request, 'Esta reserva já estava cancelada.')
    return redirect('cadastros:minhas_reservas')


@login_required
@require_POST
def responder_reserva(request, reserva_id):
    """O motorista confirma ou recusa uma reserva pendente da sua oferta."""
    reserva = get_object_or_404(ReservaCarona, id=reserva_id, oferta__motorista=request.user)
    acao = request.POST.get('acao')

    if reserva.status != 'pendente':
        messages.error(request, 'Só é possível responder reservas pendentes.')
    elif acao == 'confirmar':
        reserva.status = 'confirmada'
        reserva.save()
        messages.success(request, f'Reserva de {reserva.passageiro.nome} confirmada.')
    elif acao == 'recusar':
        reserva.status = 'cancelada'
        reserva.save()
        messages.success(request, f'Reserva de {reserva.passageiro.nome} recusada.')
    else:
        messages.error(request, 'Ação inválida.')
    return redirect('cadastros:minhas_ofertas')


# ----------------------------------------------------------------------
# PERFIL
# ----------------------------------------------------------------------
@login_required
def perfil_usuario(request):
    return render(request, 'perfil_usuario.html')


@login_required
def editar_perfil(request):
    return render(request, 'editar_perfil.html')


@login_required
def editar_usuario(request):
    usuario = request.user

    if request.method == 'POST':
        nome = request.POST.get('txtNome')
        email = request.POST.get('txtEmail')
        telefone = request.POST.get('txtTelefone')
        senha_confirmacao = request.POST.get('txtSenha')
        confirmacao = request.POST.get('confirmar_senha')
        foto = request.FILES.get('foto')

        if authenticate(request, username=usuario.email, password=senha_confirmacao) is None:
            messages.error(request, 'Senha incorreta! As alterações não foram salvas.')
            return redirect('cadastros:editar_perfil')

        if senha_confirmacao != confirmacao:
            messages.error(request, 'Senhas diferentes!')
            return redirect('cadastros:editar_perfil')

        if Usuario.objects.filter(email=email).exclude(id=usuario.id).exists():
            messages.error(request, 'Este e-mail já está em uso por outro usuário!')
            return redirect('cadastros:editar_perfil')

        usuario.nome = nome
        usuario.email = email
        usuario.telefone = telefone

        if foto:
            extensao = os.path.splitext(foto.name)[1].lower() or '.jpg'
            foto.name = f"{email}{extensao}"
            if usuario.foto:
                usuario.foto.delete(save=False)  # remove a foto antiga
            usuario.foto = foto

        try:
            usuario.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('cadastros:perfil_usuario')
        except Exception as e:
            messages.error(request, f'Ocorreu um erro ao atualizar o perfil: {str(e)}')

    return render(request, 'editar_perfil.html', {'user': usuario})


@login_required
def editar_senha(request):
    return render(request, 'editar_senha.html')


@login_required
def mudar_senha(request):
    usuario = request.user

    if request.method == 'POST':
        nova_senha = request.POST.get('txtNovaSenha')
        senha_atual = request.POST.get('txtSenha')
        confirmar_senha = request.POST.get('confirmar_senha')

        if not usuario.check_password(senha_atual):
            messages.error(request, 'Senha atual incorreta! As alterações não foram salvas.')
            return redirect('cadastros:editar_senha')

        # (o teste estava invertido: dava erro justamente quando as senhas eram iguais)
        if nova_senha != confirmar_senha:
            messages.error(request, 'As novas senhas não são iguais!')
            return redirect('cadastros:editar_senha')

        if len(nova_senha or '') < 6:
            messages.error(request, 'A nova senha é muito curta!')
            return redirect('cadastros:editar_senha')

        usuario.set_password(nova_senha)
        try:
            usuario.save()
            update_session_auth_hash(request, usuario)  # mantém o usuário logado
            messages.success(request, 'Senha atualizada com sucesso!')
            return redirect('cadastros:perfil_usuario')
        except Exception as e:
            messages.error(request, f'Ocorreu um erro ao atualizar a senha: {str(e)}')

    return render(request, 'editar_senha.html', {'user': usuario})


@login_required
def excluir_conta(request):
    return render(request, 'excluir_conta.html')


@login_required
def apagar_conta(request):
    usuario = request.user

    if request.method == 'POST':
        senha = request.POST.get('txtSenha')
        confirmar_senha = request.POST.get('confirmar_senha')

        if authenticate(request, username=usuario.email, password=confirmar_senha) is None:
            messages.error(request, 'Senha incorreta! A conta não foi excluída.')
            return redirect('cadastros:excluir_conta')

        if senha != confirmar_senha:
            messages.error(request, 'Senhas diferentes! A conta não foi excluída.')
            return redirect('cadastros:excluir_conta')

        try:
            usuario.delete()
        except ProtectedError:
            messages.error(request, 'Não é possível excluir a conta: você possui caronas ou reservas vinculadas.')
            return redirect('cadastros:excluir_conta')
        except Exception as e:
            messages.error(request, f'Ocorreu um erro ao excluir a conta: {str(e)}')
            return redirect('cadastros:excluir_conta')

        logout(request)
        messages.success(request, 'Conta excluída com sucesso!')
        return redirect('autenticacao:login')

    return render(request, 'excluir_conta.html', {'user': usuario})
