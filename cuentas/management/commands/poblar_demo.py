from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from negocios.models import Negocio, Servicio, ServicioNegocio, ImagenNegocio
from profesionales.models import Profesional, Matriculacion, HorarioProfesional
from clientes.models import Reserva, Calificacion
from datetime import date, time, timedelta
import os
from django.conf import settings
from django.core.files import File
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Pobla la base de datos con datos de ejemplo para demo/pruebas'

    def handle(self, *args, **options):
        # Superadmin
        if not User.objects.filter(username='superadmin').exists():
            superadmin = User.objects.create_superuser(username='superadmin', email='super@demo.com', password='Malware01', tipo='super_admin')
            self.stdout.write(self.style.SUCCESS('Superadmin creado'))

        # Servicios base
        servicios_base = [
            'Corte de cabello',
            'Coloración',
            'Peinado',
            'Manicura',
            'Pedicura',
            'Depilación',
            'Barbería',
            'Tratamiento capilar',
            'Maquillaje',
        ]
        
        servicios = []
        for nombre in servicios_base:
            serv, _ = Servicio.objects.get_or_create(nombre=nombre)
            servicios.append(serv)
        self.stdout.write(self.style.SUCCESS(f'{len(servicios)} servicios base creados'))

        # Nombres reales para negocios
        nombres_negocios = [
            'Salón de Belleza "Glamour"',
            'Peluquería "Estilo & Moda"',
            'Beauty Studio "Elegance"',
            'Hair Salon "Trendy"',
            'Salón "Belleza Natural"',
            'Peluquería "Modern Style"',
            'Beauty Center "Divine"',
            'Salón "Chic & Fashion"',
            'Peluquería "Elite Beauty"',
            'Beauty Studio "Premium"'
        ]

        # Negocios y usuarios tipo negocio
        negocios = []
        for i in range(1, 11):
            neg_user, created = User.objects.get_or_create(username=f'negocio{i}', defaults={
                'email': f'negocio{i}@demo.com', 'tipo': 'negocio'})
            if created:
                neg_user.set_password('Malware01')
                neg_user.save()
            
            nombre_negocio = nombres_negocios[i-1]
            direcciones = [
                'Av. Corrientes 1234, Buenos Aires',
                'Calle Florida 567, CABA',
                'Av. Santa Fe 890, Palermo',
                'Calle Serrano 456, Villa Crespo',
                'Av. Córdoba 789, Recoleta',
                'Calle Thames 321, Palermo Soho',
                'Av. Scalabrini Ortiz 654, Palermo',
                'Calle Armenia 987, Palermo Hollywood',
                'Av. Dorrego 147, Villa Crespo',
                'Calle Fitz Roy 258, Palermo'
            ]
            
            negocio, _ = Negocio.objects.get_or_create(nombre=nombre_negocio, propietario=neg_user, defaults={
                'direccion': direcciones[i-1],
                'ciudad': 'Buenos Aires',
                'barrio': ['Palermo', 'Villa Crespo', 'Recoleta', 'CABA'][i % 4],
                'latitud': -34.6037 + (i * 0.01),
                'longitud': -58.3816 + (i * 0.01),
            })
            
            # Asignar logo y portada si no existen
            if not negocio.logo:
                logo_path = os.path.join(settings.BASE_DIR, 'logos_negocios', '25231.png')
                if os.path.exists(logo_path):
                    with open(logo_path, 'rb') as f:
                        negocio.logo.save(f'logo_negocio_{i}.png', File(f), save=False)
            
            if not negocio.portada:
                portada_path = os.path.join(settings.BASE_DIR, 'portadas_peluqueros', 'Imagenhjj-1.png')
                if os.path.exists(portada_path):
                    with open(portada_path, 'rb') as f:
                        negocio.portada.save(f'portada_negocio_{i}.png', File(f), save=False)
            
            negocio.save()
            negocios.append(negocio)
            
            # Asignar servicios al negocio con precios realistas
            precios_servicios = {
                'Corte de cabello': (80, 120),
                'Coloración': (150, 300),
                'Peinado': (100, 180),
                'Manicura': (60, 100),
                'Pedicura': (80, 120),
                'Depilación': (50, 150),
                'Barbería': (90, 140),
                'Tratamiento capilar': (120, 250),
                'Maquillaje': (100, 200),
            }
            
            for servicio in servicios:
                precio_min, precio_max = precios_servicios.get(servicio.nombre, (50, 150))
                precio = random.randint(precio_min, precio_max)
                duracion = random.randint(30, 90)
                ServicioNegocio.objects.get_or_create(
                    negocio=negocio, 
                    servicio=servicio, 
                    defaults={
                        'precio': precio,
                        'duracion': duracion,
                        'activo': True
                    }
                )
            
            # Crear imágenes de galería para el negocio
            for k in range(1, 4):  # 3 imágenes por negocio
                ImagenNegocio.objects.get_or_create(
                    negocio=negocio,
                    titulo=f'Galería {k} - {negocio.nombre}',
                    descripcion=f'Imagen profesional del salón {negocio.nombre}',
                    defaults={
                        'imagen': negocio.logo  # Usar el logo como imagen de galería por ahora
                    }
                )
        
        self.stdout.write(self.style.SUCCESS('10 negocios creados con logos, portadas y servicios'))

        # Nombres reales para profesionales
        nombres_profesionales = [
            'María González', 'Carlos Rodríguez', 'Ana Martínez', 'Luis Fernández',
            'Carmen López', 'Javier Pérez', 'Isabel García', 'Miguel Torres',
            'Elena Ruiz', 'Diego Morales', 'Sofia Herrera', 'Roberto Jiménez',
            'Valentina Silva', 'Andrés Castro', 'Camila Vargas', 'Fernando Rojas',
            'Daniela Mendoza', 'Ricardo Ortega', 'Natalia Guzmán', 'Héctor Salazar',
            'Gabriela Vega', 'Oscar Mendoza', 'Lucía Paredes', 'Manuel Ríos',
            'Adriana Cortés', 'Felipe Navarro', 'Carolina Soto', 'Eduardo Bravo',
            'Patricia Valenzuela', 'Raúl Espinoza', 'Monica Fuentes', 'Alberto Reyes',
            'Verónica Molina', 'Cristian Herrera', 'Diana Ponce', 'Gustavo Cárdenas',
            'Rosa Miranda', 'José Valdez', 'Teresa Sandoval', 'Mario Acosta',
            'Claudia Rivas', 'Francisco Campos', 'Elena Figueroa', 'Roberto Guzmán',
            'Silvia Carrillo', 'Alfonso Méndez', 'Graciela Luna', 'Humberto Delgado',
            'Norma Escobar', 'Rogelio Valencia', 'Blanca Cisneros', 'Federico Rangel',
            'Lourdes Villanueva', 'Arturo Zamora', 'Consuelo Aguirre', 'René Mejía',
            'Estela Barrios', 'César Galván', 'Alicia Cervantes', 'Mauro Montoya',
            'Dolores Salas', 'Ernesto Ávila', 'Beatriz Zúñiga', 'Rolando Ibarra',
            'Margarita Solís', 'Fabián Juárez', 'Rosario Ochoa', 'Damián Lara',
            'Amparo Maldonado', 'Gerardo Robles', 'Concepción Zavala', 'Nicolás Bernal',
            'Esperanza Medrano', 'Baltazar Rosales', 'Clementina Cuevas', 'Teodoro Lozano',
            'Prudencia de la Cruz', 'Cipriano Vázquez', 'Modesta Rocha', 'Fortunato Trejo',
            'Eulalia Tovar', 'Benjamín Peña', 'Justina Ríos', 'Clemente Luna',
            'Digna Espinosa', 'Evaristo Coronel', 'Honorata Valdez', 'Fermín Rangel',
            'Veneranda Bustos', 'Crisóstomo Cárdenas', 'Eusebia Galván', 'Feliciano Rocha',
            'Modesta Tovar', 'Cipriano Luna', 'Prudencia Espinosa', 'Teodoro Coronel',
            'Clementina Valdez', 'Fortunato Rangel', 'Esperanza Bustos', 'Baltazar Cárdenas',
            'Concepción Galván', 'Gerardo Rocha', 'Amparo Tovar', 'Damián Luna',
            'Dolores Espinosa', 'César Coronel', 'Beatriz Valdez', 'Mauro Rangel',
            'Estela Bustos', 'Ernesto Cárdenas', 'Alicia Galván', 'Rolando Rocha'
        ]

        # Profesionales y usuarios tipo profesional
        profesionales = []
        especialidades = [
            'Cortes y peinados',
            'Coloración y mechas',
            'Tratamientos capilares',
            'Manicura y pedicura',
            'Barbería',
            'Maquillaje',
            'Depilación',
            'Estilismo',
            'Técnicas avanzadas',
            'Cuidado del cabello'
        ]
        
        for i in range(1, 101):
            user_prof, created = User.objects.get_or_create(username=f'profesional{i}', defaults={
                'email': f'profesional{i}@demo.com', 'tipo': 'profesional'})
            if created:
                user_prof.set_password('Malware01')
                user_prof.save()
            
            nombre_completo = nombres_profesionales[i-1] if i <= len(nombres_profesionales) else f'Profesional {i}'
            especialidad = especialidades[i % len(especialidades)]
            experiencia = random.randint(2, 15)  # 2-15 años de experiencia
            
            descripciones = [
                f'Especialista en {especialidad} con {experiencia} años de experiencia. Apasionada por crear looks únicos y modernos.',
                f'Profesional dedicado a {especialidad} con {experiencia} años en el rubro. Comprometido con la excelencia y la satisfacción del cliente.',
                f'Experta en {especialidad} con {experiencia} años de trayectoria. Especializada en técnicas innovadoras y tendencias actuales.',
                f'Profesional de {especialidad} con {experiencia} años de experiencia. Enfoque en resultados naturales y duraderos.',
                f'Especialista en {especialidad} con {experiencia} años en la industria. Dedicada a transformar y realzar la belleza natural.'
            ]
            
            prof, _ = Profesional.objects.get_or_create(usuario=user_prof, defaults={
                'nombre_completo': nombre_completo,
                'especialidad': especialidad,
                'experiencia_anos': experiencia,
                'descripcion': random.choice(descripciones),
                'disponible': True
            })
            
            # Asignar foto de perfil y portada si no existen
            if not prof.foto_perfil:
                foto_path = os.path.join(settings.BASE_DIR, 'peluqueros', '25231.png')
                if os.path.exists(foto_path):
                    with open(foto_path, 'rb') as f:
                        prof.foto_perfil.save(f'foto_profesional_{i}.png', File(f), save=False)
            
            if not prof.portada:
                portada_path = os.path.join(settings.BASE_DIR, 'portadas_peluqueros', 'Imagenhjj-1.png')
                if os.path.exists(portada_path):
                    with open(portada_path, 'rb') as f:
                        prof.portada.save(f'portada_profesional_{i}.png', File(f), save=False)
            
            prof.save()
            profesionales.append(prof)
            
            # Asignar servicios al profesional (3-5 servicios por profesional)
            servicios_profesional = servicios[i % len(servicios):(i % len(servicios)) + 3 + (i % 3)]
            if len(servicios_profesional) > len(servicios):
                servicios_profesional = servicios[:3 + (i % 3)]
            
            for servicio in servicios_profesional:
                prof.servicios.add(servicio)
        
        self.stdout.write(self.style.SUCCESS('100 profesionales creados con fotos, portadas y servicios'))

        # Distribuir profesionales entre negocios de manera más realista
        # Cada negocio tendrá entre 3-8 profesionales
        profesionales_por_negocio = {}
        for i, negocio in enumerate(negocios):
            num_profesionales = random.randint(3, 8)
            start_idx = i * 10  # Distribuir 10 profesionales por negocio
            end_idx = start_idx + num_profesionales
            profesionales_por_negocio[negocio] = profesionales[start_idx:end_idx]
        
        # Matriculación de profesionales en negocios
        for negocio, profs_negocio in profesionales_por_negocio.items():
            for i, prof in enumerate(profs_negocio):
                # Simular solicitud y aprobación
                matricula, _ = Matriculacion.objects.get_or_create(profesional=prof, negocio=negocio, defaults={
                    'estado': 'pendiente',
                    'mensaje_solicitud': f'Me interesa formar parte del equipo de {negocio.nombre}. Tengo experiencia en {prof.especialidad}.',
                    'salario_propuesto': 1500 + (i * 100),
                    'horario_propuesto': 'Lunes a Viernes, 8:00 - 17:00'
                })
                matricula.estado = 'aprobada'
                matricula.save()
                
                # Crear horarios realistas para cada día de la semana
                horarios_semana = {
                    'lunes': (time(9, 0), time(18, 0)),
                    'martes': (time(9, 0), time(18, 0)),
                    'miercoles': (time(9, 0), time(18, 0)),
                    'jueves': (time(9, 0), time(18, 0)),
                    'viernes': (time(9, 0), time(18, 0)),
                    'sabado': (time(9, 0), time(16, 0)),
                    'domingo': (time(10, 0), time(15, 0))
                }
                
                for dia, (hora_inicio, hora_fin) in horarios_semana.items():
                    # Algunos profesionales no trabajan domingo
                    if dia == 'domingo' and random.random() < 0.7:
                        disponible = False
                        hora_inicio = time(0, 0)
                        hora_fin = time(0, 0)
                    else:
                        disponible = True
                    
                    HorarioProfesional.objects.get_or_create(
                        profesional=prof,
                        dia_semana=dia,
                        defaults={
                            'hora_inicio': hora_inicio,
                            'hora_fin': hora_fin,
                            'disponible': disponible
                        }
                    )
        
        self.stdout.write(self.style.SUCCESS('Profesionales matriculados y aprobados en negocios'))

        # Crear clientes ficticios con nombres reales
        nombres_clientes = [
            'Laura Sánchez', 'Pedro Ramírez', 'Ana Torres', 'Carlos Morales',
            'María Jiménez', 'Juan Herrera', 'Sofia Castro', 'Diego Rojas',
            'Valentina Mendoza', 'Andrés Ortega', 'Camila Guzmán', 'Fernando Salazar',
            'Daniela Vega', 'Ricardo Mendoza', 'Natalia Paredes', 'Héctor Ríos',
            'Gabriela Cortés', 'Oscar Navarro', 'Lucía Soto', 'Manuel Bravo'
        ]
        
        clientes = []
        for i in range(1, 21):  # 20 clientes para más calificaciones
            nombre_cliente = nombres_clientes[i-1] if i <= len(nombres_clientes) else f'Cliente {i}'
            cli, created = User.objects.get_or_create(username=f'cliente{i}', defaults={
                'email': f'cliente{i}@demo.com', 'tipo': 'cliente',
                'first_name': nombre_cliente.split()[0],
                'last_name': nombre_cliente.split()[1] if len(nombre_cliente.split()) > 1 else ''
            })
            if created:
                cli.set_password('Malware01')
                cli.save()
            clientes.append(cli)
        self.stdout.write(self.style.SUCCESS('20 clientes creados'))

        # Reservas demo con estados variados
        estados_reserva = ['pendiente', 'confirmado', 'completado', 'cancelado']
        for i, cli in enumerate(clientes):
            # Seleccionar negocio y profesional de manera más realista
            negocio = negocios[i % len(negocios)]
            profs_negocio = profesionales_por_negocio.get(negocio, [])
            if profs_negocio:
                prof = random.choice(profs_negocio)
                servicio_negocio = ServicioNegocio.objects.filter(negocio=negocio).first()
                
                if servicio_negocio:
                    estado = random.choice(estados_reserva)
                    fecha_reserva = date.today() + timedelta(days=random.randint(-30, 30))
                    
                    Reserva.objects.get_or_create(
                        cliente=cli,
                        peluquero=negocio,
                        profesional=prof,
                        fecha=fecha_reserva,
                        hora_inicio=time(10 + random.randint(0, 6), 0),
                        hora_fin=time(10 + random.randint(0, 6), 30),
                        servicio=servicio_negocio,
                        estado=estado,
                        notas=f'Reserva de {cli.first_name} para {servicio_negocio.servicio.nombre}'
                    )
        self.stdout.write(self.style.SUCCESS('Reservas de ejemplo creadas'))

        # Crear calificaciones realistas para cada negocio
        comentarios_positivos = [
            'Excelente servicio, muy profesional y puntual. Definitivamente volveré.',
            'Muy satisfecha con el resultado. El profesional es muy talentoso.',
            'Increíble atención y calidad de trabajo. Altamente recomendado.',
            'Servicio de primera calidad. El salón está impecable.',
            'Muy profesional y amable. El resultado superó mis expectativas.',
            'Excelente trabajo, muy detallista y cuidadoso con el cabello.',
            'Muy buena experiencia, el profesional es muy experto en su área.',
            'Servicio excepcional, ambiente agradable y resultados perfectos.',
            'Muy recomendable, el profesional tiene mucha experiencia.',
            'Excelente atención al cliente y resultados de alta calidad.'
        ]
        
        comentarios_neutros = [
            'Buen servicio en general, podría mejorar en puntualidad.',
            'Servicio aceptable, el resultado fue bueno.',
            'Correcto, el profesional es competente.',
            'Buen trabajo, aunque podría ser más detallista.',
            'Servicio adecuado, cumple con lo esperado.'
        ]
        
        comentarios_negativos = [
            'No quedé satisfecha con el resultado.',
            'El servicio no cumplió mis expectativas.',
            'Podría mejorar mucho en atención al cliente.',
            'No recomendaría este servicio.',
            'El resultado no fue el esperado.'
        ]
        
        # Crear múltiples calificaciones por negocio
        for negocio in negocios:
            profs_negocio = profesionales_por_negocio.get(negocio, [])
            if profs_negocio:
                # Crear 5-10 calificaciones por negocio
                num_calificaciones = random.randint(5, 10)
                for _ in range(num_calificaciones):
                    cliente = random.choice(clientes)
                    profesional = random.choice(profs_negocio)
                    
                    # Generar puntaje realista (más probabilidad de puntajes altos)
                    puntaje = random.choices([1, 2, 3, 4, 5], weights=[1, 2, 3, 4, 5])[0]
                    
                    # Seleccionar comentario según puntaje
                    if puntaje >= 4:
                        comentario = random.choice(comentarios_positivos)
                    elif puntaje == 3:
                        comentario = random.choice(comentarios_neutros)
                    else:
                        comentario = random.choice(comentarios_negativos)
                    
                    Calificacion.objects.get_or_create(
                        cliente=cliente,
                        negocio=negocio,
                        profesional=profesional,
                        defaults={
                            'puntaje': puntaje,
                            'comentario': comentario
                        }
                    )
        
        self.stdout.write(self.style.SUCCESS('Calificaciones realistas creadas para todos los negocios'))

        self.stdout.write(self.style.SUCCESS('¡Base de datos de demo lista!'))
        self.stdout.write(self.style.SUCCESS('Credenciales de acceso:'))
        self.stdout.write(self.style.SUCCESS('- Superadmin: superadmin / Malware01'))
        self.stdout.write(self.style.SUCCESS('- Negocios: negocio1-negocio10 / Malware01'))
        self.stdout.write(self.style.SUCCESS('- Profesionales: profesional1-profesional100 / Malware01'))
        self.stdout.write(self.style.SUCCESS('- Clientes: cliente1-cliente20 / Malware01')) 