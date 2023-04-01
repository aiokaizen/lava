from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from lava.models import ChatMessage, Conversation
from lava.models.models import User
from lava.serializers.base_serializers import BaseModelSerializer, ReadOnlyBaseModelSerializer
from lava.serializers import UserExerptSerializer
from lava.utils import humanize_datetime


class MessageListSerializer(ReadOnlyBaseModelSerializer):

    sender = serializers.SerializerMethodField()
    datetime = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            'sender',
            'conversation',
            'text',
            'image',
            'avatar',
            'type',
            'datetime',
        ]

    def get_sender(self, instance):
        return instance.sender.full_name

    def get_avatar(self, instance):
        url = instance.sender.photo.url if instance.sender.photo else ''
        request = self.context.get('request', None)
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def get_datetime(self, instance):
        return humanize_datetime(instance.created_at)


class ConversationMessageListSerializer(MessageListSerializer):

    class Meta:
        model = ChatMessage
        fields = [
            "id",
            'sender',
            'text',
            'image',
            'avatar',
            'type',
            'read_by',
            'datetime',
        ]

    def get_sender(self, instance):
        return 'me' if instance.sender.id == self.user.id else 'opposite'


class ConversationListSerializer(ReadOnlyBaseModelSerializer):

    latest_message = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()
    unread = serializers.SerializerMethodField()
    datetime = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "name",
            'is_group_conversation',
            'logo',
            'latest_message',
            'unread',
            'members',
            'datetime',
            'pinned_at',
        ]

    def get_name(self, instance):
        return instance.get_name(self.user)

    def get_logo(self, instance):
        url = instance.get_logo(self.user).url
        request = self.context.get('request', None)
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def get_members(self, instance):
        members = instance.get_members().exclude(user=self.user)
        serializer = UserExerptSerializer(members, many=True)
        return serializer.data

    def get_latest_message(self, instance):
        message = instance.messages.last()
        if message:
            serializer = ConversationMessageListSerializer(message, user=self.user)
            return serializer.data
        return None

    def get_unread(self, instance):
        return instance.get_unread_messages(self.user).count()

    def get_datetime(self, instance):
        latest_message = instance.messages.first()
        if latest_message:
            return humanize_datetime(latest_message.created_at)
        return None


class ConversationGetSerializer(ReadOnlyBaseModelSerializer):

    messages = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    logo = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "name",
            'is_group_conversation',
            'logo',
            'messages',
            'members',
            'pinned_at',
        ]

    def get_name(self, instance):
        return instance.get_name(self.user)

    def get_logo(self, instance):
        url = instance.get_logo(self.user).url
        request = self.context.get('request', None)
        if request is not None:
            return request.build_absolute_uri(url)
        return url

    def get_messages(self, instance):
        messages = instance.messages
        serializer = ConversationMessageListSerializer(messages, user=self.user, many=True, context=self.context)
        return serializer.data

    def get_members(self, instance):
        members = instance.get_members().exclude(user=self.user)
        serializer = UserExerptSerializer(members, many=True)
        return serializer.data


class ConversationCreateUpdateSerializer(BaseModelSerializer):

    class Meta:
        model = Conversation
        fields = [
            "name",
            'is_group_conversation',
            'logo',
            'members',
        ]

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        members = validated_data.pop('members', None)
        try:
            self.members = User.objects.filter(pk__in=members)
            if self.members.count() < len(members):
                raise serializers.ValidationError({
                    "members": [_("Some member IDs are not valid.")]
                })
        except ValueError:
            raise serializers.ValidationError({
                "members": [_("Member IDs must be integers.")]
            })
        return validated_data

    def create(self, validated_data):
        return super().create(validated_data, members=self.members)
