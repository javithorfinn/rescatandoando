# Rescatando - Plataforma de Adopción de Animales

Este es un sistema web para ayudar en el proceso de adopción de animales rescatados. La plataforma permite gestionar todo el ciclo desde que un animal llega a un hogar temporal hasta que encuentra una familia definitiva.

## Qué hace el sistema

### Usuarios generales
- Ver animales disponibles para adopción
- Llenar solicitudes de adopción con información detallada
- Realizar donaciones y subir comprobantes
- Crear un perfil personal
- Ver el estado de sus adopciones

### Voluntarios
- Administrar animales en hogares temporales
- Revisar y procesar solicitudes de adopción
- Mantener fichas médicas actualizadas
- Generar contratos de adopción

### Administradores
- Gestionar usuarios y asignar roles
- Controlar hogares temporales
- Aprobar solicitudes de voluntariado
- Revisar donaciones
- Acceso completo al panel administrativo

## Tecnologías utilizadas

## Tecnologías utilizadas

- Backend: Django 5.2.8
- Base de Datos: MySQL
- Frontend: Bootstrap 5.3.3, HTML5, CSS3
- Python: 3.14.0
- Librerías: PyMySQL, Pillow

## Cómo instalar

Necesitas tener instalado Python 3.14 o superior, MySQL Server y pip.

### Pasos

1. Clonar el repositorio
```bash
git clone <url-del-repositorio>
cd DjangoRescatando
```

2. Crear un entorno virtual
```bash
python -m venv .venv
.venv\Scripts\activate  # En Windows
```

3. Instalar las dependencias
```bash
pip install django pymysql pillow
```

4. Configurar la base de datos
- Crear una base de datos MySQL llamada `DJANGO_RESCATANDO`
- Actualizar las credenciales en `DjangoRescatando/settings.py` si es necesario

5. Ejecutar las migraciones
```bash
python manage.py migrate
```

6. (Opcional) Crear un superusuario para el admin
```bash
python manage.py createsuperuser
```

7. Iniciar el servidor
```bash
python manage.py runserver
```

El sitio estará corriendo en `http://127.0.0.1:8000/`

## Diseño

La interfaz usa la fuente Chewy de Google Fonts porque tiene un estilo amigable y redondeado. Los colores principales son verdes y azules (#009688, #00bfa5, #80deea). Los iconos vienen de Font Awesome 6.5.0 y los usuarios pueden elegir avatares con emojis de animales.

## Estructura del proyecto

```
DjangoRescatando/
├── DjangoRescatando/       # Configuración principal
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── mainApp/                # Aplicación principal
│   ├── models.py           # Modelos de datos
│   ├── views.py            # Lógica de vistas
│   ├── forms.py            # Formularios
│   ├── admin.py            # Panel admin
│   └── migrations/         # Migraciones de BD
├── templates/              # Plantillas HTML
├── media/                  # Archivos multimedia
│   ├── animales/
│   ├── carnets/
│   ├── comprobantes/
│   └── contratos/
├── static/                 # Archivos estáticos
└── manage.py
```

## Modelos principales

- Usuario: Maneja cuentas con diferentes roles (admin, voluntario, adoptante)
- Animal: Información de los animales disponibles
- Adoptante: Datos de las personas que quieren adoptar
- SolicitudAdopcion: Lleva el proceso de cada solicitud
- Adopcion: Registro de adopciones aprobadas y completadas
- Voluntario: Información de voluntarios
- HogarTemporal: Hogares donde están los animales temporalmente
- Donacion: Registro de donaciones recibidas

## Seguridad

El sistema incluye sanitización de inputs, protección CSRF, gestión segura de contraseñas con hash, recuperación de contraseñas mediante tokens temporales, y validación de roles para acceder a diferentes secciones.

## Contribuir

Si quieres colaborar con el proyecto:

1. Haz un fork del repositorio
2. Crea una rama para tu cambio (git checkout -b mejora/descripcion)
3. Haz commit de tus cambios (git commit -m 'Descripción del cambio')
4. Sube tu rama (git push origin mejora/descripcion)
5. Abre un Pull Request

## Licencia

Este proyecto se desarrolló para facilitar la adopción responsable de animales rescatados.

## Autor

Javier - Proyecto RescatandoAndo
