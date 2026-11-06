from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Inicializa o sistema com os dados padrão'

    def handle(self, *args, **options):
        User = get_user_model()
        email = 'juanamorimlp@gmail.com'

        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(email=email, nome='Administrador', password='123456')
            self.stdout.write(self.style.SUCCESS('Superusuário criado com sucesso!'))
        else:
            self.stdout.write(self.style.WARNING('Superusuário já existe. Nenhuma ação foi tomada.'))
