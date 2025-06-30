from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UsuarioPersonalizado

class RegistroUnificadoForm(UserCreationForm):
    TIPO_CHOICES = [
        ('cliente', 'Cliente - Quiero reservar servicios'),
        ('negocio', 'Negocio - Quiero ofrecer servicios'),
        ('profesional', 'Profesional - Soy peluquero y quiero trabajar en un negocio'),
    ]
    
    tipo = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=True,
        label="Tipo de cuenta",
        help_text="Selecciona el tipo de cuenta que deseas crear",
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    telefono = forms.CharField(
        max_length=15,
        required=True,
        label="Teléfono",
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Número de teléfono'
        })
    )

    class Meta:
        model = UsuarioPersonalizado
        fields = ['username', 'email', 'tipo', 'telefono', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(RegistroUnificadoForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nombre de usuario'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Correo electrónico'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Repite tu contraseña'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.tipo = self.cleaned_data['tipo']
        user.telefono = self.cleaned_data['telefono']
        if commit:
            user.save()
        return user


class NegocioRegistroForm(UserCreationForm):
    telefono = forms.CharField(
        max_length=15,
        required=True,
        label="Teléfono",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono de contacto del negocio'})
    )

    class Meta:
        model = UsuarioPersonalizado
        fields = ['username', 'email', 'telefono', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(NegocioRegistroForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nombre del negocio o usuario'
        })
        self.fields['email'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Correo electrónico del negocio'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Repite tu contraseña'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.tipo = 'negocio'
        user.telefono = self.cleaned_data['telefono']
        if commit:
            user.save()
        return user
