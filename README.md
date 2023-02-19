# README #

This README would normally document whatever steps are necessary to get your application up and running.

## Description ##

This application is the base for all our django projects. It contains the core functionality that is required for any project (eg: Authentication, Logging, User management, Goup management, Authorization, Forgot password, Confirmation, ...etc).


## Set up ##
* Add `path("ekadmin/", include("lava.urls")),` to your project's `urls.py`.
* Add `"lava.middleware.MaintenanceModeMiddleware"` to your `MIDDLEWARE`s list
* Add the following to your `INSTALLED_APPS`: 
```
    "rest_framework",
    "rest_framework.authtoken",
    "djoser",
    "corsheaders",
```
* Add 
```'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
```
to your `MIDDLEWARE`s list.
* Add the following to your DRF settings:
```REST_FRAMEWORK = {
    # other settings
    "EXCEPTION_HANDLER": "lava.exceptions.lava_drf_exception_handler"
}```
* Add the following settings to your settings file:
```
CORS_ALLOWED_ORIGINS = [
    # "https://ekblocks.com",
    # "https://example.com",
    # "http://localhost:8000",
    # "http://127.0.0.1:9431",
]
CORS_ALLOW_ALL_ORIGINS = True


```


### 1. Configuration ###
  * Add the following to your project's `settings.py` file:
```python

EXPOSED_URL = "/exposed/"
EXPOSED_ROOT = os.path.join(BASE_DIR, "exposed")

LOG_ROOT = os.path.join(BASE_DIR, "log")
TMP_ROOT = os.path.join(BASE_DIR, "tmp")

# Maintenance mode
MAINTENANCE_MODE = int(os.environ.get("IPC_MAINTENANCE_MODE", 0))
MAINTENANCE_BYPASS_QUERY = os.environ.get(
    "MAINTENANCE_BYPASS_QUERY", "bypass_password=ekadmin_pass"
)

AUTH_USER_MODEL = "lava.User"

AUTHENTICATION_BACKENDS = ['lava.backends.EmailOrUsernameAuthenticationBackend']

FILE_PATTERNS = {
    '*.html': 'django',
    '*.txt': 'django',
    '*.js': 'javascript',
    '*.py': 'gettext',
}

```
### 2. Dependencies ###
```shell
    pip install django==3.2
```
### Tests ###
### Deployment ###

### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###
[EKBlocks](https://www.ekblocks.com)
