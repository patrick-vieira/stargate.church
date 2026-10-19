from django.apps import apps
from django.core.management import call_command
from django.db import models
from django.test import TestCase


class FixtureDemoTests(TestCase):
    """O SQLite não impõe max_length (o Postgres sim): a verificação é explícita."""

    def test_fixture_respeita_max_length(self):
        call_command("loaddata", "stargate_demo", verbosity=0)
        excedidos = []
        total = 0
        for modelo in apps.get_app_config("noticias").get_models():
            campos = [
                f
                for f in modelo._meta.concrete_fields
                if isinstance(f, models.CharField) and f.max_length
            ]
            for obj in modelo.objects.all():
                total += 1
                for campo in campos:
                    valor = getattr(obj, campo.attname)
                    if isinstance(valor, str) and len(valor) > campo.max_length:
                        excedidos.append(
                            f"{modelo.__name__}(pk={obj.pk}).{campo.name}: "
                            f"{len(valor)} > {campo.max_length}"
                        )
        self.assertGreater(total, 0, "a fixture não carregou objectos")
        self.assertEqual(excedidos, [])
