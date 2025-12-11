from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import escape
import re

# Create your views here.
from mainApp.forms import (UsuarioForm, VoluntarioForm, HogarTemporalForm, AnimalForm, 
                           AdoptanteForm, SolicitudAdopcionForm, DonacionForm,
                           EntrevistaAdopcionForm, InscripcionVoluntarioForm, FichaMedicaForm)
from mainApp.models import (Usuario, Voluntario, HogarTemporal, Animal, Adoptante, 
                            SolicitudAdopcion, Adopcion, Donacion, EntrevistaAdopcion, Contrato, SolicitudVoluntariado, PasswordResetToken)
import datetime

# Función para sanitizar entrada de texto
def sanitize_input(text, max_length=None):
    """Sanitiza entrada de texto eliminando caracteres peligrosos"""
    if text is None:
        return ''
    # Escapar HTML
    text = escape(str(text))
    # Limitar longitud si se especifica
    if max_length:
        text = text[:max_length]
    return text.strip()

def validate_email(email):
    """Valida formato de email"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def index(request):
    animales = Animal.objects.filter(disponible=True).prefetch_related('fichamedica')
    # Agregar la ficha médica a cada animal para acceso más fácil en el template
    for animal in animales:
        animal.ficha = animal.fichamedica.first() if animal.fichamedica.exists() else None
    return render(request, 'index.html', {'animales': animales})

def login_view(request):
    if request.method == 'POST':
        cuenta = sanitize_input(request.POST.get('cuenta'), 70)
        contraseña = request.POST.get('contraseña')
        
        if not cuenta or not contraseña:
            messages.error(request, 'Debes ingresar usuario y contraseña')
            return render(request, 'login.html')
        
        try:
            usuario = Usuario.objects.get(cuenta=cuenta)
            # Verificar contraseña (asumiendo que están hasheadas)
            if check_password(contraseña, usuario.contraseña):
                # Guardar usuario en sesión
                request.session['usuario_id'] = usuario.id
                request.session['usuario_nombre'] = usuario.cuenta  # Nombre de la cuenta
                request.session['usuario_rol'] = usuario.rol
                request.session['usuario_avatar'] = usuario.avatar
                messages.success(request, f'¡Bienvenido {usuario.cuenta}!')
                return redirect('index')
            else:
                messages.error(request, 'Usuario inválido')
                return render(request, 'login.html')
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario inválido')
            return render(request, 'login.html')
    
    return render(request, 'login.html')

def logout_view(request):
    request.session.flush()
    messages.success(request, 'Sesión cerrada correctamente')
    return redirect('index')

def register_usuario(request):
    if request.method == 'POST':
        # Obtener y sanitizar datos del formulario
        nombre = sanitize_input(request.POST.get('nombre'), 100)
        cuenta = sanitize_input(request.POST.get('cuenta'), 70)
        email = sanitize_input(request.POST.get('email'), 100)
        telefono = sanitize_input(request.POST.get('telefono'), 15)
        contraseña = request.POST.get('contraseña')
        confirmar_contraseña = request.POST.get('confirmar_contraseña')
        direccion = sanitize_input(request.POST.get('direccion'), 150)
        rol = request.POST.get('rol', 'usuario')
        
        # Validaciones
        if not all([nombre, cuenta, email, contraseña]):
            messages.error(request, 'Todos los campos obligatorios deben ser completados')
            return render(request, 'login.html')
        
        # Validar email
        if not validate_email(email):
            messages.error(request, 'Formato de email inválido')
            return render(request, 'login.html')
        
        # Validar longitud de contraseña
        if len(contraseña) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres')
            return render(request, 'login.html')
        
        # Validar que las contraseñas coincidan
        if contraseña != confirmar_contraseña:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'login.html')
        
        # Verificar si el nombre de cuenta ya existe
        if Usuario.objects.filter(cuenta=cuenta).exists():
            messages.error(request, 'El nombre de usuario ya está en uso. Por favor elige otro.')
            return render(request, 'login.html')
        
        # Verificar si el email ya está registrado
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, 'Este correo electrónico ya está registrado. ¿Olvidaste tu contraseña?')
            return render(request, 'login.html')
        
        # Validar rol permitido
        if rol not in ['usuario', 'admin', 'voluntario', 'adoptante']:
            rol = 'usuario'
        
        # Crear usuario
        try:
            usuario = Usuario.objects.create(
                nombre=nombre,
                cuenta=cuenta,
                email=email,
                telefono=telefono,
                contraseña=make_password(contraseña),
                direccion=direccion,
                rol=rol
            )
            messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión.')
            return redirect('login')
        except Exception as e:
            messages.error(request, f'Error al registrar: {str(e)}')
            return render(request, 'login.html')
    
    return render(request, 'login.html')

def ayudar(request):
    context = {}
    if request.session.get('usuario_id'):
        try:
            usuario = Usuario.objects.get(id=request.session['usuario_id'])
            context['usuario_email'] = usuario.email
            context['usuario_telefono'] = usuario.telefono
            context['usuario_nombre_completo'] = usuario.nombre
        except Usuario.DoesNotExist:
            pass
    return render(request, 'ayudar.html', context)

# Decorador personalizado para verificar permisos
def requiere_permiso(roles_permitidos):
    def decorador(vista):
        def wrapper(request, *args, **kwargs):
            usuario_rol = request.session.get('usuario_rol')
            if not usuario_rol:
                messages.error(request, 'Debes iniciar sesión')
                return redirect('login')
            if usuario_rol not in roles_permitidos:
                messages.error(request, 'No tienes permisos para acceder a esta página')
                return redirect('index')
            return vista(request, *args, **kwargs)
        return wrapper
    return decorador

# Ejemplo de vista protegida para agregar animales
@requiere_permiso(['admin', 'voluntario'])
def agregar_animal(request):
    if request.method == 'POST':
        form = AnimalForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Animal agregado exitosamente')
            return redirect('index')
    else:
        form = AnimalForm()
    return render(request, 'agregar_animal.html', {'form': form})

# Vista para solicitud de adopción (público)
def solicitar_adopcion(request, animal_id):
    animal = get_object_or_404(Animal, id=animal_id)
    usuario_id = request.session.get('usuario_id')
    
    if not usuario_id:
        messages.error(request, 'Debes iniciar sesión para solicitar una adopción')
        return redirect('login')
    
    if request.method == 'POST':
        usuario = Usuario.objects.get(id=usuario_id)
        
        # Manejar fotos del carnet si se subieron
        foto_carnet_frontal = request.FILES.get('foto_carnet_frontal', None)
        foto_carnet_trasera = request.FILES.get('foto_carnet_trasera', None)
        
        # Crear o actualizar adoptante con todos los datos del formulario completo
        adoptante, created = Adoptante.objects.get_or_create(
            id_usuario=usuario,
            defaults={
                'nombre': request.POST.get('nombre', ''),
                'email': usuario.email,
                'telefono': request.POST.get('telefono', ''),
                'rut': request.POST.get('rut', ''),
                'foto_carnet_frontal': foto_carnet_frontal,
                'foto_carnet_trasera': foto_carnet_trasera,
                'es_extranjero': request.POST.get('es_extranjero') == '1',
                'tiene_residencia_definitiva': request.POST.get('tiene_residencia_definitiva') == '1',
                'direccion': request.POST.get('direccion', ''),
                'ciudad': request.POST.get('ciudad', ''),
                'comuna': request.POST.get('comuna', ''),
                'edad': int(request.POST.get('edad', 18)),
                'por_que_adoptar': request.POST.get('por_que_adoptar', ''),
                'tiene_o_tuvo_mascotas': request.POST.get('tiene_o_tuvo_mascotas') == '1',
                'mascotas_esterilizadas_vacunadas': request.POST.get('mascotas_esterilizadas_vacunadas', ''),
                'alimento_mascotas': request.POST.get('alimento_mascotas', ''),
                'miembros_familia': int(request.POST.get('miembros_familia', 1)),
                'decision_compartida': request.POST.get('decision_compartida') == '1',
                'es_alergico': request.POST.get('es_alergico') == '1',
                'medidas_alergia': request.POST.get('medidas_alergia', ''),
                'tipo_vivienda': request.POST.get('tipo_vivienda', ''),
                'tiene_mallas_proteccion': request.POST.get('tiene_mallas_proteccion') == '1',
                'permiten_mascotas': request.POST.get('permiten_mascotas') == '1',
                'tiene_recursos_economicos': request.POST.get('tiene_recursos_economicos') == '1',
                'que_pasa_si_mudanza': request.POST.get('que_pasa_si_mudanza', ''),
                'acepta_videollamada': request.POST.get('acepta_videollamada') == '1',
                'acepta_seguimiento': request.POST.get('acepta_seguimiento') == '1',
                'acepta_enviar_fotos': request.POST.get('acepta_enviar_fotos') == '1',
                'acepta_tenencia_indoor': request.POST.get('acepta_tenencia_indoor') == '1'
            }
        )
        
        # Si no es nuevo, actualizar todos los datos
        if not created:
            adoptante.nombre = request.POST.get('nombre', adoptante.nombre)
            adoptante.email = usuario.email
            adoptante.telefono = request.POST.get('telefono', adoptante.telefono)
            adoptante.rut = request.POST.get('rut', adoptante.rut)
            if foto_carnet_frontal:
                adoptante.foto_carnet_frontal = foto_carnet_frontal
            if foto_carnet_trasera:
                adoptante.foto_carnet_trasera = foto_carnet_trasera
            adoptante.es_extranjero = request.POST.get('es_extranjero') == '1'
            adoptante.tiene_residencia_definitiva = request.POST.get('tiene_residencia_definitiva') == '1'
            adoptante.direccion = request.POST.get('direccion', adoptante.direccion)
            adoptante.ciudad = request.POST.get('ciudad', adoptante.ciudad)
            adoptante.comuna = request.POST.get('comuna', adoptante.comuna)
            adoptante.edad = int(request.POST.get('edad', adoptante.edad))
            adoptante.por_que_adoptar = request.POST.get('por_que_adoptar', adoptante.por_que_adoptar)
            adoptante.tiene_o_tuvo_mascotas = request.POST.get('tiene_o_tuvo_mascotas') == '1'
            adoptante.mascotas_esterilizadas_vacunadas = request.POST.get('mascotas_esterilizadas_vacunadas', '')
            adoptante.alimento_mascotas = request.POST.get('alimento_mascotas', adoptante.alimento_mascotas)
            adoptante.miembros_familia = int(request.POST.get('miembros_familia', adoptante.miembros_familia))
            adoptante.decision_compartida = request.POST.get('decision_compartida') == '1'
            adoptante.es_alergico = request.POST.get('es_alergico') == '1'
            adoptante.medidas_alergia = request.POST.get('medidas_alergia', '')
            adoptante.tipo_vivienda = request.POST.get('tipo_vivienda', adoptante.tipo_vivienda)
            adoptante.tiene_mallas_proteccion = request.POST.get('tiene_mallas_proteccion') == '1'
            adoptante.permiten_mascotas = request.POST.get('permiten_mascotas') == '1'
            adoptante.tiene_recursos_economicos = request.POST.get('tiene_recursos_economicos') == '1'
            adoptante.que_pasa_si_mudanza = request.POST.get('que_pasa_si_mudanza', adoptante.que_pasa_si_mudanza)
            adoptante.acepta_videollamada = request.POST.get('acepta_videollamada') == '1'
            adoptante.acepta_seguimiento = request.POST.get('acepta_seguimiento') == '1'
            adoptante.acepta_enviar_fotos = request.POST.get('acepta_enviar_fotos') == '1'
            adoptante.acepta_tenencia_indoor = request.POST.get('acepta_tenencia_indoor') == '1'
            adoptante.save()
        
        # Crear SOLICITUD de adopción (no adopción directa)
        solicitud = SolicitudAdopcion.objects.create(
            id_animal=animal,
            id_adoptante=adoptante,
            estado='pendiente'
        )
        
        messages.success(request, f'¡Solicitud de adopción enviada para {animal.nombre}! Pronto te contactaremos para agendar la videollamada.')
        return redirect('index')
    
    return render(request, 'solicitar_adopcion.html', {'animal': animal})

# Vista para donaciones (público)
def realizar_donacion(request):
    if request.method == 'POST':
        form = DonacionForm(request.POST, request.FILES)
        usuario_id = request.session.get('usuario_id')
        
        # Validar que usuarios no registrados ingresen su nombre
        if not usuario_id and not request.POST.get('nombre_donante'):
            messages.error(request, 'Por favor ingresa tu nombre completo')
            return render(request, 'donacion.html', {'form': form, 'usuario_logueado': False})
        
        if form.is_valid():
            donacion = form.save(commit=False)
            if usuario_id:
                donacion.id_usuario = Usuario.objects.get(id=usuario_id)
                donacion.nombre_donante = f"@{request.session.get('usuario_nombre', 'Usuario')}"
            # Si no se proporciona fecha, usar la fecha actual
            if not donacion.fecha:
                from datetime import date
                donacion.fecha = date.today()
            donacion.save()
            messages.success(request, '¡Gracias por tu donación!')
            return redirect('index')
    else:
        form = DonacionForm()
    
    usuario_logueado = 'usuario_id' in request.session
    return render(request, 'donacion.html', {'form': form, 'usuario_logueado': usuario_logueado})

# Vista para ver comprobantes (público)
def ver_comprobantes(request):
    donaciones = Donacion.objects.filter(comprobante__isnull=False).order_by('-fecha')
    return render(request, 'ver_comprobantes.html', {'donaciones': donaciones})

# Vista para inscripción de voluntarios (público)
def inscripcion_voluntario(request):
    if request.method == 'POST':
        # Obtener datos del formulario
        nombre_completo = request.POST.get('nombre_completo')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        instagram = request.POST.get('instagram')
        equipo = request.POST.get('equipo')
        experiencia_previa = request.POST.get('experiencia_previa')
        motivacion = request.POST.get('motivacion')
        informacion_adicional = request.POST.get('informacion_adicional', '')
        
        try:
            # Crear solicitud de voluntariado
            SolicitudVoluntariado.objects.create(
                nombre_completo=nombre_completo,
                email=email,
                telefono=telefono,
                direccion=direccion,
                instagram=instagram,
                equipo=equipo,
                experiencia_previa=experiencia_previa,
                motivacion=motivacion,
                informacion_adicional=informacion_adicional,
                estado='pendiente'
            )
            
            messages.success(request, '¡Solicitud enviada! Te contactaremos pronto para agendar una entrevista.')
            return redirect('index')
        except Exception as e:
            messages.error(request, f'Error al enviar solicitud: {str(e)}')
            return redirect('ayudar')
    
    return render(request, 'inscripcion_voluntario.html')

# Vista para registrar entrevistas (admin/voluntario)
@requiere_permiso(['admin', 'voluntario'])
def registrar_entrevista(request, adopcion_id):
    adopcion = get_object_or_404(Adopcion, id=adopcion_id)
    
    if request.method == 'POST':
        form = EntrevistaAdopcionForm(request.POST)
        if form.is_valid():
            entrevista = form.save(commit=False)
            entrevista.id_adopcion = adopcion
            entrevista.save()
            
            # Actualizar estado de adopción según resultado
            if entrevista.resultado == 'aprobado':
                adopcion.estado = 'aprobado'
            else:
                adopcion.estado = 'rechazado'
            adopcion.save()
            
            messages.success(request, 'Entrevista registrada exitosamente')
            return redirect('lista_adopciones')
    else:
        form = EntrevistaAdopcionForm()
    
    return render(request, 'registrar_entrevista.html', {'form': form, 'adopcion': adopcion})

# Vista para listar solicitudes de adopción (admin/voluntario)
@requiere_permiso(['admin', 'voluntario'])
def lista_adopciones(request):
    adopciones = Adopcion.objects.all().order_by('-fecha_solicitud')
    return render(request, 'lista_adopciones.html', {'adopciones': adopciones})

# Vista para gestionar usuarios (solo admin)
@requiere_permiso(['admin'])
def gestionar_usuarios(request):
    usuarios = Usuario.objects.all()
    return render(request, 'gestionar_usuarios.html', {'usuarios': usuarios})

# Vista para cambiar rol de usuario (solo admin)
@requiere_permiso(['admin'])
def cambiar_rol_usuario(request, usuario_id):
    if request.method == 'POST':
        usuario = get_object_or_404(Usuario, id=usuario_id)
        nuevo_rol = request.POST.get('rol')
        usuario.rol = nuevo_rol
        usuario.save()
        messages.success(request, f'Rol de {usuario.nombre} actualizado a {nuevo_rol}')
    return redirect('gestionar_usuarios')

# Vista para perfil de usuario
def perfil(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        messages.error(request, 'Debes iniciar sesión')
        return redirect('login')
    
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'POST':
        # Actualizar datos del usuario
        usuario.nombre = request.POST.get('nombre')
        usuario.email = request.POST.get('email')
        usuario.telefono = request.POST.get('telefono')
        usuario.direccion = request.POST.get('direccion')
        usuario.avatar = request.POST.get('avatar', 'perro1')
        
        # Cambiar contraseña si se proporciona
        nueva_contraseña = request.POST.get('nueva_contraseña')
        confirmar_contraseña = request.POST.get('confirmar_contraseña')
        
        if nueva_contraseña:
            if nueva_contraseña == confirmar_contraseña:
                usuario.contraseña = make_password(nueva_contraseña)
                messages.success(request, 'Contraseña actualizada correctamente')
            else:
                messages.error(request, 'Las contraseñas no coinciden')
                return render(request, 'perfil.html', {'usuario': usuario})
        
        usuario.save()
        request.session['usuario_nombre'] = usuario.cuenta  # Actualizar sesión con nombre de cuenta
        request.session['usuario_avatar'] = usuario.avatar  # Actualizar avatar en sesión
        messages.success(request, 'Perfil actualizado correctamente')
        return redirect('perfil')
    
    return render(request, 'perfil.html', {'usuario': usuario})

# Vista para mis adopciones
def mis_adopciones(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        messages.error(request, 'Debes iniciar sesión')
        return redirect('login')
    
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    # Buscar adoptante asociado al usuario
    try:
        adoptante = Adoptante.objects.get(id_usuario=usuario)
        # Obtener solicitudes de adopción del usuario
        solicitudes = SolicitudAdopcion.objects.filter(id_adoptante=adoptante).order_by('-fecha_solicitud')
        # Obtener adopciones aprobadas (con contrato)
        adopciones = Adopcion.objects.filter(id_adoptante=adoptante).order_by('-fecha_adopcion')
    except Adoptante.DoesNotExist:
        solicitudes = []
        adopciones = []
    
    return render(request, 'mis_adopciones.html', {
        'solicitudes': solicitudes,
        'adopciones': adopciones
    })

# Vista para gestionar animales (admin/voluntario)
@requiere_permiso(['admin', 'voluntario'])
def gestionar_animales(request):
    from mainApp.models import FichaMedica
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'agregar':
            try:
                # Obtener o crear hogar temporal
                id_hogar = request.POST.get('id_hogar')
                hogar = None
                if id_hogar:
                    hogar = HogarTemporal.objects.get(id=id_hogar)
                elif HogarTemporal.objects.exists():
                    hogar = HogarTemporal.objects.first()
                else:
                    # Crear hogar temporal por defecto
                    # Primero necesitamos un voluntario
                    if Voluntario.objects.exists():
                        voluntario = Voluntario.objects.first()
                    else:
                        # Crear voluntario básico del admin
                        usuario_admin = Usuario.objects.filter(rol='admin').first()
                        if usuario_admin:
                            voluntario = Voluntario.objects.create(
                                id_usuario=usuario_admin,
                                tipo_voluntariado='cuidado',
                                fecha_ingreso=datetime.date.today()
                            )
                        else:
                            messages.error(request, 'No hay usuarios admin o voluntarios disponibles')
                            return redirect('gestionar_animales')
                    
                    hogar = HogarTemporal.objects.create(
                        id_voluntario=voluntario,
                        direccion='Refugio Central',
                        descripcion='Hogar temporal principal',
                        capacidad_animales=50,
                        estado='activo'
                    )
                
                # Crear animal
                animal = Animal.objects.create(
                    nombre=request.POST.get('nombre'),
                    especie=request.POST.get('especie'),
                    edad=int(request.POST.get('edad', 0)),
                    sexo=request.POST.get('sexo'),
                    estado_salud=request.POST.get('estado_salud', 'Saludable'),
                    descripcion=request.POST.get('descripcion', ''),
                    foto=request.FILES.get('foto') if 'foto' in request.FILES else None,
                    disponible=True,
                    id_hogar=hogar
                )
                
                # Crear ficha médica automáticamente
                FichaMedica.objects.create(
                    id_animal=animal,
                    esterilizado=request.POST.get('esterilizado') == 'on',
                    fecha_esterilizacion=request.POST.get('fecha_esterilizacion') or None,
                    vacunas_al_dia=request.POST.get('vacunas_al_dia') == 'on',
                    ultima_vacunacion=request.POST.get('ultima_vacunacion', ''),
                    ultimo_control=request.POST.get('ultimo_control') or None,
                    proximo_control=request.POST.get('proximo_control') or None,
                    estado_salud=request.POST.get('estado_salud_ficha', 'Por evaluar'),
                    observaciones=request.POST.get('observaciones', 'Animal recién ingresado')
                )
                
                messages.success(request, f'Animal {animal.nombre} agregado exitosamente con su ficha médica')
            except Exception as e:
                messages.error(request, f'Error al agregar animal: {str(e)}')
        
        elif accion == 'editar':
            try:
                id_animal = request.POST.get('id_animal')
                animal = get_object_or_404(Animal, id=id_animal)
                
                animal.nombre = request.POST.get('nombre')
                animal.especie = request.POST.get('especie')
                animal.edad = int(request.POST.get('edad', 0))
                animal.sexo = request.POST.get('sexo')
                animal.estado_salud = request.POST.get('estado_salud', 'Saludable')
                animal.descripcion = request.POST.get('descripcion', '')
                animal.disponible = request.POST.get('disponible') == 'true'
                
                if 'foto' in request.FILES:
                    animal.foto = request.FILES['foto']
                
                animal.save()
                messages.success(request, f'Animal {animal.nombre} actualizado exitosamente')
            except Exception as e:
                messages.error(request, f'Error al editar animal: {str(e)}')
        
        elif accion == 'editar_ficha':
            try:
                id_animal = request.POST.get('id_animal')
                animal = get_object_or_404(Animal, id=id_animal)
                ficha = FichaMedica.objects.get(id_animal=animal)
                
                ficha.esterilizado = request.POST.get('esterilizado') == 'on'
                ficha.fecha_esterilizacion = request.POST.get('fecha_esterilizacion') or None
                ficha.vacunas_al_dia = request.POST.get('vacunas_al_dia') == 'on'
                ficha.ultima_vacunacion = request.POST.get('ultima_vacunacion', '')
                ficha.ultimo_control = request.POST.get('ultimo_control') or None
                ficha.proximo_control = request.POST.get('proximo_control') or None
                ficha.estado_salud = request.POST.get('estado_salud_ficha', '')
                ficha.observaciones = request.POST.get('observaciones', '')
                
                ficha.save()
                messages.success(request, f'Ficha médica de {animal.nombre} actualizada exitosamente')
            except Exception as e:
                messages.error(request, f'Error al editar ficha médica: {str(e)}')
        
        elif accion == 'eliminar':
            id_animal = request.POST.get('id_animal')
            animal = get_object_or_404(Animal, id=id_animal)
            nombre = animal.nombre
            animal.delete()
            messages.success(request, f'Animal {nombre} eliminado correctamente')
        
        return redirect('gestionar_animales')
    
    # GET - Mostrar lista de animales
    animales = Animal.objects.all().order_by('nombre')
    hogares = HogarTemporal.objects.all()
    return render(request, 'gestionar_animales.html', {'animales': animales, 'hogares': hogares})

# API para obtener ficha médica
@requiere_permiso(['admin', 'voluntario'])
def obtener_ficha_medica(request, id_animal):
    from django.http import JsonResponse
    from mainApp.models import FichaMedica
    
    try:
        animal = get_object_or_404(Animal, id=id_animal)
        ficha = FichaMedica.objects.get(id_animal=animal)
        
        data = {
            'esterilizado': ficha.esterilizado,
            'fecha_esterilizacion': ficha.fecha_esterilizacion.isoformat() if ficha.fecha_esterilizacion else None,
            'vacunas_al_dia': ficha.vacunas_al_dia,
            'ultima_vacunacion': ficha.ultima_vacunacion,
            'ultimo_control': ficha.ultimo_control.isoformat() if ficha.ultimo_control else None,
            'proximo_control': ficha.proximo_control.isoformat() if ficha.proximo_control else None,
            'estado_salud': ficha.estado_salud,
            'observaciones': ficha.observaciones
        }
        return JsonResponse(data)
    except FichaMedica.DoesNotExist:
        return JsonResponse({'error': 'Ficha médica no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Vista para ver solicitudes (admin/voluntario)
@requiere_permiso(['admin', 'voluntario'])
def ver_solicitudes(request):
    from mainApp.models import EntrevistaVoluntario
    from datetime import datetime
    from django.core.mail import send_mail
    from django.conf import settings
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        usuario_id = request.session.get('usuario_id')
        
        if accion == 'agendar_entrevista':
            id_solicitud = request.POST.get('id_adopcion')  # Mantener nombre del campo por compatibilidad
            fecha_entrevista = request.POST.get('fecha_entrevista')
            link_zoom = request.POST.get('link_zoom', '')  # Solo para enviar por correo
            
            solicitud = get_object_or_404(SolicitudAdopcion, id=id_solicitud)
            solicitud.estado = 'entrevista_agendada'
            solicitud.fecha_entrevista = fecha_entrevista
            solicitud.procesado_por_id = usuario_id
            solicitud.save()
            
            # Enviar correo al adoptante
            try:
                fecha_formateada = datetime.strptime(fecha_entrevista, '%Y-%m-%dT%H:%M').strftime('%d/%m/%Y a las %H:%M')
                asunto = f'🐾 Entrevista Agendada - Adopción de {solicitud.id_animal.nombre}'
                mensaje = f"""
Hola {solicitud.id_adoptante.nombre},

¡Tenemos buenas noticias! Tu solicitud para adoptar a {solicitud.id_animal.nombre} ha sido revisada y hemos agendado una entrevista contigo.

📅 Fecha: {fecha_formateada}
🔗 Link de Zoom: {link_zoom if link_zoom else 'Te enviaremos el link próximamente'}

Por favor, asegúrate de estar disponible en la fecha y hora indicadas. Durante la entrevista hablaremos sobre:
- Tus condiciones de vivienda
- Experiencia con mascotas
- Compromiso de cuidado

Si tienes alguna duda o necesitas reagendar, contáctanos por Instagram @rescatandoando_stgo

¡Esperamos verte pronto!

Con cariño,
Equipo RescatandoAndo Stgo 🐶🐱
                """
                
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [solicitud.id_adoptante.email],
                    fail_silently=False,
                )
                messages.success(request, f'Entrevista agendada para {solicitud.id_adoptante.nombre}. Correo enviado exitosamente.')
            except Exception as e:
                messages.warning(request, f'Entrevista agendada pero hubo un error al enviar el correo: {str(e)}')
        
        elif accion == 'marcar_entrevista_realizada':
            id_solicitud = request.POST.get('id_adopcion')
            observaciones = request.POST.get('observaciones', '')
            
            solicitud = get_object_or_404(SolicitudAdopcion, id=id_solicitud)
            solicitud.estado = 'entrevista_realizada'
            solicitud.observaciones_entrevista = observaciones
            solicitud.save()
            messages.info(request, 'Entrevista marcada como realizada')
        
        elif accion == 'aprobar_adopcion':
            id_solicitud = request.POST.get('id_adopcion')
            solicitud = get_object_or_404(SolicitudAdopcion, id=id_solicitud)
            solicitud.estado = 'aprobada'
            solicitud.fecha_aprobacion = datetime.now().date()
            solicitud.procesado_por_id = usuario_id
            solicitud.save()
            
            # CREAR LA ADOPCIÓN REAL y marcar animal como no disponible
            adopcion = Adopcion.objects.create(
                id_animal=solicitud.id_animal,
                id_adoptante=solicitud.id_adoptante,
                solicitud_origen=solicitud,
                aprobado_por_id=usuario_id,
                estado='en_proceso'
            )
            
            # Marcar animal como no disponible
            animal = solicitud.id_animal
            animal.disponible = False
            animal.save()
            
            # Generar el contrato automáticamente
            from mainApp.utils import generar_contrato_pdf
            contrato = Contrato.objects.create(
                id_adopcion=adopcion,
                id_adoptante=solicitud.id_adoptante,
                acepta_seguimiento=solicitud.id_adoptante.acepta_seguimiento,
                compromiso_cuidado=f'Compromiso de cuidado para {solicitud.id_animal.nombre}'
            )
            
            if generar_contrato_pdf(contrato):
                adopcion.estado = 'contrato_generado'
                adopcion.fecha_contrato = datetime.now().date()
                adopcion.save()
                mensaje_contrato = ' Contrato generado automáticamente.'
            else:
                mensaje_contrato = ' Contrato creado pero falta generar PDF (instala reportlab).'
            
            # Enviar correo de aprobación
            try:
                asunto = f'🎉 ¡Adopción Aprobada! - {solicitud.id_animal.nombre}'
                mensaje = f"""
Hola {solicitud.id_adoptante.nombre},

¡Felicitaciones! 🎊 

Tu solicitud para adoptar a {solicitud.id_animal.nombre} ha sido APROBADA. Esto significa que cumples con todos los requisitos para darle un hogar lleno de amor.

Próximos pasos:
1. Nos pondremos en contacto contigo para coordinar la entrega
2. Firmaremos el contrato de adopción
3. Te daremos todas las indicaciones de cuidado
4. ¡{solicitud.id_animal.nombre} tendrá su nuevo hogar! 🏡

Recuerda que estaremos en contacto constante para hacer seguimiento y asegurarnos de que todo vaya bien.

¡Gracias por darle una segunda oportunidad a {solicitud.id_animal.nombre}!

Con mucho cariño,
Equipo RescatandoAndo Stgo 🐶🐱💕
                """
                
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [solicitud.id_adoptante.email],
                    fail_silently=False,
                )
                messages.success(request, f'Solicitud aprobada. Adopción creada, {solicitud.id_animal.nombre} marcado como no disponible.{mensaje_contrato} Correo enviado.')
            except Exception as e:
                messages.warning(request, f'Adopción aprobada pero hubo un error al enviar el correo: {str(e)}')
        
        elif accion == 'rechazar_adopcion':
            id_solicitud = request.POST.get('id_adopcion')
            motivo = request.POST.get('motivo_rechazo', '')
            
            solicitud = get_object_or_404(SolicitudAdopcion, id=id_solicitud)
            solicitud.estado = 'rechazada'
            solicitud.motivo_rechazo = motivo
            solicitud.procesado_por_id = usuario_id
            solicitud.save()
            messages.warning(request, 'Solicitud de adopción rechazada')
        
        elif accion == 'generar_contrato':
            id_adopcion = request.POST.get('id_adopcion')
            adopcion = get_object_or_404(Adopcion, id=id_adopcion)
            
            # Crear el contrato
            contrato = Contrato.objects.create(
                id_adopcion=adopcion,
                id_adoptante=adopcion.id_adoptante,
                acepta_seguimiento=True,
                compromiso_cuidado='El adoptante se compromete a cuidar y proteger al animal adoptado.'
            )
            
            # Generar el PDF del contrato
            from mainApp.utils import generar_contrato_pdf
            if generar_contrato_pdf(contrato):
                adopcion.estado = 'contrato_generado'
                adopcion.fecha_contrato = datetime.now().date()
                adopcion.save()
                messages.success(request, f'Contrato generado exitosamente para {adopcion.id_adoptante.nombre}')
            else:
                messages.error(request, 'Error al generar el PDF del contrato. Instala reportlab: pip install reportlab')
        
        elif accion == 'aprobar_voluntario':
            id_entrevista = request.POST.get('id_entrevista')
            entrevista = get_object_or_404(EntrevistaVoluntario, id=id_entrevista)
            entrevista.resultado = 'aprobado'
            entrevista.save()
            messages.success(request, 'Voluntario aprobado')
        
        elif accion == 'rechazar_voluntario':
            id_entrevista = request.POST.get('id_entrevista')
            entrevista = get_object_or_404(EntrevistaVoluntario, id=id_entrevista)
            entrevista.resultado = 'rechazado'
            entrevista.save()
            messages.warning(request, 'Voluntario rechazado')
        
        # Acciones para solicitudes de voluntariado
        elif accion == 'agendar_entrevista_voluntariado':
            id_solicitud = request.POST.get('id_solicitud')
            fecha_entrevista = request.POST.get('fecha_entrevista')
            link_zoom = request.POST.get('link_zoom', '')  # Solo para enviar por correo
            
            solicitud = get_object_or_404(SolicitudVoluntariado, id=id_solicitud)
            solicitud.estado = 'entrevista_agendada'
            solicitud.fecha_entrevista = fecha_entrevista
            solicitud.procesado_por_id = usuario_id
            solicitud.save()
            
            # Enviar correo al voluntario
            try:
                fecha_formateada = datetime.strptime(fecha_entrevista, '%Y-%m-%dT%H:%M').strftime('%d/%m/%Y a las %H:%M')
                asunto = f'🙌 Entrevista Agendada - Voluntariado en {solicitud.get_equipo_display()}'
                mensaje = f"""
Hola {solicitud.nombre_completo},

¡Excelentes noticias! Tu solicitud para unirte como voluntario/a en el equipo de {solicitud.get_equipo_display()} ha sido revisada y hemos agendado una entrevista contigo.

📅 Fecha: {fecha_formateada}
🔗 Link de Zoom: {link_zoom if link_zoom else 'Te enviaremos el link próximamente'}

Durante la entrevista conversaremos sobre:
- Tu experiencia previa con animales
- Disponibilidad horaria
- Expectativas y compromiso
- Actividades específicas del equipo

Si tienes alguna duda o necesitas reagendar, contáctanos por Instagram @rescatandoando_stgo

¡Nos emociona conocerte y que seas parte de nuestro equipo!

Con cariño,
Equipo RescatandoAndo Stgo 🐾
                """
                
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [solicitud.email],
                    fail_silently=False,
                )
                messages.success(request, f'Entrevista agendada para {solicitud.nombre_completo}. Correo enviado exitosamente.')
            except Exception as e:
                messages.warning(request, f'Entrevista agendada pero hubo un error al enviar el correo: {str(e)}')
        
        elif accion == 'aprobar_voluntariado':
            id_solicitud = request.POST.get('id_solicitud')
            observaciones = request.POST.get('observaciones_admin', '')
            
            solicitud = get_object_or_404(SolicitudVoluntariado, id=id_solicitud)
            solicitud.estado = 'aprobada'
            solicitud.observaciones_admin = observaciones
            solicitud.procesado_por_id = usuario_id
            solicitud.save()
            
            # Enviar correo de aprobación
            try:
                asunto = f'🎉 ¡Bienvenido/a al Equipo! - {solicitud.get_equipo_display()}'
                mensaje = f"""
Hola {solicitud.nombre_completo},

¡Felicitaciones! 🎊 

Tu solicitud para unirte como voluntario/a en el equipo de {solicitud.get_equipo_display()} ha sido APROBADA.

Nos encanta tenerte en el equipo RescatandoAndo. Tu compromiso y amor por los animales marcan la diferencia.

Próximos pasos:
1. Nos pondremos en contacto contigo por WhatsApp o Instagram
2. Te integraremos al grupo del equipo de {solicitud.get_equipo_display()}
3. Coordinaremos tus primeras actividades
4. ¡Comenzarás a hacer la diferencia en la vida de muchos animalitos! 🐾

{f'Observaciones: {observaciones}' if observaciones else ''}

¡Gracias por sumarte a nuestra misión!

Con mucho cariño,
Equipo RescatandoAndo Stgo 🙌💕
                """
                
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [solicitud.email],
                    fail_silently=False,
                )
                messages.success(request, f'Solicitud de {solicitud.nombre_completo} aprobada. Correo enviado exitosamente.')
            except Exception as e:
                messages.warning(request, f'Solicitud aprobada pero hubo un error al enviar el correo: {str(e)}')
        
        elif accion == 'rechazar_voluntariado':
            id_solicitud = request.POST.get('id_solicitud')
            observaciones = request.POST.get('observaciones_admin', '')
            
            solicitud = get_object_or_404(SolicitudVoluntariado, id=id_solicitud)
            solicitud.estado = 'rechazada'
            solicitud.observaciones_admin = observaciones
            solicitud.procesado_por_id = usuario_id
            solicitud.save()
            
            # Enviar correo de rechazo (opcional, de forma amable)
            try:
                asunto = 'Actualización sobre tu solicitud de voluntariado - RescatandoAndo'
                mensaje = f"""
Hola {solicitud.nombre_completo},

Gracias por tu interés en formar parte del equipo de voluntarios de RescatandoAndo.

Lamentablemente, en este momento no podemos continuar con tu solicitud para el equipo de {solicitud.get_equipo_display()}.

{f'Motivo: {observaciones}' if observaciones else ''}

Esto no significa que no valores para nosotros. Te invitamos a:
- Seguir apoyándonos desde las redes sociales
- Participar en nuestras campañas de difusión
- Volver a postular más adelante cuando surjan nuevas oportunidades

¡Gracias por tu interés y compromiso con los animales!

Con cariño,
Equipo RescatandoAndo Stgo 🐾
                """
                
                send_mail(
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [solicitud.email],
                    fail_silently=False,
                )
                messages.warning(request, f'Solicitud de {solicitud.nombre_completo} rechazada. Correo enviado.')
            except Exception as e:
                messages.warning(request, f'Solicitud rechazada pero hubo un error al enviar el correo: {str(e)}')
        
        elif accion == 'eliminar_solicitud':
            id_solicitud = request.POST.get('id_solicitud')
            solicitud = get_object_or_404(SolicitudAdopcion, id=id_solicitud)
            animal_nombre = solicitud.id_animal.nombre
            
            # Si la solicitud fue aprobada, volver a hacer disponible el animal
            if solicitud.estado == 'aprobada':
                solicitud.id_animal.disponible = True
                solicitud.id_animal.save()
            
            solicitud.delete()
            messages.success(request, f'Solicitud de {animal_nombre} eliminada correctamente.')
        
        elif accion == 'eliminar_adopcion':
            id_adopcion = request.POST.get('id_adopcion')
            adopcion = get_object_or_404(Adopcion, id=id_adopcion)
            animal = adopcion.id_animal
            animal_nombre = animal.nombre
            
            # Si tiene solicitud origen, cambiar su estado a "cancelada" o eliminarla
            if adopcion.solicitud_origen:
                solicitud = adopcion.solicitud_origen
                solicitud.estado = 'rechazada'
                solicitud.motivo_rechazo = 'Adopción cancelada por administración'
                solicitud.save()
            
            # Eliminar contratos relacionados
            Contrato.objects.filter(id_adopcion=adopcion).delete()
            
            # Volver a hacer disponible el animal
            animal.disponible = True
            animal.save()
            
            adopcion.delete()
            messages.success(request, f'Adopción de {animal_nombre} eliminada. Animal disponible nuevamente.')
        
        return redirect('ver_solicitudes')
    
    # GET - Mostrar SOLICITUDES DE ADOPCIÓN (no adopciones) agrupadas por estado
    solicitudes_pendientes = SolicitudAdopcion.objects.filter(estado='pendiente').order_by('-fecha_solicitud')
    solicitudes_entrevista = SolicitudAdopcion.objects.filter(estado__in=['entrevista_agendada', 'entrevista_realizada']).order_by('-fecha_solicitud')
    solicitudes_aprobadas = SolicitudAdopcion.objects.filter(estado='aprobada').order_by('-fecha_solicitud')
    solicitudes_rechazadas = SolicitudAdopcion.objects.filter(estado='rechazada').order_by('-fecha_solicitud')
    
    # ADOPCIONES REALES (solo las aprobadas)
    adopciones_en_proceso = Adopcion.objects.filter(estado__in=['en_proceso', 'contrato_generado']).order_by('-fecha_adopcion')
    adopciones_completadas = Adopcion.objects.filter(estado='completada').order_by('-fecha_adopcion')
    
    # Solicitudes de voluntariado por estado
    voluntariado_pendientes = SolicitudVoluntariado.objects.filter(estado='pendiente').order_by('-fecha_solicitud')
    voluntariado_entrevista = SolicitudVoluntariado.objects.filter(estado='entrevista_agendada').order_by('-fecha_solicitud')
    voluntariado_aprobadas = SolicitudVoluntariado.objects.filter(estado='aprobada').order_by('-fecha_solicitud')
    voluntariado_rechazadas = SolicitudVoluntariado.objects.filter(estado='rechazada').order_by('-fecha_solicitud')
    
    # Total de solicitudes de voluntariado (todas las solicitudes)
    total_solicitudes_voluntariado = SolicitudVoluntariado.objects.all().count()
    
    voluntarios = EntrevistaVoluntario.objects.all().order_by('-fecha')
    donaciones = Donacion.objects.all().order_by('-fecha')
    
    return render(request, 'lista_adopciones.html', {
        'adopciones_pendientes': solicitudes_pendientes,
        'adopciones_entrevista': solicitudes_entrevista,
        'adopciones_aprobadas': solicitudes_aprobadas,
        'adopciones_rechazadas': solicitudes_rechazadas,
        'adopciones_proceso': adopciones_en_proceso,
        'adopciones_completadas': adopciones_completadas,
        'voluntariado_pendientes': voluntariado_pendientes,
        'voluntariado_entrevista': voluntariado_entrevista,
        'voluntariado_aprobadas': voluntariado_aprobadas,
        'voluntariado_rechazadas': voluntariado_rechazadas,
        'total_solicitudes_voluntariado': total_solicitudes_voluntariado,
        'voluntarios': voluntarios,
        'donaciones': donaciones
    })

# Vista actualizada para gestionar usuarios (admin)
@requiere_permiso(['admin'])
def gestionar_usuarios_view(request):
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'cambiar_rol':
            id_usuario = request.POST.get('id_usuario')
            nuevo_rol = request.POST.get('nuevo_rol')
            usuario = get_object_or_404(Usuario, id=id_usuario)
            usuario.rol = nuevo_rol
            usuario.save()
            messages.success(request, f'Rol de {usuario.nombre} actualizado a {nuevo_rol}')
        
        elif accion == 'eliminar_usuario':
            id_usuario = request.POST.get('id_usuario')
            try:
                from django.db import connection
                usuario = Usuario.objects.get(id=id_usuario)
                nombre_usuario = usuario.nombre
                
                # Verificar si tiene registros relacionados
                with connection.cursor() as cursor:
                    # Verificar en Voluntario
                    cursor.execute("SELECT COUNT(*) FROM mainApp_voluntario WHERE id_usuario_id = %s", [id_usuario])
                    count_voluntario = cursor.fetchone()[0]
                    
                    # Verificar en Adoptante
                    cursor.execute("SELECT COUNT(*) FROM mainApp_adoptante WHERE id_usuario_id = %s", [id_usuario])
                    count_adoptante = cursor.fetchone()[0]
                    
                    # Verificar en Donacion
                    cursor.execute("SELECT COUNT(*) FROM mainApp_donacion WHERE id_usuario_id = %s", [id_usuario])
                    count_donacion = cursor.fetchone()[0]
                    
                    if count_voluntario > 0 or count_adoptante > 0 or count_donacion > 0:
                        relaciones = []
                        if count_voluntario > 0:
                            relaciones.append(f"{count_voluntario} registro(s) de voluntario")
                        if count_adoptante > 0:
                            relaciones.append(f"{count_adoptante} registro(s) de adoptante")
                        if count_donacion > 0:
                            relaciones.append(f"{count_donacion} donación(es)")
                        
                        messages.error(request, f'No se puede eliminar a {nombre_usuario}. Tiene: {", ".join(relaciones)}. Elimina primero estos registros o cambia su estado.')
                    else:
                        # Si no tiene relaciones, eliminar
                        cursor.execute("DELETE FROM mainApp_usuario WHERE id = %s", [id_usuario])
                        messages.success(request, f'Usuario {nombre_usuario} eliminado correctamente')
                        
            except Usuario.DoesNotExist:
                messages.error(request, 'Usuario no encontrado')
            except Exception as e:
                messages.error(request, f'Error al eliminar usuario: {str(e)}')
        
        return redirect('gestionar_usuarios')
    
    # GET - Mostrar lista de usuarios
    usuarios = Usuario.objects.all().order_by('nombre')
    return render(request, 'gestionar_usuarios.html', {'usuarios': usuarios})


def solicitar_voluntariado(request):
    """Vista para procesar solicitud de voluntariado - REQUIERE LOGIN"""
    usuario_id = request.session.get('usuario_id')
    
    if not usuario_id:
        messages.error(request, 'Debes iniciar sesión para solicitar unirte como voluntario')
        return redirect('login')
    
    if request.method == 'POST':
        try:
            usuario = Usuario.objects.get(id=usuario_id)
            
            # Crear nueva solicitud con los datos del formulario y vincular al usuario
            solicitud = SolicitudVoluntariado(
                nombre_completo = request.POST.get('nombre_completo'),
                email = request.POST.get('email'),
                telefono = request.POST.get('telefono'),
                direccion = request.POST.get('direccion'),
                instagram = request.POST.get('instagram', ''),
                equipo = request.POST.get('equipo'),
                experiencia_previa = request.POST.get('experiencia_previa'),
                motivacion = request.POST.get('motivacion'),
                informacion_adicional = request.POST.get('informacion_adicional', ''),
                estado = 'pendiente',
                usuario_solicitante = usuario  # Vincular al usuario registrado
            )
            solicitud.save()
            
            messages.success(request, '¡Tu solicitud de voluntariado ha sido enviada exitosamente! Pronto nos pondremos en contacto contigo.')
            return redirect('ayudar')
        except Exception as e:
            messages.error(request, f'Error al enviar la solicitud: {str(e)}')
            return redirect('ayudar')
    
    return redirect('ayudar')


# Vista para solicitar recuperación de contraseña
def recuperar_contrasena(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            # Usar filter().first() en lugar de get() para evitar error con duplicados
            usuario = Usuario.objects.filter(email=email).first()
            
            if not usuario:
                messages.error(request, 'No existe un usuario con ese correo electrónico.')
                return render(request, 'recuperar_contrasena.html')
            
            # Eliminar tokens antiguos del usuario
            PasswordResetToken.objects.filter(usuario=usuario).delete()
            
            # Crear nuevo token
            token = PasswordResetToken.generate_token()
            PasswordResetToken.objects.create(usuario=usuario, token=token)
            
            # Enviar email
            reset_url = f"{request.scheme}://{request.get_host()}/resetear-contrasena/{token}/"
            mensaje = f"""
Hola {usuario.nombre},

Recibimos una solicitud para restablecer tu contraseña en RescatandoAndo.

Haz clic en el siguiente enlace para crear una nueva contraseña:
{reset_url}

Este enlace es válido por 1 hora.

Si no solicitaste este cambio, ignora este correo.

Saludos,
Equipo RescatandoAndo 🐾
            """
            
            send_mail(
                'Recuperación de Contraseña - RescatandoAndo',
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            messages.success(request, 'Te hemos enviado un correo con instrucciones para recuperar tu contraseña.')
            return redirect('login')
            
        except Exception as e:
            messages.error(request, f'Error al enviar el correo: {str(e)}')
    
    return render(request, 'recuperar_contrasena.html')


# Vista para resetear contraseña con token
def resetear_contrasena(request, token):
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        
        if not reset_token.is_valid():
            messages.error(request, 'Este enlace ha expirado. Solicita uno nuevo.')
            return redirect('recuperar_contrasena')
        
        if request.method == 'POST':
            nueva_contrasena = request.POST.get('nueva_contrasena')
            confirmar_contrasena = request.POST.get('confirmar_contrasena')
            
            if nueva_contrasena != confirmar_contrasena:
                messages.error(request, 'Las contraseñas no coinciden.')
                return render(request, 'resetear_contrasena.html', {'token': token})
            
            if len(nueva_contrasena) < 6:
                messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
                return render(request, 'resetear_contrasena.html', {'token': token})
            
            # Actualizar contraseña
            usuario = reset_token.usuario
            usuario.contraseña = make_password(nueva_contrasena)
            usuario.save()
            
            # Eliminar token usado
            reset_token.delete()
            
            messages.success(request, '¡Contraseña actualizada! Ya puedes iniciar sesión.')
            return redirect('login')
        
        return render(request, 'resetear_contrasena.html', {'token': token})
        
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'El enlace no es válido.')
        return redirect('recuperar_contrasena')



