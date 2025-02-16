from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

# Função para inicializar o sistema com os dados padrão
class Command(BaseCommand):
    help = 'Inicializa o sistema com os dados padrão'

    def handle(self, *args, **options):
        # Obtém o modelo de usuário personalizado
        User = get_user_model()

        # Verifica se o superusuário já existe
        if not User.objects.filter(email='juanamorimlp@gmail.com').exists():
            # Cria o superusuário, incluindo o 'username' (por exemplo, usando o e-mail)
            usuario = User.objects.create_superuser(
                email='juanamorimlp@gmail.com',
                username='juanamorimlp',  # Adicionando o 'username' explicitamente
                password='123456',  # Defina a senha do superusuário
            )
            # Atribui o campo 'nome' após a criação
            usuario.nome = 'Administrador'
            usuario.save()

            self.stdout.write(self.style.SUCCESS('Superusuário criado com sucesso!'))
        else:
            self.stdout.write(self.style.WARNING('Superusuário já existe. Nenhuma ação foi tomada.'))
