"""
Management command para crear un superusuario admin.
Uso: python manage.py createadmin
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from mainApp.models import Usuario


class Command(BaseCommand):
    help = 'Crea un superusuario admin si no existe'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cuenta',
            type=str,
            default='admin',
            help='Nombre de cuenta del admin (default: admin)'
        )
        parser.add_argument(
            '--nombre',
            type=str,
            default='Administrador',
            help='Nombre completo del admin (default: Administrador)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@rescatando.com',
            help='Email del admin (default: admin@rescatando.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            help='Password del admin (si no se provee, usa variable ADMIN_PASSWORD o "rescatando2025")'
        )

    def handle(self, *args, **options):
        cuenta = options['cuenta']
        nombre = options['nombre']
        email = options['email']
        
        # Obtener password desde argumento, variable de entorno, o default
        password = options.get('password') or os.getenv('ADMIN_PASSWORD', 'rescatando2025')

        # Verificar si ya existe
        if Usuario.objects.filter(cuenta=cuenta).exists():
            self.stdout.write(
                self.style.WARNING(f'✓ El usuario "{cuenta}" ya existe. No se creó ningún usuario.')
            )
            return

        # Crear el superusuario
        try:
            admin = Usuario.objects.create(
                nombre=nombre,
                cuenta=cuenta,
                email=email,
                contraseña=make_password(password),
                rol='admin',
                avatar='👤'
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✓ Superusuario creado exitosamente!')
            )
            self.stdout.write(f'  • Cuenta: {cuenta}')
            self.stdout.write(f'  • Nombre: {nombre}')
            self.stdout.write(f'  • Email: {email}')
            self.stdout.write(f'  • Rol: admin')
            
            if options.get('password'):
                self.stdout.write(self.style.WARNING('\n⚠️  Password personalizada configurada'))
            else:
                self.stdout.write(self.style.WARNING('\n⚠️  IMPORTANTE: Cambia la contraseña después del primer login'))
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Error al crear superusuario: {str(e)}')
            )
