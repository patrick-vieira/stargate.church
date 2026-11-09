# STAR-47: efeito atmosfera:quase-presente (sobre a 0012 do STAR-63)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_alter_ato_efeito_hub'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ato',
            name='efeito',
            field=models.CharField(choices=[('parallax:camadas', 'Parallax em camadas'), ('scroll:revela', 'Revela ao rolar'), ('three:gira', 'Cena 3D que gira'), ('rive:estado', 'Rive com estado'), ('diagrama:constroi', 'Diagrama que se constrói'), ('linha-tempo:decadas', 'Linha do tempo por décadas'), ('filtro:chips', 'Filtro por chips (perguntas)'), ('grelha:posts', 'Grelha dos posts da série'), ('terminal:fala', 'Terminal que fala'), ('three:corredor', 'Corredor 3D'), ('olho:segue', 'Olho que segue o cursor'), ('atmosfera:maquina-fria', 'Atmosfera «Máquina fria»'), ('atmosfera:guerra-maquinas', 'Atmosfera «Guerra das máquinas»'), ('atmosfera:ser-humano', 'Atmosfera «O que é ser humano?»'), ('atmosfera:escolhas', 'Atmosfera «Escolhas da máquina»'), ('atmosfera:ia-afetiva', 'Atmosfera «IA afetiva»'), ('atmosfera:leis-robos-livros', 'Atmosfera «Leis, robôs e livros»'), ('atmosfera:quase-presente', 'Atmosfera «O quase-presente»')], max_length=30, verbose_name='efeito'),
        ),
    ]
