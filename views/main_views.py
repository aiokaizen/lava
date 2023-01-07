import json
import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth import (
    login as auth_login, logout as do_logout
)
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import resolve_url, render, redirect, HttpResponseRedirect
from django.urls.base import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.http import HttpResponse

from lava.forms import LoginForm, SignupForm


class Home(View):

    template_name = "lava/home.html"
    page_id = 'home'

    def get_permissions(self, request):
        pass 

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        context = {
            'page_breadcrumb_id': self.page_id,
        }
        return render(request, self.template_name, context)


class Login(View):

    form_class = LoginForm
    initial = {}
    template_name = 'lava/login.html'
    page_id = 'login'
    authentication_form = None
    redirect_authenticated_user = False
    extra_context = None
    redirect_field_name = 'next'

    def get_redirect_url(self):
        """Return the user-originating redirect URL if it's safe."""
        redirect_to = self.request.POST.get(
            self.redirect_field_name,
            self.request.GET.get(self.redirect_field_name, '')
        )
        print('redirect url:', redirect_to)
        url_is_safe = True  # self.request.is_secure()
        return redirect_to if url_is_safe else ''

    def get_success_url(self):
        url = self.get_redirect_url()
        return url or resolve_url(settings.LOGIN_REDIRECT_URL or 'lava:home')

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if self.redirect_authenticated_user and self.request.user.is_authenticated:
            redirect_to = self.get_success_url()
            if redirect_to == self.request.path:
                raise ValueError(
                    "Redirection loop for authenticated user detected. Check that "
                    "your LOGIN_REDIRECT_URL doesn't point to a login page."
                )
            return HttpResponseRedirect(redirect_to)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(request=request, initial=self.initial)
        context = {
            'page_breadcrumb_id': self.page_id,
            'form': form
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request=request, data=request.POST)
        if form.is_valid():
            auth_login(self.request, form.get_user())
            return HttpResponseRedirect(self.get_success_url())

        context = {
            'page_breadcrumb_id': self.page_id,
            'form': form
        }
        return render(request, self.template_name, context)


class Signup(View):

    form_class = SignupForm
    initial = {}
    template_name = 'lava/signup.html'
    page_id = 'signup'

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        context = {
            'page_breadcrumb_id': self.page_id,
            'form': form
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            # Create a new user
            return redirect(reverse('lava:login'))

        context = {
            'page_breadcrumb_id': self.page_id,
            'form': form
        }
        return render(request, self.template_name, context)


class ResetPassword(View):

    def get(self, request):
        return redirect(reverse('lava:home'))


@login_required
def logout(request):
    do_logout(request)
    return redirect(reverse('lava:home'))


def activate_user(request, uid, token):
    protocol = "https://" if request.is_secure() else "http://"
    web_url = protocol + request.get_host()
    post_url = web_url + "/auth/users/activation/"
    post_data = {"uid": uid, "token": token}
    result = requests.post(post_url, data=post_data)

    try:
        content = json.loads(result.text)
    except Exception as e:
        content = {"details": str(e)}
    context = {
        "status": "success" if result.status_code == 204 else "error",
        "content": content.get("detail", ""),
    }
    return render(request, "lava/users/activation.html", context)


class ResetPasswordConfirm(View):

    def get(self, request, uid, token):
        form = SetPasswordForm(user=None)
        return render(
            request,
            "lava/users/change_password.html",
            context={"success": False, "form": form},
        )

    def post(self, request, uid, token):
        protocol = "https://" if request.is_secure() else "http://"
        web_url = protocol + request.get_host()
        post_url = web_url + "/auth/users/reset_password_confirm/"

        form = SetPasswordForm(user=None, data=request.POST, files=request.FILES)
        if not form.is_valid():
            return render(
                request,
                "lava/users/change_password.html",
                {
                    "success": False,
                    "form": form,
                },
            )

        payload = {
            "uid": uid,
            "token": token,
            "new_password": form.cleaned_data.get("new_password1"),
            "re_new_password": form.cleaned_data.get("new_password2"),
        }
        result = requests.post(post_url, data=payload)
        if result.ok:  # Success
            context = {
                "success": True,
            }
        else:
            errors = result.json()
            html_errors = '<ul class="pl-3">'
            for field, error in errors.items():
                html_errors += f"<li><b>{field}:</b> {error[0]}</li>"
            html_errors += "</ul>"
            messages.error(request, html_errors)
            context = {
                "success": False,
            }
        return render(request, "lava/users/change_password.html", context)


class Notifications(View):

    def get(self, request):
        return HttpResponse("<h2>Notifications</h2>")
