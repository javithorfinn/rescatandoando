from django import forms
from .models import (Animal, Usuario, Voluntario, HogarTemporal, Adoptante, 
                     Adopcion, FichaMedica, Donacion, EntrevistaAdopcion, 
                     EntrevistaVoluntario, Contrato)

class UsuarioForm(forms.ModelForm):
    contraseña = forms.CharField(widget=forms.PasswordInput(render_value=True))

    class Meta:
        model = Usuario
        fields = ['nombre', 'cuenta', 'email', 'contraseña', 'telefono', 'direccion', 'rol']

class VoluntarioForm(forms.ModelForm):
    class Meta:
        model = Voluntario
        fields = ['id_usuario', 'tipo_voluntariado', 'fecha_ingreso']
        widgets = {
            'fecha_ingreso': forms.DateInput(attrs={'type': 'date'}),
        }

class HogarTemporalForm(forms.ModelForm):
    class Meta:
        model = HogarTemporal
        fields = ['id_voluntario', 'direccion', 'descripcion', 'capacidad_animales', 'estado']

class AnimalForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = ['nombre', 'especie', 'edad', 'sexo', 'estado_salud', 'descripcion', 'foto', 'disponible', 'id_hogar']
        widgets = {
            'foto': forms.ClearableFileInput(),
        }

class FichaMedicaForm(forms.ModelForm):
    class Meta:
        model = FichaMedica
        fields = ['id_animal', 'esterilizado', 'fecha_esterilizacion', 'vacunas_al_dia', 
                  'ultima_vacunacion', 'ultimo_control', 'proximo_control', 'estado_salud', 'observaciones']
        widgets = {
            'fecha_esterilizacion': forms.DateInput(attrs={'type': 'date'}),
            'ultimo_control': forms.DateInput(attrs={'type': 'date'}),
            'proximo_control': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 4}),
        }

class AdoptanteForm(forms.ModelForm):
    class Meta:
        model = Adoptante
        fields = ['nombre', 'email', 'telefono', 'rut', 'foto_carnet_frontal', 'foto_carnet_trasera', 'es_extranjero', 
                  'tiene_residencia_definitiva', 'direccion', 'ciudad', 'comuna', 'edad',
                  'por_que_adoptar', 'tiene_o_tuvo_mascotas', 'mascotas_esterilizadas_vacunadas',
                  'alimento_mascotas', 'miembros_familia', 'decision_compartida', 'es_alergico',
                  'medidas_alergia', 'tipo_vivienda', 'tiene_mallas_proteccion', 'permiten_mascotas',
                  'tiene_recursos_economicos', 'que_pasa_si_mudanza', 'acepta_videollamada',
                  'acepta_seguimiento', 'acepta_enviar_fotos', 'acepta_tenencia_indoor']

class SolicitudAdopcionForm(forms.ModelForm):
    class Meta:
        model = Adopcion
        fields = ['id_animal']
        widgets = {
            'id_animal': forms.Select(attrs={'class': 'form-control'}),
        }

class DonacionForm(forms.ModelForm):
    nombre_donante = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre completo'}),
        label='Nombre Completo'
    )
    fecha = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        label='Fecha de la Donación'
    )
    
    class Meta:
        model = Donacion
        fields = ['nombre_donante', 'monto', 'fecha', 'comprobante']
        widgets = {
            'monto': forms.NumberInput(attrs={'min': '1000', 'step': '100', 'class': 'form-control', 'placeholder': 'Ej: 5000'}),
        }

class EntrevistaAdopcionForm(forms.ModelForm):
    class Meta:
        model = EntrevistaAdopcion
        fields = ['id_adopcion', 'id_voluntario', 'fecha', 'observaciones', 'resultado']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

class InscripcionVoluntarioForm(forms.ModelForm):
    """Formulario público para inscribirse como voluntario"""
    nombre = forms.CharField(max_length=100)
    email = forms.EmailField()
    telefono = forms.CharField(max_length=15)
    tipo_voluntariado = forms.CharField(max_length=30)
    
    class Meta:
        model = Voluntario
        fields = ['tipo_voluntariado']
