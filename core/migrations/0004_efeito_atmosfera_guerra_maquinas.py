from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_efeito_atmosfera_maquina_fria'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ato',
            name='efeito',
            field=models.CharField(choices=[('parallax:camadas', 'Parallax em camadas'), ('scroll:revela', 'Revela ao rolar'), ('three:gira', 'Cena 3D que gira'), ('rive:estado', 'Rive com estado'), ('diagrama:constroi', 'Diagrama que se constrói'), ('terminal:fala', 'Terminal que fala'), ('three:corredor', 'Corredor 3D'), ('olho:segue', 'Olho que segue o cursor'), ('atmosfera:maquina-fria', 'Atmosfera «Máquina fria»'), ('atmosfera:guerra-maquinas', 'Atmosfera «Guerra das máquinas»')], max_length=30, verbose_name='efeito'),
        ),
    ]
