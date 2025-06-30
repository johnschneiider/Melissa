from django import forms
from .models import Profesional
from negocios.models import Servicio

class ProfesionalPerfilForm(forms.ModelForm):
    portada = forms.ImageField(
        required=False,
        label="Portada",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )
    servicios = forms.ModelMultipleChoiceField(
        queryset=Servicio.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select'}),
        label='Servicios que ofrece',
        help_text='Selecciona uno o más servicios que ofreces.'
    )
    class Meta:
        model = Profesional
        fields = [
            'nombre_completo',
            'especialidad',
            'experiencia_anos',
            'descripcion',
            'foto_perfil',
            'portada',
            'certificaciones',
            'cv',
            'servicios',
        ]
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre completo'}),
            'especialidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Colorista, Barbería, etc.'}),
            'experiencia_anos': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'placeholder': 'Años de experiencia'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe tu experiencia, estilo, etc. (opcional)'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'certificaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Certificaciones, cursos, etc. (opcional)'}),
            'cv': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
        } 