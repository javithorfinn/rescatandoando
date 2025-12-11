from django.contrib import admin
from django.contrib.auth.hashers import make_password
from mainApp.models import (
    Usuario, Voluntario, HogarTemporal, Animal, Adoptante,
    SolicitudAdopcion, Adopcion, FichaMedica, Contrato, Donacion,
    EntrevistaVoluntario, EntrevistaAdopcion, SolicitudVoluntariado
)

# Register your models here.

class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['cuenta', 'nombre', 'email', 'rol']
    list_filter = ['rol']
    search_fields = ['cuenta', 'nombre', 'email']
    
    def save_model(self, request, obj, form, change):
        # Si la contraseña ha sido modificada y no está hasheada
        if 'contraseña' in form.changed_data:
            # Verificar si la contraseña no está hasheada (no empieza con pbkdf2_sha256$)
            if not obj.contraseña.startswith('pbkdf2_sha256$'):
                obj.contraseña = make_password(obj.contraseña)
        super().save_model(request, obj, form, change)

admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Voluntario)
admin.site.register(HogarTemporal)
admin.site.register(Animal)
# admin.site.register(Adoptante)  # Deshabilitado temporalmente
admin.site.register(SolicitudAdopcion)
admin.site.register(Adopcion)
admin.site.register(FichaMedica)
admin.site.register(Contrato)
admin.site.register(Donacion)
admin.site.register(EntrevistaVoluntario)
admin.site.register(EntrevistaAdopcion)
admin.site.register(SolicitudVoluntariado)