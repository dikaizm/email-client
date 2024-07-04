from django import forms

class LoginForm(forms.Form):
    fullname = forms.CharField(required=False)  # Optional, only needed for new registrations
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)
    confirm_password = forms.CharField(widget=forms.PasswordInput, required=False)  # Only needed for registration
