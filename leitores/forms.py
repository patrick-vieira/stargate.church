from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class CriarContaForm(forms.Form):
    email = forms.EmailField(label="E-mail")
    senha = forms.CharField(label="Senha", widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if get_user_model().objects.filter(username__iexact=email).exists():
            raise ValidationError("Já existe uma conta com este e-mail.")
        return email

    def clean(self):
        dados = super().clean()
        senha, email = dados.get("senha"), dados.get("email")
        if senha:
            user = get_user_model()(username=email or "", email=email or "")
            try:
                validate_password(senha, user)
            except ValidationError as erro:
                self.add_error("senha", erro)
        return dados

    def guardar(self):
        email = self.cleaned_data["email"]
        return get_user_model().objects.create_user(
            username=email, email=email, password=self.cleaned_data["senha"]
        )


class EntrarForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "E-mail ou senha incorretos.",
        "inactive": "Esta conta está inativa.",
    }
