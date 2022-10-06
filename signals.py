import os

from django.core.files.storage import default_storage
from django.db.models import FileField, signals

from lava.models import User


def post_delete_file_cleanup(sender, **kwargs):
    """
    File cleanup callback used to emulate the old delete
    behavior using signals. Initially django deleted linked
    files when an object containing a File/ImageField was deleted.

    Usage:
    >>> from django.db.models.signals import post_delete
    >>> post_delete.connect(
    >>>     post_delete_file_cleanup, sender=MyModel,
    >>>     dispatch_uid="myapp.mymodel.post_delete_file_cleanup"
    >>> )
    """
    instance = kwargs["instance"]
    for field in sender._meta.fields:

        if field and isinstance(field, FileField):
            fieldname = field.name
            f = getattr(instance, fieldname)
            m = instance.__class__._default_manager
            if (
                f
                and hasattr(f, "path")
                and os.path.exists(f.path)
                and not m.filter(
                    **{"%s__exact" % fieldname: getattr(instance, fieldname)}
                ).exclude(pk=instance._get_pk_val())
            ):
                try:
                    default_storage.delete(f.path)
                except:
                    pass


def pre_save_file_cleanup(sender, **kwargs):
    """
    Instance old file will be deleted from os.

    Usage:
    >>> from django.db.models.signals import pre_save
    >>> pre_save.connect(
    >>>     pre_save_file_cleanup, sender=MyModel,
    >>>     dispatch_uid="myapp.mymodel.pre_save_file_cleanup"
    >>> )
    """
    instance = kwargs["instance"]
    if not instance.pk:
        return

    for field in sender._meta.fields:

        if field and isinstance(field, FileField):
            fieldname = field.name
            manager = sender._default_manager
            old_inst = manager.get(id=instance.id)
            old_field = getattr(old_inst, fieldname)
            new_field = getattr(instance, fieldname)

            old_file = (
                old_field.path if old_field and hasattr(old_field, "path") else None
            )
            new_file = (
                new_field.path if new_field and hasattr(new_field, "path") else None
            )

            if (new_file and new_file != old_file) or (not new_file and old_file):
                try:
                    default_storage.delete(old_file)
                except:
                    pass


# Connecting signals
signals.post_delete.connect(
    post_delete_file_cleanup,
    sender=User,
    dispatch_uid="lava.User.post_delete_file_cleanup",
)
signals.pre_save.connect(
    pre_save_file_cleanup, sender=User, dispatch_uid="lava.User.pre_save_file_cleanup"
)
