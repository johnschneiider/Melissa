from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UsuarioPersonalizado, Feedback, RespuestaTicket
from django.db import models

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

class FeedbackForm(forms.ModelForm):
    categoria = forms.ChoiceField(
        choices=[
            ('', 'Selecciona una categoría'),
            ('bug', 'Bug/Error'),
            ('sugerencia', 'Sugerencia'),
            ('consulta', 'Consulta'),
            ('mejora', 'Solicitud de Mejora'),
            ('otro', 'Otro'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='sugerencia'
    )
    
    # Ocultamos el campo prioridad y lo dejamos por defecto en 'baja'
    prioridad = forms.CharField(
        widget=forms.HiddenInput(),
        initial='baja',
        required=False
    )
    
    titulo = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Título de la sugerencia (ej: Problemas con las reservas)'
        })
    )
    
    etiquetas = forms.ModelMultipleChoiceField(
        queryset=UsuarioPersonalizado.objects.filter(
            models.Q(is_superuser=True) | models.Q(tipo='super_admin')
        ),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Feedback
        fields = ['titulo', 'categoria', 'prioridad', 'mensaje', 'imagen', 'etiquetas']
        widgets = {
            'mensaje': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Escribe aquí tu problema o idea con palabras simples'
            }),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'placeholder': 'Sube una foto (opcional)'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['etiquetas'].queryset = UsuarioPersonalizado.objects.filter(
            models.Q(is_superuser=True) | models.Q(tipo='super_admin')
        )
        self.fields['etiquetas'].required = False

class RespuestaTicketForm(forms.ModelForm):
    """Formulario para responder a tickets"""
    
    class Meta:
        model = RespuestaTicket
        fields = ['mensaje']
        widgets = {
            'mensaje': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Escribe tu respuesta...'
            })
        }

class CambiarEstadoTicketForm(forms.Form):
    """Formulario para cambiar el estado de un ticket"""
    estado = forms.ChoiceField(
        choices=Feedback.ESTADO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    mensaje = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Mensaje opcional para el cambio de estado...'
        }),
        required=False
    )

class EditarPerfilClienteForm(forms.ModelForm):
    class Meta:
        model = UsuarioPersonalizado
        fields = [
            'username',
            'first_name', 'last_name', 'telefono', 'email', 'fecha_nacimiento', 'genero'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Teléfono'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'genero': forms.Select(attrs={'class': 'form-control'}),
        }
