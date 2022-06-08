import json
import requests

from django.shortcuts import render


def home(request):
    context = {

    }
    return render(request, 'users/home.html', context)


def user_list(request):
    context = {

    }
    return render(request, 'users/user_list.html', context)


def user_add(request):
    context = {

    }
    return render(request, 'users/user_add.html', context)


def user_details(request, pk):
    context = {

    }
    return render(request, 'users/user_details.html', context)


def user_change(request, pk):
    context = {

    }
    return render(request, 'users/user_change.html', context)


def user_change_pwd(request, pk):
    context = {

    }
    return render(request, 'users/user_change_pwd.html', context)


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


def reset_pwd_confirm(request, uid, token):
    protocol = 'https://' if request.is_secure() else 'http://'
    web_url = protocol + request.get_host()
    post_url = web_url + "/auth/users/password/reset/confirm/"
    post_data = {'uid': uid, 'token': token}
    result = requests.post(post_url, data = post_data)
    content = result.text
    context = {
        'content': content,
    }
    return render(request, 'lava/users/pwd_confirm.html', context)
