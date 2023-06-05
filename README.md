# README #

This README would normally document whatever steps are necessary to get your application up and running.
<br>
<br>

## Description ##

This application is the base for all our django projects. It contains the core functionality that is required for any project (eg: Authentication, Logging, User management, Goup management, Authorization, Forgot password, Confirmation, ...etc).
<br>
<br>

## Set up & Configuration ##
Clone Lava repository from remote to your project directory:
```shell
/project/root$ git clone git@bitbucket.org:username/lava.git
```
Add the following urls to your project's `urls.py` urlpatterns.
```python
    path("ekadmin/", include("lava.urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.authtoken")),
```

Add the following code to the end of your project `urls.py` file:
```python
from django.conf.urls.static import static

if settings.DEBUG is True:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.EXPOSED_URL, document_root=settings.EXPOSED_ROOT
    )
```
Add the following code to the bottom of your project settings file, right above local_settings:
```python
try:
    from lava.project_settings import *
except ImportError:
    pass
```
<br>
<br>

## Dependencies ##
Install all the dependancies from `requirements.txt` file using the following command:
```shell
/project/root$ pip install -r lava/requirements.txt
```
<br>
<br>

## Testing ##
<br>
<br>

## Deployment ##
<br>
<br>

## Contribution guidelines ##
* Writing tests
* Code review
* Other guidelines
<br>
<br>

## Who do I talk to? ##
Send all your questions and thoughts to: [EKBlocks](https://www.ekblocks.com)
