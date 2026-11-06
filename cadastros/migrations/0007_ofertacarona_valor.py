from django.db import migrations, models


def padroniza_status(apps, schema_editor):
    """Ofertas antigas foram salvas com status 'Aberta'; as choices usam minúsculo."""
    OfertaCarona = apps.get_model('cadastros', 'OfertaCarona')
    for antigo, novo in (('Aberta', 'aberta'), ('Encerrada', 'encerrada'), ('Cancelada', 'cancelada')):
        OfertaCarona.objects.filter(status=antigo).update(status=novo)


class Migration(migrations.Migration):

    dependencies = [
        ('cadastros', '0006_alter_usuario_is_admin'),
    ]

    operations = [
        migrations.AddField(
            model_name='ofertacarona',
            name='valor',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
        migrations.RunPython(padroniza_status, migrations.RunPython.noop),
    ]
