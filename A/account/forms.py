from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .captcha import validate_login_captcha
from .models import Profile


class UserRegistrationForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'your username'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'your email'}))
    password1 = forms.CharField(label='password', widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'your password'}))
    password2 = forms.CharField(label='confirm password', widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'your password'}))

    def clean_email(self):
        email = self.cleaned_data['email']
        user = User.objects.filter(email=email).exists()
        if user:
            raise ValidationError('this email already exist')
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        user = User.objects.filter(username=username).exists()
        if user:
            raise ValidationError('this username is already exist')
        return username

    def clean(self):
        cd = super().clean()
        p1 = cd.get('password1')
        p2 = cd.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError('password must match')


class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'وارد کردن نام کاربری الزامی است.'}
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        error_messages={'required': 'وارد کردن رمز عبور الزامی است.'}
    )
    captcha_answer = forms.IntegerField(
        min_value=0,
        max_value=20,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'پاسخ کپچا'}),
        error_messages={
            'required': 'پاسخ کپچا را وارد کن.',
            'invalid': 'پاسخ کپچا باید عدد باشد.',
            'min_value': 'پاسخ کپچا نمی‌تواند کمتر از ۰ باشد.',
            'max_value': 'پاسخ کپچا نمی‌تواند بیشتر از ۲۰ باشد.',
        }
    )

    def __init__(self, *args, captcha_payload=None, **kwargs):
        self.captcha_payload = captcha_payload
        super().__init__(*args, **kwargs)

    def clean(self):
        cd = super().clean()
        typed_answer = cd.get('captcha_answer')
        if typed_answer is None:
            return cd
        submitted_token = self.data.get('captcha_token')
        is_valid, error_message = validate_login_captcha(self.captcha_payload, submitted_token, typed_answer)
        if not is_valid:
            raise ValidationError(error_message)
        return cd


class EditUserForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = Profile
        fields = ('age', 'bio')
