from django import forms


class ComentarioForm(forms.Form):
    nome = forms.CharField(
        label="Nome", max_length=60, error_messages={"required": "Informe um nome."}
    )
    texto = forms.CharField(
        label="Comentário",
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 4}),
        error_messages={"required": "Escreva o comentário."},
    )

    def full_clean(self):
        super().full_clean()
        for campo in self.errors:
            if campo in self.fields:
                self.fields[campo].widget.attrs["aria-describedby"] = f"erro-{campo}"
                self.fields[campo].widget.attrs["aria-invalid"] = "true"
