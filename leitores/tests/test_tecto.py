import datetime
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.test import RequestFactory, TestCase, override_settings

from leitores import tecto
from leitores.models import UsoDiario

User = get_user_model()


@override_settings(STARGATE_TECTO_CONVERSA=3, STARGATE_TECTO_COMENTARIO=2)
class TectoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("a@b.com", "a@b.com", "uma-senha-forte-91")

    def test_chega_ao_limite_e_recusa(self):
        self.assertEqual(tecto.restante(self.user, "conversa"), 3)
        res = [tecto.consumir(self.user, "conversa") for _ in range(4)]
        self.assertEqual(res, [True] * 3 + [False])
        self.assertEqual(tecto.restante(self.user, "conversa"), 0)
        self.assertEqual(UsoDiario.objects.get().quantidade, 3)

    def test_tipos_sao_independentes(self):
        for _ in range(3):
            tecto.consumir(self.user, "conversa")
        self.assertTrue(tecto.consumir(self.user, "comentario"))
        self.assertEqual(tecto.restante(self.user, "comentario"), 1)

    def test_dia_seguinte_zera(self):
        for _ in range(3):
            tecto.consumir(self.user, "conversa")
        self.assertFalse(tecto.consumir(self.user, "conversa"))
        amanha = tecto._hoje() + datetime.timedelta(days=1)
        with mock.patch.object(tecto, "_hoje", return_value=amanha):
            self.assertEqual(tecto.restante(self.user, "conversa"), 3)
            self.assertTrue(tecto.consumir(self.user, "conversa"))

    def test_anonimo_nunca_consome(self):
        self.assertFalse(tecto.consumir(AnonymousUser(), "conversa"))
        self.assertEqual(tecto.restante(AnonymousUser(), "conversa"), 0)
        self.assertFalse(UsoDiario.objects.exists())

    def test_tipo_desconhecido(self):
        with self.assertRaises(ValueError):
            tecto.consumir(self.user, "x")

    @override_settings(STARGATE_TECTO_CONVERSA=20)
    def test_defaults_vem_das_settings(self):
        self.assertEqual(tecto.limite("conversa"), 20)


@override_settings(STARGATE_TECTO_CONVERSA=1)
class DecoradorTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

        @tecto.exige_tecto("conversa")
        def view(request):
            return JsonResponse({"ok": True})

        self.view = view

    def _pedido(self, user):
        r = self.rf.post("/x/")
        r.user = user
        return self.view(r)

    def test_anonimo_recusado(self):
        self.assertEqual(self._pedido(AnonymousUser()).status_code, 401)

    def test_deixa_passar_ate_ao_tecto_e_depois_429(self):
        user = User.objects.create_user("a@b.com", "a@b.com", "uma-senha-forte-91")
        self.assertEqual(self._pedido(user).status_code, 200)
        self.assertEqual(self._pedido(user).status_code, 429)
