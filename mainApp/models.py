from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone
import secrets

# ------------------------
# USUARIO
# ------------------------
from django.db import models
from django.utils.html import escape

class Usuario(models.Model):
    ROL_CHOICES = [
        ('admin', 'Administrador'),
        ('voluntario', 'Voluntario'),
        ('adoptante', 'Adoptante'),
        ('usuario', 'Usuario'),
    ]
    
    AVATAR_CHOICES = [
        ('perro', '🐕 Perro'),
        ('gato', '🐱 Gato'),
        ('pajaro', '🦜 Pájaro'),
        ('chanchito', '🐷 Chanchito'),
        ('rata', '🐭 Rata'),
        ('caballo', '🐴 Caballo'),
        ('conejo', '🐰 Conejo'),
        ('tortuga', '🐢 Tortuga'),
        ('vaca', '🐮 Vaca'),
        ('dinosaurio', '🦖 Dinosaurio'),
    ]
    
    nombre = models.CharField(max_length=100)
    cuenta = models.CharField(max_length=70, unique=True)  # username
    email = models.CharField(max_length=100, blank=True)
    contraseña = models.CharField(max_length=255)
    telefono = models.CharField(max_length=15, blank=True)
    direccion = models.CharField(max_length=150, blank=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='usuario')
    avatar = models.CharField(max_length=20, choices=AVATAR_CHOICES, default='perro')
    fecha_creacion = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Sanitizar campos antes de guardar
        if self.nombre:
            self.nombre = escape(self.nombre)[:100]
        if self.cuenta:
            self.cuenta = escape(self.cuenta)[:70]
        if self.email:
            self.email = escape(self.email)[:100]
        if self.direccion:
            self.direccion = escape(self.direccion)[:150]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre
    
    def es_admin(self):
        return self.rol == 'admin'
    
    def puede_gestionar_animales(self):
        return self.rol in ['admin', 'voluntario']


# ------------------------
# VOLUNTARIO
# ------------------------
class Voluntario(models.Model):
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tipo_voluntariado = models.CharField(max_length=30)
    fecha_ingreso = models.DateField()

    def __str__(self):
        return f"Voluntario: {self.id_usuario.nombre}"


# ------------------------
# SOLICITUD DE VOLUNTARIADO
# ------------------------
class SolicitudVoluntariado(models.Model):
    EQUIPOS = [
        ('veterinaria', 'Veterinaria'),
        ('peluqueria', 'Peluquería'),
        ('rescatistas', 'Rescatistas'),
        ('diseno', 'Diseño gráfico'),
        ('tallerista', 'Tallerista'),
        ('hogar_temporal', 'Hogar Temporal'),
    ]
    
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('entrevista_agendada', 'Entrevista Agendada'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    
    # Datos personales
    nombre_completo = models.CharField(max_length=100)
    email = models.EmailField()
    telefono = models.CharField(max_length=20)
    direccion = models.CharField(max_length=200)
    instagram = models.CharField(max_length=100)
    
    # Información del voluntariado
    equipo = models.CharField(max_length=30, choices=EQUIPOS)
    experiencia_previa = models.TextField()
    motivacion = models.TextField()
    informacion_adicional = models.TextField(blank=True, default='')
    
    # Control administrativo
    fecha_solicitud = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=30, choices=ESTADOS, default='pendiente')
    fecha_entrevista = models.DateTimeField(null=True, blank=True)
    observaciones_admin = models.TextField(blank=True, default='')
    usuario_solicitante = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL, related_name='solicitudes_voluntariado')
    procesado_por = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL, related_name='solicitudes_voluntariado_procesadas')
    
    def __str__(self):
        return f"Solicitud de {self.nombre_completo} - {self.get_equipo_display()}"


# ------------------------
# HOGAR TEMPORAL
# ------------------------
class HogarTemporal(models.Model):
    id_voluntario = models.ForeignKey(Voluntario, on_delete=models.CASCADE)
    direccion = models.CharField(max_length=150)
    descripcion = models.CharField(max_length=255)
    capacidad_animales = models.IntegerField()
    estado = models.CharField(max_length=20)

    def __str__(self):
        return f"Hogar en {self.direccion}"


# ------------------------
# ANIMAL
# ------------------------
class Animal(models.Model):
    nombre = models.CharField(max_length=50)
    especie = models.CharField(max_length=30)
    edad = models.IntegerField()
    sexo = models.CharField(max_length=10)
    estado_salud = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=255)
    foto = models.ImageField(upload_to="animales/")
    disponible = models.BooleanField(default=True)
    id_hogar = models.ForeignKey(HogarTemporal, on_delete=models.CASCADE)

    def __str__(self):
        return self.nombre
    
    def get_ficha_medica(self):
        try:
            return self.fichamedica.first()
        except:
            return None


# ------------------------
# FICHA MÉDICA
# ------------------------
class FichaMedica(models.Model):
    id_animal = models.ForeignKey(Animal, on_delete=models.CASCADE, related_name='fichamedica')
    # Vacunación y Esterilización
    esterilizado = models.BooleanField(default=False)
    fecha_esterilizacion = models.DateField(null=True, blank=True)
    vacunas_al_dia = models.BooleanField(default=True)
    ultima_vacunacion = models.CharField(max_length=255, blank=True, default='')
    # Control Veterinario
    ultimo_control = models.DateField(null=True, blank=True)
    proximo_control = models.DateField(null=True, blank=True)
    estado_salud = models.CharField(max_length=100, default='Bueno')
    # Observaciones
    observaciones = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Ficha médica de {self.id_animal.nombre}"


# ------------------------
# ADOPTANTE
# ------------------------
class Adoptante(models.Model):
    # Relación con usuario (puede ser NULL si solicita sin registrarse)
    id_usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    
    # Datos personales
    nombre = models.CharField(max_length=100, default='')
    email = models.EmailField(max_length=100, default='')
    telefono = models.CharField(max_length=20, default='')
    rut = models.CharField(max_length=20, default='', blank=True)
    foto_carnet_frontal = models.ImageField(upload_to='carnets/', null=True, blank=True)
    foto_carnet_trasera = models.ImageField(upload_to='carnets/', null=True, blank=True)
    es_extranjero = models.BooleanField(default=False)
    tiene_residencia_definitiva = models.BooleanField(default=False, blank=True)
    direccion = models.CharField(max_length=200, default='')
    ciudad = models.CharField(max_length=100, default='')
    comuna = models.CharField(max_length=100, default='')
    edad = models.IntegerField(default=18)
    
    # Motivación y experiencia
    por_que_adoptar = models.TextField(default='')
    tiene_o_tuvo_mascotas = models.BooleanField(default=False)
    mascotas_esterilizadas_vacunadas = models.CharField(max_length=100, blank=True, default='')  # Si/No/N/A
    alimento_mascotas = models.CharField(max_length=200, default='')
    
    # Familia
    miembros_familia = models.IntegerField(default=1)
    decision_compartida = models.BooleanField(default=True)
    es_alergico = models.BooleanField(default=False)
    medidas_alergia = models.TextField(blank=True, default='')
    
    # Vivienda
    tipo_vivienda = models.CharField(max_length=50, default='')  # Casa/Departamento
    tiene_mallas_proteccion = models.BooleanField(default=False)
    permiten_mascotas = models.BooleanField(default=True)
    tiene_recursos_economicos = models.BooleanField(default=True)
    
    # Compromiso
    que_pasa_si_mudanza = models.TextField(default='')
    acepta_videollamada = models.BooleanField(default=True)
    acepta_seguimiento = models.BooleanField(default=True)
    acepta_enviar_fotos = models.BooleanField(default=True)
    acepta_tenencia_indoor = models.BooleanField(default=True)

    def __str__(self):
        return f"Adoptante: {self.nombre}"


# ------------------------
# SOLICITUD DE ADOPCIÓN
# ------------------------
class SolicitudAdopcion(models.Model):
    ESTADOS = [
        ('pendiente', 'Solicitud Pendiente'),
        ('entrevista_agendada', 'Entrevista Agendada'),
        ('entrevista_realizada', 'Entrevista Realizada'),
        ('aprobada', 'Aprobada'),
        ('rechazada', 'Rechazada'),
    ]
    
    id_animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    id_adoptante = models.ForeignKey(Adoptante, on_delete=models.CASCADE)
    fecha_solicitud = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=30, choices=ESTADOS, default='pendiente')
    
    # Seguimiento del proceso de solicitud
    fecha_entrevista = models.DateTimeField(null=True, blank=True)
    observaciones_entrevista = models.TextField(blank=True, default='')
    motivo_rechazo = models.TextField(blank=True, default='')
    fecha_aprobacion = models.DateField(null=True, blank=True)
    
    # Usuario que procesa (admin o voluntario)
    procesado_por = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL, related_name='solicitudes_adopcion_procesadas')

    def __str__(self):
        return f"Solicitud de {self.id_animal.nombre} - {self.id_adoptante.nombre}"


# ------------------------
# ADOPCIÓN (Solo adopciones aprobadas)
# ------------------------
class Adopcion(models.Model):
    ESTADOS = [
        ('en_proceso', 'En Proceso'),
        ('contrato_generado', 'Contrato Generado'),
        ('completada', 'Adopción Completada'),
    ]
    
    id_animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    id_adoptante = models.ForeignKey(Adoptante, on_delete=models.CASCADE)
    solicitud_origen = models.ForeignKey('SolicitudAdopcion', null=True, blank=True, on_delete=models.SET_NULL, related_name='adopcion_creada')
    fecha_adopcion = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=30, choices=ESTADOS, default='en_proceso')
    
    # Seguimiento del proceso de adopción
    fecha_contrato = models.DateField(null=True, blank=True)
    fecha_completada = models.DateField(null=True, blank=True)
    
    # Usuario que aprobó
    aprobado_por = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL, related_name='adopciones_aprobadas')

    def __str__(self):
        return f"Adopción de {self.id_animal.nombre} por {self.id_adoptante.nombre}"


# ------------------------
# ENTREVISTA DE ADOPCIÓN
# ------------------------
class EntrevistaAdopcion(models.Model):
    id_adopcion = models.ForeignKey(Adopcion, on_delete=models.CASCADE)
    id_voluntario = models.ForeignKey(Voluntario, null=True, blank=True, on_delete=models.SET_NULL)
    id_admin = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL)
    fecha = models.DateField()
    observaciones = models.CharField(max_length=255)
    resultado = models.CharField(max_length=20)

    def __str__(self):
        return f"Entrevista adopción #{self.id_adopcion.id}"


# ------------------------
# CONTRATO
# ------------------------
class Contrato(models.Model):
    id_adopcion = models.ForeignKey(Adopcion, on_delete=models.CASCADE)
    id_adoptante = models.ForeignKey(Adoptante, on_delete=models.CASCADE)
    fecha_generacion = models.DateField(auto_now_add=True)
    archivo_pdf = models.FileField(upload_to='contratos/', blank=True)
    firma_adoptante = models.BooleanField(default=False)
    firma_admin = models.BooleanField(default=False)
    fecha_firma_adoptante = models.DateField(null=True, blank=True)
    fecha_firma_admin = models.DateField(null=True, blank=True)
    # Datos del contrato
    acepta_seguimiento = models.BooleanField(default=True)
    compromiso_cuidado = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Contrato #{self.id} - {self.id_adoptante.nombre}"


# ------------------------
# DONACIÓN
# ------------------------
class Donacion(models.Model):
    id_usuario = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL)
    nombre_donante = models.CharField(max_length=100, blank=True)
    email = models.CharField(max_length=100, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha = models.DateField(null=True, blank=True)
    comprobante = models.ImageField(upload_to='comprobantes/')
    comentario = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Donación de {self.monto}"


# ------------------------
# ENTREVISTA DE VOLUNTARIO
# ------------------------
class EntrevistaVoluntario(models.Model):
    id_voluntario = models.ForeignKey(Voluntario, on_delete=models.CASCADE)
    id_admin = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL, related_name="admin_entrevista_vol")
    id_voluntario_entr = models.ForeignKey(Voluntario, null=True, blank=True, on_delete=models.SET_NULL, related_name="vol_entrevista_vol")
    fecha = models.DateField()
    observaciones = models.CharField(max_length=255)
    resultado = models.CharField(max_length=20)

    def __str__(self):
        return f"Entrevista a {self.id_voluntario.id_usuario.nombre}"


# ------------------------
# TOKEN DE RECUPERACIÓN DE CONTRASEÑA
# ------------------------
class PasswordResetToken(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_valid(self):
        # Token válido por 1 hora
        return timezone.now() < self.created_at + timedelta(hours=1)
    
    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)
    
    def __str__(self):
        return f"Token para {self.usuario.cuenta}"
