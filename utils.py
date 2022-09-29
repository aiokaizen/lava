import os
import random
import logging
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from templated_mail.mail import BaseEmailMessage

import firebase_admin
from firebase_admin import credentials

from lava import settings as lava_settings

class imdict(dict):
    """ Immutable dictionary. """
    def __hash__(self):
        return id(self)

    def _immutable(self, *args, **kws):
        raise TypeError('This object is immutable')

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear       = _immutable
    update      = _immutable
    setdefault  = _immutable
    pop         = _immutable
    popitem     = _immutable


class odict(dict):
    """
    A dictionnary that supports the '.' syntax for its members.
    ex:
    >>> user = odict(username="janedoe", password="secret_pass")
    >>> user.username
    janedoe
    >>> user['password']
    secret_pass
    """
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)


class Result(imdict):
    """
    An immutable Result object representing
    both Success and Error results from functions and APIs.
    """

    def __init__(self, success:bool, message:str='', instance=None, errors:dict=None, tag:str=None):
        self.success = success
        self.message = message
        self.instance = instance
        self.tag = tag
        if not self.tag:
            self.tag = 'success' if success else 'error'
        self.errors = errors
        dict.__init__(self, success=success, message=message, errors=errors)
    
    @classmethod
    def from_dict(cls, result_dict):
        if "success" not in result_dict or "message" not in result_dict:
            raise TypeError()

        return cls(
            result_dict["success"],
            result_dict["message"],
            result_dict.get("instance", None),
            result_dict.get("errors", None),
            result_dict.get("tag", None),
        )
    
    def to_dict(self):
        res_dict = {
            "success": self.success,
            "tag": self.tag,
            "message": self.message
        }
        if not self.success:
            res_dict["errors"] = self.errors or []
        return res_dict


def mask_number(n):
    """ This function disguises an ID before using it in a public context. """
    if isinstance(n, int):
        return n + 747251
    return n

def unmask_number(mask):
    if isinstance(mask, int):
        return mask - 747251
    return mask

# Handle Uploaded file names
def get_user_cover_filename(instance, filename):
    ext = filename.split('.')[-1]
    folder = "user/{}".format(mask_number(instance.id))
    return '{}/cover_picture.{}'.format(folder, ext)

def get_user_photo_filename(instance, filename):
    ext = filename.split('.')[-1]
    folder = "user/{}".format(mask_number(instance.id))
    return '{}/profile_picture.{}'.format(folder, ext)

def handle_excel_file(file, start_row=1, extract_columns=[]):
    """
    file | File like object: The file to extract data from.
    start_row | int: the number of row where the header of the file is located.
    extract_columns | List of strings: the names of columns to extract from the file.
    The extract_columns param will be slugified as well as the columns from the excel file,
    so caps, spaces, and special characters are ignored making it easier to match.

    example:
    >>> with read('file.xlsx', 'r') as f:
    >>>     start_row = 3
    >>>     column_names = [
    >>>         "name", "age", "address"
    >>>     ]
    >>>     data = handle_excel_file(f, start_row, column_names)
    """
    extract_columns = [
        slugify(name) for name in extract_columns
    ] if extract_columns else None

    column_names = []  # This list will be extracted from the file and then slugified.

    for column_name in extract_columns:
        if column_name not in column_names:
            raise ValidationError(_("The uploaded file does not contain `email` column."))

    # return odict object with the following format:
    # {
    #   'column_names': ['name', 'age', 'email'],
    #   'column_names_display': ['Name', 'Age', 'Email'],
    #   'data': [
    #       odict({"name": "Albert", "age": 39, "email": "albert@mail.com"}),
    #       odict({"name": "Emily", "age": 26, "email": "emily@mail.com"}),
    #   ],
    # }
    result = odict()

    return file


def send_html_email(request, template, recipients, sender=None, context={}, fail_silently=False):

    email = BaseEmailMessage(
        request, context=context, template_name=template
    )

    email.send(
        to=recipients,
        from_email=sender,
        fail_silently=fail_silently
    )

# Othr things
def get_log_filepath():
    now = datetime.now()
    current_hour = now.strftime("%Y%m%d_%H")
    filename = f"{current_hour}.log"
    filepath = os.path.join(settings.LOG_ROOT, filename)
    if not os.path.exists(settings.LOG_ROOT):
        os.makedirs(settings.LOG_ROOT)
    return filepath


def generate_password(length=8, include_special_characters=True):
    lower_alphabets = 'abcdefghijklmnopqrstuvwxyz'
    upper_alphabets = lower_alphabets.upper()
    numbers = '1234567890'
    special_characters = '-_!?.^*@#$%'
    pool = lower_alphabets + upper_alphabets + numbers
    if include_special_characters:
        pool += special_characters
    
    random_password = ''.join(random.SystemRandom().choices(pool, k=length))
    return random_password


def generate_username(email="", first_name="", last_name=""):
    """ Geneartes a random username from user data. """
    if email:
        username = email.split('@')[0]
        if _is_username_valid(username):
            return username

    if first_name:
        username = slugify(first_name, separator='')
        if last_name:
            username += f".{slugify(last_name, separator='')}"
        if _is_username_valid(username):
            return username
    
    while True:
        suffix = ''.join(random.SystemRandom().choices('1234567890', k=5))
        username = f"controller_{suffix}"
        if _is_username_valid(username):
            return username


def _is_username_valid(username):
    from lava.models import User
    try:
        User.objects.get(username=username)
        return False
    except User.DoesNotExist:
        return True


def init_firebase():
    creds_file_path = lava_settings.FIREBASE_CREDENTIALS_FILE_PATH
    if not os.path.exists(creds_file_path):
        logging.error("Firebase credentials file does not exist.")
        return Result(False, _("Firebase credentials file does not exist."))

    try:
        creds = credentials.Certificate(creds_file_path)
        print('creds:', creds)
        # cred = credentials.RefreshToken(creds_file_path)
        default_app = firebase_admin.initialize_app(creds)
        print('app name:', default_app.name)
        return Result(True)
    except Exception as e:
        logging.error(e)
        return Result(False, str(e))
