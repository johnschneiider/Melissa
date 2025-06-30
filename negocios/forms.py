from django import forms
from .models import Negocio, ImagenNegocio, Servicio
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
import imghdr
import os

class NegocioForm(forms.ModelForm):
    logo = forms.ImageField(
        required=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'],
                message='Solo se permiten archivos de imagen (jpg, jpeg, png, gif, webp).'
            )
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    portada = forms.ImageField(
        required=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'],
                message='Solo se permiten archivos de imagen (jpg, jpeg, png, gif, webp).'
            )
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    # Campos adicionales que no están en el modelo pero se usan en el template
    telefono = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: +54 11 1234-5678',
            'pattern': '[0-9+\-\s\(\)]+'
        })
    )
    
    ciudad = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Buenos Aires'
        })
    )
    
    descripcion = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Describe tu negocio...'
        })
    )
    
    servicios = forms.ModelMultipleChoiceField(
        queryset=Servicio.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label='Servicios que ofrece el negocio',
        help_text='Selecciona uno o más servicios. Puedes crear nuevos servicios abajo.'
    )
    nuevo_servicio = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Agregar nuevo servicio...'}),
        label='Nuevo servicio'
    )
    
    class Meta:
        model = Negocio
        fields = ['nombre', 'direccion', 'logo', 'portada', 'servicios']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '100',
                'pattern': '[A-Za-z0-9áéíóúÁÉÍÓÚñÑ\s\-\.]+'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'maxlength': '500'
            }),
        }

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            # Verificar tamaño del archivo (2MB máximo para logos)
            if logo.size > 2 * 1024 * 1024:
                raise ValidationError("El logo es demasiado grande. Tamaño máximo: 2MB.")
            
            # Verificar tipo de archivo
            allowed_types = ['jpeg', 'jpg', 'png', 'gif', 'webp']
            file_type = imghdr.what(logo)
            if file_type not in allowed_types:
                raise ValidationError("Tipo de archivo no permitido.")
        
        return logo

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            nombre = nombre.strip()
            if len(nombre) < 2:
                raise ValidationError("El nombre del negocio debe tener al menos 2 caracteres.")
            if len(nombre) > 100:
                raise ValidationError("El nombre del negocio no puede exceder 100 caracteres.")
        return nombre

class ImagenNegocioForm(forms.ModelForm):
    imagen = forms.ImageField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'],
                message='Solo se permiten archivos de imagen (jpg, jpeg, png, gif, webp).'
            )
        ],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    class Meta:
        model = ImagenNegocio
        fields = ['imagen', 'titulo', 'descripcion']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': '100',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'maxlength': '500',
            }),
        }