import asyncio

from channels.layers import get_channel_layer

from lava.utils import humanize_datetime, guess_protocol
from lava.settings import HOST


async def send_message_to_clients(message, alias='default', target_users=None, target_groups=None):
    """ Send a message to a specific WebSocket clients. """
    channel_layer = get_channel_layer()
    if target_groups:
        group_name_prefix = 'user_group_'
        for group in target_groups:
            try:
                await channel_layer.group_send(
                    f"{group_name_prefix}{group.id}", message
                )
            except Exception:
                pass
    if target_users:
        group_name_prefix = 'user_'
        for user in target_users:
            try:
                await channel_layer.group_send(
                    f"{group_name_prefix}{user.id}", message
                )
            except Exception:
                pass


def send_ws_notification(instance, target_groups, target_users):
    """
    Send a notification via WebSocket to the target users and groups
    """

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    photo = ''
    if instance.sender and instance.sender.photo:
        photo = f"{guess_protocol()}://{HOST}{instance.sender.photo.url}"
    loop.run_until_complete(
        send_message_to_clients(
            message={
                "type": "send_notification",
                "message": {
                    "title": str(instance.title),
                    "sender": {
                        "id": instance.sender.id,
                        "first_name": instance.sender.first_name,
                        "last_name": instance.sender.last_name,
                        "photo": photo
                    } if instance.sender else None,
                    "date": humanize_datetime(instance.date),
                    "content": str(instance.content),
                    "category": instance.category,
                    "url": instance.url,
                }
            },
            alias='notification',
            target_users=target_users,
            target_groups=target_groups,
        )
    )
    loop.close()


def send_ws_backup_status(instance):
    """
    Send initiated backup status via WebSocket to the target users and groups
    """

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        send_message_to_clients(
            message={
                "type": "send_backup_status",
                "backup": {
                    "id": instance.id,
                    "status": instance.status,
                },
            },
            alias='backup',
            target_users=[instance.created_by],
        )
    )
    loop.close()
