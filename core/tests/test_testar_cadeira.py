import importlib.util
import tomllib
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "testar_cadeira.py"


def _carregar():
    spec = importlib.util.spec_from_file_location("testar_cadeira", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


class TestarCadeiraTests(SimpleTestCase):
    def test_ordem_dos_quatro_passos_e_modulos(self):
        modulo = _carregar()
        with mock.patch(
            "subprocess.run", return_value=SimpleNamespace(returncode=0)
        ) as run:
            rc = modulo.main(["core.tests.test_a", "core.tests.test_b"])
        self.assertEqual(rc, 0)
        comandos = [c.args[0] for c in run.call_args_list]
        self.assertEqual(len(comandos), 4)
        self.assertEqual(comandos[0][1:], ["check", "."])
        self.assertEqual(comandos[1][1:], ["format", "--check", "."])
        self.assertIn("makemigrations", comandos[2])
        self.assertIn("--check", comandos[2])
        self.assertIn("test", comandos[3])
        self.assertIn("core.tests.test_a", comandos[3])
        self.assertIn("core.tests.test_b", comandos[3])

    def test_ruff_ignora_entregas_nao_rastreadas(self):
        config = tomllib.loads((SCRIPT.parents[1] / "pyproject.toml").read_text())
        self.assertIn("_entregas", config["tool"]["ruff"]["extend-exclude"])

    def test_passo_falhado_da_rc_e_nao_corta_os_seguintes(self):
        modulo = _carregar()
        rcs = iter([1, 0, 0, 0])
        with mock.patch(
            "subprocess.run",
            side_effect=lambda *a, **k: SimpleNamespace(returncode=next(rcs)),
        ) as run:
            rc = modulo.main([])
        self.assertNotEqual(rc, 0)
        self.assertEqual(run.call_count, 4)
