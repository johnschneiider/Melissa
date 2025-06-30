from django import forms
from django.utils import timezone
from datetime import datetime
from .models import Reserva
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
            self.fields['servicio'].queryset = ServicioNegocio.objects.filter(negocio=negocio)
            self.fields['servicio'].label_from_instance = lambda obj: f"{obj.servicio.nombre} ({obj.duracion} min)"
            from profesionales.models import Matriculacion
            profesionales = Profesional.objects.filter(matriculaciones__negocio=negocio, matriculaciones__estado='aprobada').distinct()
            self.fields['profesional'].queryset = profesionales
        if profesional_preseleccionado:
            self.fields['profesional'].initial = profesional_preseleccionado.id