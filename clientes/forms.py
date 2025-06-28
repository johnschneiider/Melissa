from django import forms
from django.utils import timezone
from datetime import datetime
from .models import Reserva
from negocios.models import ImagenGaleria

class ReservaForm(forms.ModelForm):
    servicio = forms.ModelChoiceField(
        queryset=ImagenGaleria.objects.none(),
        required=False,
        label="Servicio (opcional)"
    )
    
    class Meta:
        model = Reserva
        fields = ['fecha', 'hora_inicio', 'servicio', 'notas']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'notas': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, peluquero=None, **kwargs):
        super().__init__(*args, **kwargs)
        if peluquero:
            self.fields['servicio'].queryset = ImagenGaleria.objects.filter(
                peluquero=peluquero
            ).order_by('nombre')
            
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