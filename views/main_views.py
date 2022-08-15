import json
from django.views import View
import requests

from django.contrib import messages
from django.contrib.auth.forms import SetPasswordForm
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _


def home(request):
    context = {

    }
    return render(request, 'lava/home.html', context)


def activate_user(request, uid, token):
    protocol = 'https://' if request.is_secure() else 'http://'
    web_url = protocol + request.get_host()
    post_url = web_url + "/auth/users/activation/"
    post_data = {'uid': uid, 'token': token}
    result = requests.post(post_url, data = post_data)

    try:
        content = json.loads(result.text)
    except Exception as e:
        content = {'details': str(e)}
    context = {
        'status': 'success' if result.status_code == 204 else 'error',
        'content': content.get('detail', ''),
    }
    return render(request, 'lava/users/activation.html', context)


class ResetPasswordConfirm(View):

    def get(self, request, uid, token):
        form = SetPasswordForm(user=None)
        return render(request, 'lava/users/change_password.html', context={
            'success': False,
            'form': form
        })

    def post(self, request, uid, token):
        protocol = 'https://' if request.is_secure() else 'http://'
        web_url = protocol + request.get_host()
        post_url = web_url + "/auth/users/reset_password_confirm/"

        form = SetPasswordForm(user=None, data=request.POST, files=request.FILES)
        if not form.is_valid():
            return render(request, 'lava/users/change_password.html', {
                'success': False,
                "form": form,
            })

        payload = {
            'uid': uid,
            'token': token,
            'new_password': form.cleaned_data.get('new_password1'),
            're_new_password': form.cleaned_data.get('new_password2')
        }
        result = requests.post(post_url, data=payload)
        if result.ok:  # Success
            context = {
                'success': True,
            }
        else:
            errors = result.json()
            html_errors = "<ul class=\"pl-3\">"
            for field, error in errors.items():
                html_errors += f"<li><b>{field}:</b> {error[0]}</li>"
            html_errors += "</ul>"
            messages.error(request, html_errors)
            context = {
                'success': False,
            }
        return render(request, 'lava/users/change_password.html', context)
