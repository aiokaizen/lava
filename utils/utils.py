import os
import random
import logging
from io import BytesIO
from datetime import datetime, timedelta
import unicodedata
import zipfile
import subprocess
import re
import mimetypes

import requests

from PIL import Image as PILImage

from django.conf import settings
from django.core.files import File
from django.core.files.base import ContentFile
from django.utils import timezone
from django.utils.text import slugify as base_slugify
from django.utils.translation import gettext_lazy as _
from django.core.mail import get_connection, EmailMultiAlternatives
from django.template.context import make_context
from django.template.loader import render_to_string

from templated_mail.mail import BaseEmailMessage

from lava.exceptions import LavaBaseException

from lava import settings as lava_settings


def slugify(value, allow_unicode=False, separator='_'):
    result = base_slugify(value, allow_unicode).replace('-', separator)
    return result


class imdict(dict):
    """Immutable dictionary."""

    def __hash__(self):
        return id(self)

    def _immutable(self, *args, **kws):
        raise TypeError("This object is immutable")

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    update = _immutable
    setdefault = _immutable
    pop = _immutable
    popitem = _immutable


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

    def __setitem__(self, __key, __value):
        key = slugify(__key).replace('-', '_')
        setattr(self, key, __value)
        return super().__setitem__(__key, __value)


def strtobool(val:str):
    """Convert a string representation of truth to true (1) or false (0).
    True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
    are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
    'val' is anything else.
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    elif val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    else:
        raise ValueError(_("invalid truth value %r") % (val,))


def humanize_datetime(datetime):
    now = timezone.now()
    if now.date() == datetime.date():
        return datetime.strftime("%H:%M")
        # return f"{(now - datetime).seconds()}s ago"
    elif (now - datetime) < timedelta(days=360):
        return datetime.strftime("%B, %d")

    return  datetime.strftime("%Y/%m/%d")


def contains_arabic_chars(val:str):
    """
    Returns True if the string in the argument contains any arabic characters.
    Otherwise, it returns False
    """
    for c in val:
        unicode_name = unicodedata.name(c).lower()
        if 'arabic' in unicode_name:
            return True

    return False


def get_tmp_root(dirname=None):
    tmp_root = lava_settings.TMP_ROOT
    tmp_root = os.path.join(tmp_root, dirname) if dirname else tmp_root
    if not os.path.exists(tmp_root):
        os.makedirs(tmp_root)
    return tmp_root


def get_log_root(dirname=None):
    log_root = lava_settings.LOG_ROOT
    log_root = os.path.join(log_root, dirname) if dirname else log_root
    if not os.path.exists(log_root):
        os.makedirs(log_root)
    return log_root


class Result(imdict):
    """
    An immutable Result object representing
    both Success and Error results from functions and APIs.
    """

    def __init__(
        self,
        success: bool,
        message: str = "",
        instance: any = None,
        errors: dict = None,
        tag: str = None,
        error_code: str = "",
    ):
        self.success = success
        self.is_success = success
        self.message = message
        self.instance = instance
        self.tag = tag
        if not self.tag:
            self.tag = "success" if success else "error"
        self.is_error = True if self.tag == "error" else False
        self.is_warning = True if self.tag in ["warn", "warning"] else False
        self.errors = errors
        self.error_code = error_code
        dict.__init__(self, success=success, message=message, errors=errors)
        # logging.warning(
        #     "This method is deprecated. Please use a class methods instead:\n"
        #     "\tsuccess: Result.success('My success message')\n"
        #     "\twarning: Result.warning('My warning message')\n"
        #     "\terror  : Result.error('My error message')\n"
        # )

    @classmethod
    def success(self, message="", instance=None):
        return Result(True, message, instance=instance)

    @classmethod
    def warning(self, message="", instance=None):
        return Result(False, message, instance=instance, tag="warning")

    @classmethod
    def error(self, message="", instance=None, errors=None, error_code=""):
        return Result(
            False, message, instance=instance, errors=errors, error_code=error_code
        )

    @classmethod
    def from_dict(cls, result_dict):
        if (
            "result" not in result_dict or
            "message" not in result_dict or
            result_dict.get("class_name", "") != "lava.utils.Result"
        ):
            raise TypeError("Invalid result dict format.")

        tag = result_dict["result"]
        is_success = True if tag == "success" else False

        return cls(
            success=is_success,
            message=result_dict["message"],
            instance=result_dict.get("instance", None),
            errors=result_dict.get("errors", None),
            error_code=result_dict.get("error_code", None),
            tag=tag,
        )

    def to_dict(self):
        type = "success" if self.is_success else "error"
        if self.is_warning:
            type = "warning"

        res_dict = {
            "class_name": 'lava.utils.Result',
            "result": type,
            "message": str(self.message)
        }

        if not self.is_success:
            res_dict["errors"] = self.errors or []
            res_dict["error_code"] = self.error_code
        if self.instance:
            res_dict["object_id"] = self.instance.id
        return res_dict


def camelcase_to_snakecase(value):
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', value).lower()


def mask_number(n):
    """This function disguises an ID before using it in a public context."""
    if isinstance(n, int):
        return n + 747251
    return n


def unmask_number(mask):
    if isinstance(mask, int):
        return mask - 747251
    return mask


def map_interval(value, min1, max1, min2, max2):
    return (value - min1) / (max1 - min1) * (max2 - min2) + min2


# Handle Uploaded file names
def get_user_cover_filename(instance, filename):
    ext = filename.split(".")[-1]
    folder = "user/{}".format(mask_number(instance.id))
    return "{}/cover_picture.{}".format(folder, ext)


def get_user_photo_filename(instance, filename):
    ext = filename.split(".")[-1]
    folder = "user/{}".format(mask_number(instance.id))
    return "{}/profile_picture.{}".format(folder, ext)


def get_group_photo_filename(instance, filename):
    ext = filename.split(".")[-1]
    folder = "group/{}".format(instance.id)
    return "{}/photo.{}".format(folder, ext)


def get_entity_logo_filename(instance, filename):
    ext = filename.split(".")[-1]
    return f"entity/{slugify(instance.name)}/logo.{ext}"


def get_entity_logo_light_filename(instance, filename):
    ext = filename.split(".")[-1]
    return f"entity/{slugify(instance.name)}/logo_light.{ext}"


def get_person_image_filename(instance, filename):
    ext = filename.split(".")[-1]
    name = f"{instance.last_name}{instance.first_name}"
    return f"person/{slugify(name)}_picture.{ext}"


def get_model_file_from_io(filename, is_image=False):
    try:
        with open(filename, 'rb') as f:
            fname, ext = os.path.splitext(os.path.basename(filename))

            file_data = f.read()
            if is_image:
                file = PILImage.open(BytesIO(file_data))
            else:
                file = BytesIO(file_data)
            file_io = BytesIO()
            file.save(file_io, format=file.format)
            model_file = File(ContentFile(file_io.getvalue()))
            model_file.name = f"{fname}{ext}"
            return Result.success(instance=model_file)
    except Exception as e:
        return Result.error(str(e))


def get_model_file_from_url(url, is_image=False):
    retries_left = 3
    response = None
    e = None
    while retries_left >= 0:
        try:
            response = requests.get(url)
            e = None
            break
        except requests.exceptions.ConnectionError as error:
            logging.warning(
                "CONNECTION ERROR: Could not connect to the server. Retrying... "
                f"(Retries left: {retries_left}"
            )
            retries_left -= 1
            e = error

    if e:
        logging.error(
            "ABORT: Could not connect to the server, please check your internet connection."
        )

    if response.status_code == 200:
        try:
            filename = url.split('/')[-1].split('.')[0]
            filename = slugify(filename)
            content_type = response.headers['content-type']
            ext = mimetypes.guess_extension(content_type)
            if is_image:
                file = PILImage.open(BytesIO(response.content))
            else:
                file = BytesIO(response.content)
            file_io = BytesIO()
            file.save(file_io, format=file.format)
            model_file = File(ContentFile(file_io.getvalue()))
            model_file.name = f"{filename}{ext}"
            return Result.success(instance=model_file)
        except Exception as e:
            return Result.error(str(e))
    else:
        return Result.error(f"Response error {response.status_code}")


def get_backup_file_filename(instance, filename):
    return "backup/{}".format(instance.get_filename())


def get_or_create(klass, action_user=None, default_value=None, create_parmas=None, *args, **kwargs):
    try:
        instance = klass.objects.get(*args, **kwargs)
    except klass.DoesNotExist:
        default_value = default_value or {}
        create_parmas = create_parmas or {}
        instance = klass(**default_value)
        result = instance.create(user=action_user, **create_parmas)
        if not result:
            raise LavaBaseException(result)

    return instance


def send_html_email(
    request, template, recipients, sender=None, context=None, fail_silently=False
):

    email = BaseEmailMessage(request, context=context, template_name=template)

    email.send(to=recipients, from_email=sender, fail_silently=fail_silently)


def send_mass_html_email(
    request, template, subject, recipients, sender=None, context=None,
    user=None, password=None, fail_silently=False, connection=None, datatuple=None
):
    """
    Given a datatuple of (subject, text_content, html_content, from_email,
    recipient_list), sends each message to each recipient list. Returns the
    number of emails sent.

    If from_email is None, the DEFAULT_FROM_EMAIL setting is used.
    If auth_user and auth_password are set, they're used to log in.
    If auth_user is None, the EMAIL_HOST_USER setting is used.
    If auth_password is None, the EMAIL_HOST_PASSWORD setting is used.

    """
    connection = connection or get_connection(
        username=user, password=password, fail_silently=fail_silently
    )

    datatuple = datatuple or [
        (
            subject,
            "",
            render_to_string(
                template,
                make_context(
                    BaseEmailMessage(
                        request, context={**context, 'to': recipient}, template_name=template
                    ).get_context_data(),
                    request
                ).flatten()
            ),
            sender,
            recipient,
        ) for recipient in recipients
    ]

    messages = []

    for subject, text, html, from_email, recipient in datatuple:
        if type(recipient) not in [list, tuple]:
            recipient = (recipient, )
        message = EmailMultiAlternatives(subject, text, from_email, recipient)
        message.attach_alternative(html, "text/html")
        messages.append(message)

    return connection.send_messages(messages)


# Other things
def add_margin_to_image(pil_img, top, right, bottom, left, color):
    width, height = pil_img.size
    new_width = width + right + left
    new_height = height + top + bottom
    result = PILImage.new(pil_img.mode, (new_width, new_height), color)
    result.paste(pil_img, (left, top))
    return result


def get_image(image_path, target_width=None, target_height=None, margin=None, color="#00000000"):
    """ margin: tuple (top, right, bottom, left)"""

    image = PILImage.open(image_path)
    tmp_image_filename = os.path.join(get_tmp_root(), f"tmp_image.png")
    save_image = False

    if target_width and target_width != image.width:
        target_height = int(image.height * target_width / image.width)
        image = image.resize(size=(target_width, target_height))
        save_image = True

    elif target_height and target_height != image.height:
        target_width = int(image.width * target_height / image.height)
        image = image.resize(size=(target_width, target_width))
        save_image = True

    if margin:
        image = add_margin_to_image(image, *margin, color)
        save_image = True

    if save_image:
        image.save(tmp_image_filename)
        image.close()
        image = PILImage.open(tmp_image_filename)

    return image


def generate_password(length=8, include_special_characters=True):
    lower_alphabets = "abcdefghijklmnopqrstuvwxyz"
    upper_alphabets = lower_alphabets.upper()
    numbers = "1234567890"
    special_characters = "-_!?.^*@#$%"
    pool = lower_alphabets + upper_alphabets + numbers
    if include_special_characters:
        pool += special_characters

    random_password = "".join(random.SystemRandom().choices(pool, k=length))
    return random_password


def generate_username(email="", first_name="", last_name=""):
    """Geneartes a random username from user data."""
    if email:
        username = email.split("@")[0]
        if _is_username_valid(username):
            return username

    if first_name:
        username = slugify(first_name, separator="")
        if last_name:
            username += f".{slugify(last_name, separator='')}"
        if _is_username_valid(username):
            return username

    while True:
        suffix = "".join(random.SystemRandom().choices("1234567890", k=5))
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


def hex_to_rgb(hex_value:str):
    assert hex_value.startswith("#"), "Invalid color format, please enter a hex color value"
    hex_value = hex_value[1:]
    return tuple(int(hex_value[i:i + 2], 16) for i in (0, 2, 4))


def adjust_color(color, amount=0.5):
    """
    color:  str: rgb or hex color value
    amount: int: less than 0 => darker color, graiter than 0 => lighter color
    """

    rgb_color = color
    if color.startswith("#"):
        rgb_color = hex_to_rgb(color)

    r, g, b = rgb_color
    min_val = 0 if amount < 0 else 200
    max_val = 55 if amount < 0 else 255
    r = int(map_interval(r, 0, 255, min_val, max_val))
    g = int(map_interval(g, 0, 255, min_val, max_val))
    b = int(map_interval(b, 0, 255, min_val, max_val))
    return f"rgb({r}, {g}, {b})"


def path_is_parent(parent_path, child_path):
    parent_path = os.path.abspath(parent_path)
    child_path = os.path.abspath(child_path)
    return os.path.commonpath([parent_path]) == os.path.commonpath([parent_path, child_path])


def path_includes_dir(parent_path, dir_name):
    return (
        f"{os.sep}{dir_name}{os.sep}" in parent_path or
        parent_path.startswith(f"{dir_name}{os.sep}") or
        parent_path.endswith(f"{os.sep}{dir_name}")
    )


def zipdir(target_dir, output=None, mode='w', skip_dirs=None):
    """
        Zip all files in a directory located at target_dir.
        Outputs the zip into output our the parent directory.
    """

    if not skip_dirs:
        skip_dirs = []

    if not output:
        filename = f"{os.path.basename(target_dir)}.zip"
        output = os.path.join(os.path.dirname(target_dir), filename)

    with zipfile.ZipFile(output, mode, zipfile.ZIP_DEFLATED) as zipf:
        for root, _dirs, files in os.walk(target_dir):
            skip_root = False
            for skip_dir in skip_dirs:
                if path_includes_dir(root, skip_dir):
                    skip_root = True
                    break

            if skip_root:
                continue

            for file in files:
                zipf.write(
                    os.path.join(root, file),
                    os.path.relpath(
                        os.path.join(root, file),
                        os.path.join(target_dir, '..')
                    )
                )

    return output


def zipf(filename, output=None, ziph=None):
    """ Zip the file with the path filename into the output zip. """

    if not output:
        file_name, ext = os.path.splitext(filename)
        output = os.path.join(
            os.path.dirname(filename),
            f"{file_name}.zip"
        )

    output_parent_dir = os.path.dirname(output)

    try:
        zipf = ziph if ziph else zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED)
        zipf.write(
            filename,
            os.path.relpath(
                filename,
                os.path.join(output_parent_dir)
            )
        )
    finally:
        if not ziph:
            zipf.close()


def dump_pgdb(output_filename=None, db="default"):

    db_name = settings.DATABASES[db]["NAME"]
    username = settings.DATABASES[db]["USER"]
    password = settings.DATABASES[db]["PASSWORD"]
    host = settings.DATABASES[db]["HOST"]
    port = settings.DATABASES[db]["PORT"]
    port = f' -p {port}' if port else ''

    now = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = output_filename or f"{db_name}_backup_{now}.sql"

    with open(filename, 'w') as output:
        subprocess.Popen(
            [f"PGPASSWORD='{password}' pg_dump -h {host}{port} -U {username} {db_name}"],
            stdout=output,
            shell=True
        )
    return filename


def generate_requirements(out=None):

    base_dir = settings.BASE_DIR
    filename = out or os.path.join(base_dir, "all_requirements.txt")

    with open(filename, 'w') as output:
        process = subprocess.Popen(
            [f"pip freeze"],
            stdout=output,
            shell=True
        )
        process.wait()

    return filename
