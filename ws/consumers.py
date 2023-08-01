import json

from django.utils.translation import gettext_lazy as _
from django.conf import settings

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from lava.models.chat_models import ChatMessage, Conversation
from lava.models.models import Notification
from lava.utils import Result
from channels.layers import get_channel_layer


class BaseConsumer(AsyncWebsocketConsumer):

    async def prepare_connection(self):
        self.user = self.scope['user']

        headers = self.scope["headers"]
        media_protocol = 'https' if settings.DEBUG is False else 'http'

        self.base_url = None
        for key, value in headers:
            if key.decode() == 'host':
                self.base_url = f"{media_protocol}://{value.decode()}"

        if self.channel_layer:
            self.user_group_name = f'user_{self.user.id}'
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )

    async def connect(self):
        await self.prepare_connection()
        await self.accept()

    async def disconnect(self, close_code):
        # Clean up
        client_groups = self.channel_layer.groups.get(self.channel_name, set())
        for group_name in client_groups:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def get_group_member_count(group_name):
        group_status = await self.channel_layer.group_status(group_name)
        return group_status.get("channel_layer", {}).get("groups", {}).get(group_name, {}).get("channel_count", 0)


class ChatConsumer(BaseConsumer):

    async def connect(self):
        await super().prepare_connection()
        conversation_id = self.scope['url_route']['kwargs'].get('conversation_id', 0)
        if conversation_id:
            self.conversation = await database_sync_to_async(
                lambda : Conversation.objects.get(pk=conversation_id)
            )()
            members = await database_sync_to_async (
                list
            )(self.conversation.get_members())
            if self.user not in members:
                return await self.close()

            self.conversation_group_name = f'conversation_{conversation_id}'
            await self.channel_layer.group_add(
                self.conversation_group_name,
                self.channel_name
            )

        user_conversations = await database_sync_to_async(
            list
        )(Conversation.get_user_conversations(self.user).exclude(id=conversation_id))

        for conversation in user_conversations:
            conversation_group_name = f'conversation_{conversation.id}'
            await self.channel_layer.group_add(
                conversation_group_name,
                self.channel_name
            )
        await self.accept()

    async def receive(self, text_data):
        if not text_data:
            return
        data = json.loads(text_data)
        action = data.get('action')
        if action == 'send_message':
            await self.send_message(data)
        elif action == 'mark_message_as_read':
            await self.mark_as_read(data)

    async def send_message(self, data):
        user = self.user

        message = ChatMessage(
            sender=user,
            type=data.get('type', ''),
            text=data.get('text', ''),
            conversation=self.conversation
        )
        image = data.get('image', None)
        result = await database_sync_to_async(
            message.create
        )(user=user, file_fields=(("image", image), ) if image else None)
        if result.is_error:
            await self.send({
                'type': 'error_message',
                'error': result.to_dict()
            })
            return

        avatar = message.sender.photo.url if message.sender.photo else None
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'chat_message',
                'conversation_id': self.conversation.id,
                'message': {
                    'id': message.id,
                    'image': self.base_url + image if image else "",
                    'avatar': self.base_url + avatar if avatar else "",
                    'sender': {
                        'id': message.sender.id,
                        'full_name': message.sender.full_name,
                    },
                    'text': message.text,
                    'type': message.type,
                    'created_at': message.created_at.strftime('%Y-%m-%d %H:%M:%S %z'),
                    'conversation': self.conversation.id
                }
            }
        )

    async def mark_as_read(self, data):
        try:
            message_id = data['message_id']
            message = ChatMessage.objects.get(id=message_id)
            message.mark_as_read(self.user)
            await self.send(text_data=json.dumps({
                'action': 'message_read',
                'message_id': message_id
            }))
        except ChatMessage.DoesNotExist:
            await self.send({
                'type': 'error_message',
                'error': Result.error(_("Message ID is not valid!"))
            })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'action': 'chat_message',
            'message': event['message']
        }))

    async def error_message(self, event):
        error = event['error']
        await self.send(text_data=json.dumps({
            'action': 'error_message',
            'error': error
        }))


class NotificationConsumer(BaseConsumer):

    async def connect(self):
        await super().prepare_connection()
        user_groups = await database_sync_to_async (
            list
        )(self.user.groups.all())

        if self.channel_layer:
            self.user_groups_names = []
            for group in user_groups:
                user_group_name = f'user_group_{group.id}'
                await self.channel_layer.group_add(
                    user_group_name,
                    self.channel_name
                )
                self.user_groups_names.append(user_group_name)
        await self.accept()

    async def receive(self, text_data):
        if not text_data:
            return
        data = json.loads(text_data)
        action = data.get('action')
        # if action == 'send_notification':
        #     await self.send_notification(data)
        if action == 'mark_notification_as_read':
            await self.mark_as_read(data)

    # async def send_notification(self, data):
    #     await self.channel_layer.group_send(
    #         self.conversation_group_name, {
    #             'type': 'notification_message',
    #             'message': data
    #         }
    #     )

    async def mark_as_read(self, data):
        notification_id = data['notification_id']
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.mark_as_read(self.user)
            await self.send(text_data=json.dumps({
                'action': 'notification_read',
                'notification_id': notification_id
            }))
        except Notification.DoesNotExist:
            await self.send({
                'type': 'error_message',
                'error': Result.error(_("Notification ID is not valid!"))
            })

    async def notification_message(self, event):
        data = event['message']
        if data.get('sender') is None:
            data['sender'] = {
                "first_name": "System",
                "last_name": "",
                "id": 0,
                "photo": ""
            }
        elif data['sender'].get('photo') and hasattr(self, 'baseurl'):
            if not data['sender'].get('photo').startswith('http'):
                data['sender']['photo'] = self.baseurl + data['sender']['photo']

        await self.send(text_data=json.dumps({
            'action': 'notification_message',
            'message': data
        }))

    async def error_message(self, event):
        error = event['error']
        await self.send(text_data=json.dumps({
            'action': 'error_message',
            'error': error
        }))


class BackUpConsumer(BaseConsumer):

    async def connect(self):
        await super().prepare_connection()
        user_groups = await database_sync_to_async (
            list
        )(self.user.groups.all())

        if self.channel_layer:
            self.user_groups_names = []
            for group in user_groups:
                user_group_name = f'user_group_{group.id}'
                await self.channel_layer.group_add(
                    user_group_name,
                    self.channel_name
                )
                self.user_groups_names.append(user_group_name)
        await self.accept()

    async def backup_status(self, event):
        await self.send(text_data=json.dumps({
            'action': 'backup_status',
            'message': event['backup']
        }))
