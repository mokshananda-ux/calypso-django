from django import forms
from .models import Account, UserProfile

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Ingresa Contraseña',
        
    }))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirmar Contraseña',
        
    }))
    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password', 'confirm_password']

    
    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError(
                "Las contraseñas no coinciden!"
            )


    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'Ingresa Nombre'
        self.fields['last_name'].widget.attrs['placeholder'] = 'Ingresa Apellido'
        self.fields['email'].widget.attrs['placeholder'] = 'Ingresa Correo Electrónico'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Ingresa Teléfono'
        self.fields['password'].widget.attrs['placeholder'] = 'Ingresa Contraseña'
        self.fields['confirm_password'].widget.attrs['placeholder'] = 'Confirmar Contraseña'

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class UserForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['first_name', 'last_name', 'phone_number']

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class UserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False, error_messages={'invalid': "Seleccione una imagen válida. Los archivos deben estar en formato JPEG, PNG o GIF."}, widget=forms.FileInput)
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'address_line_1', 'address_line_2', 'city', 'state', 'zip_code']

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
