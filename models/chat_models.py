from datetime import timedelta

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from lava.error_codes import REQUIRED_ERROR_CODE
from lava.models import User, BaseModel
from lava.utils.utils import (
    Result, get_conversation_logo_filename, get_chat_message_image_filename
)
from lava import settings as lava_settings


class Conversation(BaseModel):

    class Meta(BaseModel.Meta):
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")
        ordering = ('-pinned_at', '-messages__created_at')

    name = models.CharField(_("Name"), max_length=100, blank=True)
    is_group_conversation = models.BooleanField(_("Group conversation"), default=False)
    # @TODO: Use ThumbnailerImageField instead
    logo = models.ImageField(
        _("Logo"), null=True, blank=True, upload_to=get_conversation_logo_filename
    )
    # Format: {
    #   "<id>": {
    #       "muted": False,
    #       "unmute_at": None
    #       "joined_at": Timezone.now(),
    #   }, ...
    # }
    members = models.JSONField(_("Members"), default=dict)
    pinned_at = models.DateTimeField(_("Pinned at"), null=True, blank=True)

    def __str__(self):
        return self.name

    def get_members(self):
        return User.objects.filter(pk__in=self.members.keys())

    def get_recipient(self, current_user):
        if self.is_group_conversation:
            return None

        return self.get_members().exclude(pk=current_user.pk).first()

    def get_name(self, current_user):
        return self.name if self.is_group_conversation else \
            self.get_recipient(current_user).full_name

    def get_logo(self, current_user):
        return self.logo if self.is_group_conversation else \
            self.get_recipient(current_user).photo

    def get_unread_messages(self, user):
        return self.messages.all().exclude(
            Q(read_by__has_key=str(user.id)) | Q(sender=user)
        )

    def create(self, user, members=None, *args, **kwargs):
        members = members or []
        self.add_members(members=[*members, user], save=False)

        if not self.name and self.is_group_conversation:
            msg = _("This field is mandatory")
            return Result.error(msg, errors={
                "name": [msg]
            }, error_code=REQUIRED_ERROR_CODE)

        if not self.is_group_conversation:
            recepient = self.get_members().exclude(user=user).first()
            self.name = user.full_name + ' & ' + recepient.full_name
        return super().create(user, *args, **kwargs)

    def mark_as_read(self, user):
        for message in self.get_unread_messages(user):
            result = message.mark_as_read(user)
        return Result.success(_("Conversation has been marked as read."))

    def add_members(self, members, save=True):
        if not members:
            return Result.warning(_("New members list is empty!"))

        if type(members) not in [list, tuple]:
            members = [members]

        now = timezone.now().strftime("%Y-%m-%d %H:%M:%S %z")
        for member in members:
            self.members[str(member.id)] = {
                "muted": False,
                "unmute_at": None,
                "joined_at": now
            }

        if save:
            return self.update(update_fields=['members'])

        return Result.success()

    def pin_conversation(self):
        self.pinned_at = timezone.now()
        return self.update(update_fields=['pinned_at'])

    def mute_for_user(self, user, period : tuple =None):
        if not str(user.id) in self.members.keys():
            return Result.error(_("This user is not part of the conversation."))

        self.members[str(user.id)]["muted"] = True
        if period:
            now = timezone.now()
            time_unit, n = period[0], int(period[1])
            if time_unit in lava_settings.TIMEUNIT_CHOICES:
                period = timedelta(**{f"{time_unit}": n})
                self.members[str(user.id)]["unmute_at"] = (
                    now + period
                ).strftime("%Y-%m-%d %H:%M:%S %z")

        self.save(update_fields=["members"])
        return Result.success(_("The conversation has been muted for this user"))

    def unmute_for_user(self, user):
        if not str(user.id) in self.members.keys():
            return Result.error(_("This user is not part of the conversation."))

        self.members[str(user.id)]["muted"] = False
        self.members[str(user.id)]["unmute_at"] = None
        self.save(update_fields=["members"])
        return Result.success(_("The conversation has been unmuted for this user"))

    @classmethod
    def get_user_unread_messages(cls, user):
        conversations = cls.get_user_conversations(user)
        messages = ChatMessage.objects.filter(
            conversation__in=conversations
        ).exclude(
            Q(read_by__has_key=str(user.id)) | Q(sender=user)
        ).order_by('-created_at')
        return messages

    @classmethod
    def get_user_conversations(cls, user, trash=False, kwargs=None):
        return Conversation.filter(user, trash, kwargs).filter(
            members__has_key=str(user.id)
        )


class ChatMessage(BaseModel):

    class Meta(BaseModel.Meta):
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        ordering = ('created_at', )

    sender = models.ForeignKey(
        User, verbose_name=_("Sender"), related_name='sent_messages',
        on_delete=models.CASCADE
    )
    conversation = models.ForeignKey(
        Conversation, verbose_name=_("Conversation"), related_name='messages',
        on_delete=models.CASCADE
    )
    text = models.TextField(_("Text"), blank=True)
    # @TODO: Use ThumbnailerImageField instead
    image = models.ImageField(
        _("Image"), null=True, blank=True, upload_to=get_chat_message_image_filename
    )
    type = models.CharField(
        _("Message type"), default='email', choices=lava_settings.CHAT_MESSAGE_CHOICES,
        max_length=32
    )
    read_by = models.JSONField(_("Read by"), default=dict)

    def __str__(self):
        return self.text

    def create(self, user, *args, **kwargs):
        if not self.text and not self.image:
            return Result.error(_("You can't send an empty message."))

        if str(user.id) not in self.conversation.members.keys():
            return Result.error(_("You can not send messages to this conversation!"))

        return super().create(user, *args, **kwargs)

    def mark_as_read(self, user):
        if user.id not in self.read_by:
            self.read_by[user.id] = timezone.now().strftime("%Y-%m-%d %H:%M:%S %z")
            self.save()

        return Result.success(_("Message has been marked as read."))

    def is_read_by(self, user):
        return user.id in self.read_by

    @classmethod
    def get_unread_messages_for_user(cls, user):
        return ChatMessage.objects.exclude(read_by__has_key=str(user.id))
