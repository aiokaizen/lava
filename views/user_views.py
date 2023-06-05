from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls.base import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views import View

from lava.forms.user_forms import UserFilterForm
from lava.models import User


class UserListView(View):

    filter_form_class = UserFilterForm
    model_class = User
    template_name = 'lava/users/user-list.html'
    page_id = 'user_list'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self, request):
        return self.model_class.filter(kwargs=request.GET)

    def get(self, request, *args, **kwargs):
        filter_form = self.filter_form_class(data=request.GET)
        queryset = self.get_queryset(request)
        context = {
            'page_breadcrumb_id': self.page_id,
            'queryset': queryset,
            'filter_form': filter_form
        }
        return render(request, self.template_name, context)
