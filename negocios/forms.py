from django import forms
from .models import Negocio, Peluquero, ImagenGaleria
from django.core.exceptions import ValidationError
import imghdr

class ImagenGaleriaForm(forms.ModelForm):
    class Meta:
        model = ImagenGaleria
        fields = ['nombre', 'descripcion', 'duracion', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'duracion': forms.NumberInput(attrs={'class': 'form-control', 'min': 5}),
            'imagen': forms.FileInput(attrs={'class': 'form-control'})
        }



class NegocioForm(forms.ModelForm):
    class Meta:
        model = Negocio
        fields = ['nombre', 'direccion', 'logo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class PeluqueroForm(forms.ModelForm):
    class Meta:
        model = Peluquero
        fields = ['nombre', 'avatar', 'portada', 'horario', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'horario': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            if imghdr.what(avatar) == 'avif':
                raise ValidationError("El formato AVIF no está permitido.")
        return avatar

    def clean_portada(self):
        portada = self.cleaned_data.get('portada')
        if portada:
            if imghdr.what(portada) == 'avif':
                raise ValidationError("El formato AVIF no está permitido.")
        return portada