from django.conf import settings
from django.db import models


class UsoDiario(models.Model):
    """Quanto um utilizador já gastou, num dia, de cada tipo de uso com tecto."""

    CONVERSA = "conversa"
    COMENTARIO = "comentario"
    TIPOS = [(CONVERSA, "Conversa"), (COMENTARIO, "Comentário")]

    utilizador = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="usos_diarios"
    )
    dia = models.DateField()
    tipo = models.CharField(max_length=20, choices=TIPOS)
    quantidade = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("utilizador", "dia", "tipo")]

    def __str__(self):
        return f"{self.utilizador} {self.dia} {self.tipo}={self.quantidade}"
