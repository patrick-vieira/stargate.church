from django.conf import settings
from django.test.runner import DiscoverRunner


class RaizDiscoverRunner(DiscoverRunner):
    """Sem rótulo, descobre os testes a partir da raiz do projecto (BASE_DIR),
    e não do directório de trabalho: o resultado deixa de depender do cwd."""

    def build_suite(self, test_labels=None, **kwargs):
        if not test_labels:
            test_labels = [str(settings.BASE_DIR)]
        return super().build_suite(test_labels, **kwargs)
