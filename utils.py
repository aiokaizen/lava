import os
from datetime import datetime

from django.conf import settings


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


# Othr things
def get_log_filepath():
    now = datetime.now()
    current_hour = now.strftime("%Y%m%d_%H")
    filename = f"{current_hour}.log"
    filepath = os.path.join(settings.LOG_ROOT, filename)
    if not os.path.exists(settings.LOG_ROOT):
        os.makedirs(settings.LOG_ROOT)
    return filepath
