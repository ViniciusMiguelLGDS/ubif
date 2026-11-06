from django.shortcuts import render
from django.utils import timezone
from cadastros.models import OfertaCarona


def main(request):
    ofertas = OfertaCarona.objects.filter(
        status='aberta', data_hora__gte=timezone.now()
    ).select_related('motorista').order_by('data_hora')
    if request.user.is_authenticated:
        ofertas = ofertas.exclude(motorista=request.user)

    return render(request, "main.html", {'exibir_busca': True, 'ofertas': ofertas[:6]})
