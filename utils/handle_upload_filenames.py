import os

from lava.utils.utils import slugify, mask_number


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


def get_conversation_logo_filename(instance, filename):
    ext = filename.split(".")[-1]
    return f"chat/conversations/{instance.id}/logo.{ext}"


def get_chat_message_image_filename(instance, filename):
    ext = filename.split(".")[-1]
    now = timezone.now().strftime("%Y%m%d%H%M%S%z")
    return f"chat/conversations/{instance.conversation.id}/messages/{instance.id}_{now}.{ext}"


def get_document_filename(instance, filename):
    filename, ext = os.path.splitext(filename)
    return f"documents/{slugify(filename)}{ext}"


def get_backup_file_filename(instance, filename):
    return "backup/{}".format(instance.get_filename())
