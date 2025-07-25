from django import forms
from django.utils import timezone
from datetime import datetime, time
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
        profesional = cleaned_data.get('profesional')
        servicio = cleaned_data.get('servicio')
        cliente = self.instance.cliente if self.instance and self.instance.pk else self.initial.get('cliente')
        if not cliente and hasattr(self, 'user'):
            cliente = self.user
        # Validación de solapamiento de reservas del cliente
        if fecha and hora_inicio and cliente:
            # Calcular hora_fin tentativa
            duracion = servicio.duracion if servicio else 30
            hora_inicio_dt = datetime.combine(fecha, hora_inicio)
            hora_fin_dt = hora_inicio_dt + timezone.timedelta(minutes=duracion)
            hora_fin = hora_fin_dt.time()
            reservas_cliente = Reserva.objects.filter(
                fecha=fecha,
                cliente=cliente,
                estado__in=['pendiente', 'confirmado']
            ).exclude(
                id=self.instance.id if self.instance and self.instance.pk else None
            )
            for reserva_existente in reservas_cliente:
                if (hora_inicio < reserva_existente.hora_fin and hora_fin > reserva_existente.hora_inicio):
                    raise forms.ValidationError(
                        f"Ya tienes una reserva para el {fecha.strftime('%d/%m/%Y')} entre las "
                        f"{reserva_existente.hora_inicio.strftime('%H:%M')} y {reserva_existente.hora_fin.strftime('%H:%M')}. "
                        f"No puedes reservar dos turnos solapados."
                    )
            
        if fecha and hora_inicio:
            # Hacer que la fecha/hora de reserva sea aware
            fecha_hora_reserva = timezone.make_aware(
                datetime.combine(fecha, hora_inicio))
            
            # Comparar con la hora actual (ya es aware)
            if fecha_hora_reserva < timezone.now():
                raise forms.ValidationError("No puedes reservar en fechas/horas pasadas.")
            
            # Validar solapamiento de reservas si hay profesional y servicio
            if profesional and servicio and fecha:
                # Calcular hora_fin basada en la duración del servicio
                duracion = servicio.duracion
                hora_inicio_dt = datetime.combine(fecha, hora_inicio)
                hora_fin_dt = hora_inicio_dt + timezone.timedelta(minutes=duracion)
                hora_fin = hora_fin_dt.time()
                
                # Buscar reservas existentes que se solapen
                reservas_solapadas = Reserva.objects.filter(
                    fecha=fecha,
                    profesional=profesional,
                    estado__in=['pendiente', 'confirmado']
                ).exclude(
                    # Excluir la reserva actual si estamos editando
                    id=self.instance.id if self.instance and self.instance.pk else None
                )
                
                for reserva_existente in reservas_solapadas:
                    # Verificar si hay solapamiento
                    # Solapamiento ocurre cuando:
                    # - La hora de inicio de la nueva reserva < hora fin de la existente Y
                    # - La hora fin de la nueva reserva > hora inicio de la existente
                    if (hora_inicio < reserva_existente.hora_fin and 
                        hora_fin > reserva_existente.hora_inicio):
                        raise forms.ValidationError(
                            f"Ya existe una reserva para {profesional.nombre_completo} "
                            f"el {fecha.strftime('%d/%m/%Y')} entre las "
                            f"{reserva_existente.hora_inicio.strftime('%H:%M')} y "
                            f"{reserva_existente.hora_fin.strftime('%H:%M')}. "
                            f"Por favor, selecciona otro horario."
                        )
                
        # Validación de máximo 2 reservas activas por cliente, por día y servicio
        if fecha and servicio and cliente:
            reservas_activas = Reserva.objects.filter(
                fecha=fecha,
                cliente=cliente,
                servicio=servicio,
                estado__in=['pendiente', 'confirmado']
            ).exclude(
                id=self.instance.id if self.instance and self.instance.pk else None
            ).count()
            if reservas_activas >= 2:
                raise forms.ValidationError(
                    f"No puedes tener más de 2 reservas activas para el mismo servicio el {fecha.strftime('%d/%m/%Y')}."
                )
                
        # Validar que la reserva esté dentro del horario laboral del profesional
        if fecha and hora_inicio and profesional:
            dia_semana = fecha.strftime('%A').lower()
            if dia_semana == 'wednesday': dia_semana = 'miercoles'
            elif dia_semana == 'saturday': dia_semana = 'sabado'
            elif dia_semana == 'sunday': dia_semana = 'domingo'
            horario = profesional.horarios.filter(dia_semana=dia_semana, disponible=True).first()
            if not horario:
                print(f"ADVERTENCIA: Profesional {profesional.nombre_completo} no tiene horario configurado para {dia_semana}")
            elif not (horario.hora_inicio <= hora_inicio < horario.hora_fin):
                raise forms.ValidationError(
                    f"El profesional no trabaja el {dia_semana.capitalize()} o fuera de su horario laboral ({horario.hora_inicio if horario else '--:--'} - {horario.hora_fin if horario else '--:--'})."
                )
                
        # Validar que la fecha de la reserva no caiga en una ausencia activa del profesional
        if fecha and profesional:
            from profesionales.models import AusenciaProfesional
            if AusenciaProfesional.objects.filter(profesional=profesional, activo=True, fecha_inicio__lte=fecha, fecha_fin__gte=fecha).exists():
                raise forms.ValidationError(
                    f"El profesional tiene una ausencia o vacaciones en la fecha seleccionada. Por favor, elige otro día.")
                
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
        self.negocio = negocio

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        profesional = cleaned_data.get('profesional')
        servicio = cleaned_data.get('servicio')
        cliente = self.initial.get('cliente')
        if not cliente and hasattr(self, 'user'):
            cliente = self.user
        # Validación de solapamiento de reservas del cliente
        if fecha and hora_inicio and cliente:
            duracion = servicio.duracion if servicio else 30
            hora_inicio_dt = datetime.combine(fecha, hora_inicio)
            hora_fin_dt = hora_inicio_dt + timezone.timedelta(minutes=duracion)
            hora_fin = hora_fin_dt.time()
            reservas_cliente = Reserva.objects.filter(
                fecha=fecha,
                cliente=cliente,
                estado__in=['pendiente', 'confirmado']
            ).exclude(
                id=self.instance.id if self.instance and self.instance.pk else None
            )
            for reserva_existente in reservas_cliente:
                if (hora_inicio < reserva_existente.hora_fin and hora_fin > reserva_existente.hora_inicio):
                    raise forms.ValidationError(
                        f"Ya tienes una reserva para el {fecha.strftime('%d/%m/%Y')} entre las "
                        f"{reserva_existente.hora_inicio.strftime('%H:%M')} y {reserva_existente.hora_fin.strftime('%H:%M')}. "
                        f"No puedes reservar dos turnos solapados."
                    )
                
        if fecha and hora_inicio and profesional and servicio:
            # Calcular hora_fin basada en la duración del servicio
            duracion = servicio.duracion
            hora_inicio_dt = datetime.combine(fecha, hora_inicio)
            hora_fin_dt = hora_inicio_dt + timezone.timedelta(minutes=duracion)
            hora_fin = hora_fin_dt.time()
            
            # Buscar reservas existentes que se solapen
            reservas_solapadas = Reserva.objects.filter(
                fecha=fecha,
                profesional=profesional,
                estado__in=['pendiente', 'confirmado']
            ).exclude(
                # Excluir la reserva actual si estamos editando
                id=self.instance.id if self.instance and self.instance.pk else None
            )
            
            for reserva_existente in reservas_solapadas:
                # Verificar si hay solapamiento
                if (hora_inicio < reserva_existente.hora_fin and 
                    hora_fin > reserva_existente.hora_inicio):
                    raise forms.ValidationError(
                        f"Ya existe una reserva para {profesional.nombre_completo} "
                        f"el {fecha.strftime('%d/%m/%Y')} entre las "
                        f"{reserva_existente.hora_inicio.strftime('%H:%M')} y "
                        f"{reserva_existente.hora_fin.strftime('%H:%M')}. "
                        f"Por favor, selecciona otro horario."
                    )
                
        # Validación de máximo 2 reservas activas por cliente, por día y servicio
        if fecha and servicio and cliente:
            reservas_activas = Reserva.objects.filter(
                fecha=fecha,
                cliente=cliente,
                servicio=servicio,
                estado__in=['pendiente', 'confirmado']
            ).exclude(
                id=self.instance.id if self.instance and self.instance.pk else None
            ).count()
            if reservas_activas >= 2:
                raise forms.ValidationError(
                    f"No puedes tener más de 2 reservas activas para el mismo servicio el {fecha.strftime('%d/%m/%Y')}."
                )
                
        # Validar que la reserva esté dentro del horario laboral del profesional
        if fecha and hora_inicio and profesional:
            dia_semana = fecha.strftime('%A').lower()
            if dia_semana == 'wednesday': dia_semana = 'miercoles'
            elif dia_semana == 'saturday': dia_semana = 'sabado'
            elif dia_semana == 'sunday': dia_semana = 'domingo'
            horario = profesional.horarios.filter(dia_semana=dia_semana, disponible=True).first()
            if not horario or not (horario.hora_inicio <= hora_inicio < horario.hora_fin):
                raise forms.ValidationError(
                    f"El profesional no trabaja el {dia_semana.capitalize()} o fuera de su horario laboral ({horario.hora_inicio if horario else '--:--'} - {horario.hora_fin if horario else '--:--'})."
                )
                
        # Validar que la fecha de la reserva no caiga en una ausencia activa del profesional
        if fecha and profesional:
            from profesionales.models import AusenciaProfesional
            if AusenciaProfesional.objects.filter(profesional=profesional, activo=True, fecha_inicio__lte=fecha, fecha_fin__gte=fecha).exists():
                raise forms.ValidationError(
                    f"El profesional tiene una ausencia o vacaciones en la fecha seleccionada. Por favor, elige otro día.")
                
        return cleaned_data

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