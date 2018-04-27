from django.utils.translation import ugettext_lazy as _
from captcha.fields import CaptchaField

from allauth.account.forms import SignupForm as AllAuthSignupForm
from django import forms

class SignupForm(AllAuthSignupForm):

    captcha = CaptchaField(label=_("Captcha"))

# class RegisterForm(forms.Form):
#     # 不能为空
#     email = forms.EmailField(required=True)
#     password = forms.CharField(required=True, min_length=6,max_length=20)
#     # 出错信息
#     captcha = CaptchaField(error_messages={"invalid":u"验证码错误"})