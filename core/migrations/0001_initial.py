import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PostImersivo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("slug", models.SlugField(unique=True, verbose_name="slug")),
                ("titulo", models.CharField(max_length=200, verbose_name="título")),
                ("publicado", models.BooleanField(default=False, verbose_name="publicado")),
            ],
            options={
                "verbose_name": "post imersivo",
                "verbose_name_plural": "posts imersivos",
                "ordering": ["titulo"],
            },
        ),
        migrations.CreateModel(
            name="Ato",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ordem", models.PositiveIntegerField(default=0, verbose_name="ordem")),
                ("titulo", models.CharField(max_length=200, verbose_name="título")),
                ("texto", models.TextField(verbose_name="texto")),
                (
                    "efeito",
                    models.CharField(
                        choices=[
                            ("parallax:camadas", "Parallax em camadas"),
                            ("scroll:revela", "Revela ao rolar"),
                            ("three:gira", "Cena 3D que gira"),
                            ("rive:estado", "Rive com estado"),
                            ("diagrama:constroi", "Diagrama que se constrói"),
                        ],
                        max_length=30,
                        verbose_name="efeito",
                    ),
                ),
                (
                    "parametros",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="Objeto JSON; as chaves aceitas dependem do efeito.",
                        verbose_name="parâmetros",
                    ),
                ),
                (
                    "reduzido",
                    models.CharField(
                        choices=[("estatico", "Estático"), ("omitir", "Omitir")],
                        default="estatico",
                        max_length=10,
                        verbose_name="com movimento reduzido",
                    ),
                ),
                (
                    "post",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="atos",
                        to="core.postimersivo",
                        verbose_name="post",
                    ),
                ),
            ],
            options={
                "verbose_name": "ato",
                "verbose_name_plural": "atos",
                "ordering": ["post", "ordem", "pk"],
            },
        ),
    ]
