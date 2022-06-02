from django.shortcuts import render

# Create your views here.
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

