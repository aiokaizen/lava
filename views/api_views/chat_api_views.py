from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from lava.serializers.chat_serializers import (
    ConversationListSerializer, ConversationGetSerializer,
    ConversationCreateUpdateSerializer, MessageListSerializer
)
from lava.models.chat_models import ChatMessage, Conversation
from lava.views.api_views.base_api_views import BaseModelViewSet


class ChatAPIViewSet(BaseModelViewSet):

    page_size = 100
    permission_classes = [permissions.IsAuthenticated]
    queryset = Conversation.objects.none()

    list_serializer_class = ConversationListSerializer
    retrieve_serializer_class = ConversationGetSerializer
    create_serializer_class = ConversationCreateUpdateSerializer
    update_serializer_class = ConversationCreateUpdateSerializer

    def get_queryset(self):
        user = getattr(self, 'user', None)
        trash = getattr(self, 'trash', False)
        return Conversation.get_user_conversations(
            user=user, trash=trash, kwargs=self.request.GET
        )

    def get_permissions(self):
        if self.action == 'mark_as_read':
            self.permission_classes = [permissions.AllowAny]
        return super().get_permissions()

    @action(detail=True, methods=['POST'])
    def mark_as_read(self, request, *args, **kwargs):
        self.user = request.user
        conversation = self.get_object()
        result = conversation.mark_as_read(self.user)
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        return Response(result.to_dict(), status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'])
    def unread_messages(self, request, *args, **kwargs):
        self.user = request.user
        messages = Conversation.get_user_unread_messages(self.user)
        unread_count = messages.count()
        serializer = MessageListSerializer(
            messages[:5], many=True, user=self.user,
            context=self.get_serializer_context()
        )
        return Response({
            "count": unread_count,
            "messages": serializer.data
        })
