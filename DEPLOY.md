# Deploy a Render - Rescatando

## Paso 1: Preparar el repositorio en GitHub

1. Ve a https://github.com y crea un nuevo repositorio llamado `RescatandoAndo` (público o privado)

2. En tu terminal local, ejecuta:
```bash
cd C:\Users\javit\MisProyectos\RescatandoAndo\DjangoRescatando
git init
git add .
git commit -m "Initial commit - Proyecto Rescatando"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/RescatandoAndo.git
git push -u origin main
```

## Paso 2: Crear cuenta en Render

1. Ve a https://render.com
2. Haz clic en "Get Started"
3. Regístrate con tu cuenta de GitHub

## Paso 3: Crear base de datos PostgreSQL

1. En el dashboard de Render, haz clic en "New +"
2. Selecciona "PostgreSQL"
3. Configuración:
   - **Name**: `rescatando-db`
   - **Database**: `rescatando`
   - **User**: (se genera automáticamente)
   - **Region**: Oregon (US West) o el más cercano
   - **PostgreSQL Version**: 17
   - **Datadog API Key**: (dejar vacío)
   - **Plan**: Free
4. Haz clic en "Create Database"
5. **IMPORTANTE**: Copia la URL de conexión interna (`Internal Database URL`) - la necesitarás después

## Paso 4: Crear Web Service

1. En el dashboard, haz clic en "New +"
2. Selecciona "Web Service"
3. Conecta tu repositorio de GitHub
4. Configuración:
   - **Name**: `rescatando`
   - **Region**: Oregon (US West) - mismo que la DB
   - **Branch**: `main`
   - **Root Directory**: (dejar vacío)
   - **Runtime**: `Python 3`
   - **Build Command**: `sh build.sh`
   - **Start Command**: `gunicorn DjangoRescatando.wsgi:application`
   - **Plan**: Free

## Paso 5: Configurar Variables de Entorno

En la sección "Environment", haz clic en "Add Environment Variable" y agrega:

```
DEBUG=False
SECRET_KEY=tu-secret-key-super-segura-genera-una-nueva
ALLOWED_HOSTS=rescatando.onrender.com,*.onrender.com
DATABASE_URL=postgresql://user:password@host:5432/database
CSRF_TRUSTED_ORIGINS=https://rescatando.onrender.com,https://*.onrender.com
ADMIN_PASSWORD=tu_password_admin_segura
```

**Notas importantes:**
- `DATABASE_URL`: Pega aquí la Internal Database URL que copiaste en el Paso 3
- `SECRET_KEY`: Genera una nueva con: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `ALLOWED_HOSTS`: Reemplaza `rescatando` con el nombre que le pusiste a tu servicio
- `CSRF_TRUSTED_ORIGINS`: Reemplaza `rescatando` con tu nombre de servicio
- `ADMIN_PASSWORD`: Password para el usuario admin que se creará automáticamente

## Paso 6: Deploy

1. Haz clic en "Create Web Service"
2. Render comenzará el build automáticamente
3. Espera 5-10 minutos mientras:
   - Instala dependencias
   - Ejecuta migraciones
   - Crea usuario admin
   - Recolecta archivos estáticos

## Paso 7: Verificar Deploy

1. Una vez que veas "Live" en verde, haz clic en la URL de tu aplicación
2. Deberías ver la página principal de Rescatando
3. Para acceder como admin:
   - Usuario: `admin`
   - Contraseña: La que configuraste en `ADMIN_PASSWORD`

## Problemas comunes

### Error de migraciones
Si las migraciones fallan, conéctate al Shell de Render:
1. En tu servicio, ve a "Shell"
2. Ejecuta: `python manage.py migrate --run-syncdb`

### Admin no se creó
En el Shell de Render:
```bash
python manage.py createadmin --password TU_PASSWORD
```

### Error 500 - Internal Server Error
1. Ve a "Logs" en tu servicio de Render
2. Busca el traceback del error
3. Verifica que todas las variables de entorno estén correctas

### Los archivos estáticos no cargan
En el Shell:
```bash
python manage.py collectstatic --no-input
```

## Actualizaciones futuras

Cada vez que hagas cambios:
```bash
git add .
git commit -m "Descripción del cambio"
git push origin main
```

Render detectará el push y re-desplegará automáticamente.

## Backup de base de datos

Render Free hace backups automáticos por 7 días. Para descargar un backup manual:
1. Ve a tu base de datos PostgreSQL en Render
2. Click en "Backups"
3. Descarga el archivo `.dump`

---

¿Necesitas ayuda? Revisa los logs en Render > Tu servicio > Logs
