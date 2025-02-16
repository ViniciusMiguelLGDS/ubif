from django.core.management.base import BaseCommand
from django.db import connection, transaction
from cadastros.models import Usuario

class Command(BaseCommand):
    help = 'Redefine o banco de dados do app carona e cria um usuário administrador.'

    @transaction.atomic
    def handle(self, *args, **options):
        cursor = connection.cursor()
        app_labels = ['cadastros']
        tables = [table for table in connection.introspection.table_names() if any(app in table for app in app_labels)]

        # Desabilita constraints de chave estrangeira (PostgreSQL)
        if connection.vendor == 'postgresql':
            for table in tables:
                cursor.execute(f'ALTER TABLE "{table}" DISABLE TRIGGER ALL;')

        # Apaga os dados
        for table in tables:
            cursor.execute(f'TRUNCATE TABLE "{table}" CASCADE;')

        # Reseta sequência de IDs (PostgreSQL)
        if connection.vendor == 'postgresql':
            for table in tables:
                cursor.execute(f"""
                    DO $$ 
                    BEGIN 
                        IF EXISTS (
                            SELECT 1 FROM information_schema.columns
                            WHERE table_name='{table}' AND column_name='id'
                        ) THEN
                            PERFORM setval(pg_get_serial_sequence('"{table}"', 'id'), 1, false);
                        END IF;
                    END $$;
                """)

        # Reabilita constraints de chave estrangeira
        if connection.vendor == 'postgresql':
            for table in tables:
                cursor.execute(f'ALTER TABLE "{table}" ENABLE TRIGGER ALL;')

        # Criação do usuário administrador
        if not Usuario.objects.filter(email='juanamorimlp@gmail.com').exists():
            usuario = Usuario.objects.create_superuser(
                email='juanamorimlp@gmail.com',
                nome='Administrador',
                password='123456'
            )
            self.stdout.write(self.style.SUCCESS('Usuário administrador criado com sucesso!'))
        else:
            self.stdout.write(self.style.WARNING('Usuário administrador já existe.'))

        self.stdout.write(self.style.SUCCESS('Banco de dados redefinido com sucesso!'))
