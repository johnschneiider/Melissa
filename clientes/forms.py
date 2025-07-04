from django import forms
from django.utils import timezone
from datetime import datetime
from .models import Reserva, Calificacion
from negocios.models import Servicio, ServicioNegocio
from profesionales.models import Profesional

class ReservaForm(forms.ModelForm):
    servicio = forms.ModelChoiceField(
        queryset=Servicio.objects.none(),
        required=False,
        label="Servicio (opcional)"
    )
    profesional = forms.ModelChoiceField(
        queryset=Profesional.objects.none(),
        required=False,
        label="Profesional (opcional)"
    )
    
    class Meta:
        model = Reserva
        fields = ['fecha', 'hora_inicio', 'servicio', 'profesional', 'notas']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, negocio=None, **kwargs):
        super().__init__(*args, **kwargs)
        if negocio:
            from negocios.models import ServicioNegocio
            self.fields['servicio'].queryset = ServicioNegocio.objects.filter(negocio=negocio)
            from profesionales.models import Matriculacion
            profesionales = Profesional.objects.filter(matriculaciones__negocio=negocio, matriculaciones__estado='aprobada').distinct()
            self.fields['profesional'].queryset = profesionales

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        
        if fecha and hora_inicio:
            # Hacer que la fecha/hora de reserva sea aware
            fecha_hora_reserva = timezone.make_aware(
                datetime.combine(fecha, hora_inicio))
            
            # Comparar con la hora actual (ya es aware)
            if fecha_hora_reserva < timezone.now():
                raise forms.ValidationError("No puedes reservar en fechas/horas pasadas.")
                
        return cleaned_data

class ReservaNegocioForm(forms.ModelForm):
    servicio = forms.ModelChoiceField(queryset=ServicioNegocio.objects.none(), required=True, label="Servicio",
        widget=forms.Select(attrs={'class': 'form-select'}))
    profesional = forms.ModelChoiceField(queryset=Profesional.objects.none(), required=True, label="Profesional",
        widget=forms.Select(attrs={'class': 'form-select'}))
    class Meta:
        model = Reserva
        fields = ['servicio', 'profesional', 'fecha', 'hora_inicio', 'notas']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'readonly': 'readonly'}),
            'notas': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    def __init__(self, *args, negocio=None, profesional_preseleccionado=None, **kwargs):
        super().__init__(*args, **kwargs)
        if negocio:
            from profesionales.models import Matriculacion, Profesional
            profesionales = Profesional.objects.filter(matriculaciones__negocio=negocio, matriculaciones__estado='aprobada').distinct()
            self.fields['profesional'].queryset = profesionales
            self.fields['servicio'].queryset = ServicioNegocio.objects.filter(negocio=negocio)
            self.fields['servicio'].label_from_instance = lambda obj: f"{obj.servicio.nombre} ({obj.duracion} min)"
            # Si hay un profesional preseleccionado, filtrar servicios por los asignados a ese profesional
            if profesional_preseleccionado:
                servicios_ids = profesional_preseleccionado.servicios.values_list('id', flat=True)
                self.fields['servicio'].queryset = ServicioNegocio.objects.filter(negocio=negocio, servicio__id__in=servicios_ids)
                self.fields['profesional'].initial = profesional_preseleccionado.id

class CalificacionForm(forms.ModelForm):
    """Formulario para crear calificaciones con estrellas"""
    
    class Meta:
        model = Calificacion
        fields = ['puntaje', 'comentario']
        widgets = {
            'puntaje': forms.HiddenInput(),  # Se manejará con JavaScript
            'comentario': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Comparte tu experiencia con este negocio y profesional...'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['puntaje'].initial = 5