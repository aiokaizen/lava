# README #

This README would normally document whatever steps are necessary to get your application up and running.

## Description ##

This application is the base for all our django projects. It contains the core functionality that is required for any project (eg: Authentication, Logging, User management, Goup management, Authorization, Forgot password, Confirmation, ...etc).


## Set up ##

### 1. Configuration ###
  * Add the following settings to your project's settings.py:
```python

    AUTHENTICATION_BACKENDS = ['lava.backends.EmailOrUsernameAuthenticationBackend']
    
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
