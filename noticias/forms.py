from django import forms
from django.core.exceptions import ValidationError


class ComentarioForm(forms.Form):
    nome = forms.CharField(label="Nome", max_length=60)
    texto = forms.CharField(
        label="Comentário", max_length=1000, widget=forms.Textarea(attrs={"rows": 4})
    )

    def full_clean(self):
        super().full_clean()
        for campo in self.errors:
            if campo in self.fields:
                self.fields[campo].widget.attrs["aria-describedby"] = f"erro-{campo}"

    def clean_nome(self):
        nome = self.cleaned_data["nome"].strip()
        if not nome:
            raise ValidationError("Informe um nome.")
        return nome

    def clean_texto(self):
        texto = self.cleaned_data["texto"].strip()
        if not texto:
            raise ValidationError("Escreva o comentário.")
        return texto
