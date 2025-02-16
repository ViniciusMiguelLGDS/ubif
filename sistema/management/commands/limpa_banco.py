from django.core.management.base import BaseCommand
from django.db import connection, transaction
from cadastros.models import (
 Usuario
)

class Command(BaseCommand):
    help = 'Redefine o sistema, apagando tudo do banco'

    @transaction.atomic
    def handle(self, *args, **options):
        cursor = connection.cursor()
        # obtem apenas as tabelas do aplicativo 'cadastros'
        app_labels = ['cadastros']
        tables = [table for table in connection.introspection.table_names() if any(app in table for app in app_labels)]
        
        # desabilita as constraints de chave estrangeira para postgres
        if connection.vendor == 'postgresql':
            for table in tables:
                cursor.execute(f'ALTER TABLE "{table}" DISABLE TRIGGER ALL;')

        # apaga todos os dados das tabelas do aplicativo
        for table in tables:
            cursor.execute(f'TRUNCATE TABLE "{table}" CASCADE;')

        # reseta as sequencias de autoincremento
        if connection.vendor == 'postgresql':
            for table in tables:
                cursor.execute(f"""
                    SELECT setval(pg_get_serial_sequence('"{table}"', 'id'), 1, false)
                    WHERE EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='{table}' AND column_name='id'
                        AND column_default LIKE 'nextval%'
                    );
                """)

        # reabilita as constraints de chave estrangeira para postgres
        if connection.vendor == 'postgresql':
            for table in tables:
                cursor.execute(f'ALTER TABLE "{table}" ENABLE TRIGGER ALL;')

        self.stdout.write(self.style.SUCCESS('Banco de dados apagado com sucesso!'))