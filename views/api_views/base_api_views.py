from copy import deepcopy
import importlib

from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from drf_spectacular.utils import extend_schema

from lava.enums import PermissionActionName
from lava.messages import ACTION_NOT_ALLOWED
from lava.pagination import LavaPageNumberPagination
from lava.serializers.serializers import ResultSerializer
from lava.services.permissions import get_model_base_permission_class
from lava.services.class_permissions import ActionNotAllowed
from lava.utils import Result


class BaseModelViewSet(ModelViewSet):

    pagination_class = LavaPageNumberPagination

    serializer_class = None
    list_serializer_class = None
    retrieve_serializer_class = None
    create_serializer_class = None
    update_serializer_class = None
    delete_serializer_class = None

    denied_actions = []

    def get_override_field_values(self):
        """
        This function is used to override field values gotten from the API
        """
        return {}

    def get_queryset(self):
        ActiveModel = self.queryset.model
        trash = getattr(self, 'trash', False)
        user = getattr(self, 'user', None)
        return ActiveModel.filter(user=user, trash=trash, kwargs=self.request.GET)

    def get_serializer_class(self):
        self.serializer_class = self.list_serializer_class or self.serializer_class
        if self.action == 'retrieve' and self.retrieve_serializer_class:
            self.serializer_class = self.retrieve_serializer_class
        elif self.action == 'create' and self.create_serializer_class:
            self.serializer_class = self.create_serializer_class
        elif self.action in ['update', 'partial_update'] and self.update_serializer_class:
            self.serializer_class = self.update_serializer_class
        elif self.action == 'destroy' and self.delete_serializer_class:
            self.serializer_class = self.delete_serializer_class
        elif self.action == 'metadata':
            self.serializer_class = self.get_metadata_serializer_class()
        return self.serializer_class

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        serializer = serializer_class(*args, user=getattr(self, 'user', None), **kwargs)
        return serializer

    def get_metadata_serializer_class(self):
        serializer_class = None
        display_mode = self.request.GET.get("mode") == 'display'

        if self.detail:
            if display_mode:
                serializer_class = self.retrieve_serializer_class
            else:
                serializer_class = self.update_serializer_class
        else:
            if display_mode:
                serializer_class = self.list_serializer_class
            else:
                serializer_class = self.create_serializer_class

        return serializer_class or self.serializer_class

    def get_permissions(self):
        permission_classes = self.permission_classes or []
        ActiveModel = self.queryset.model

        if self.action == 'create':
            permission_classes.extend([
                get_model_base_permission_class(ActiveModel, PermissionActionName.Add)
            ])
        elif self.action in ['update', 'partial_update']:
            permission_classes.extend([
                get_model_base_permission_class(ActiveModel, PermissionActionName.Change)
            ])
        elif self.action == 'destroy':
            permission_classes.extend([
                get_model_base_permission_class(ActiveModel, PermissionActionName.SoftDelete)
            ])
        elif self.action == 'retrieve':
            permission_classes.extend([
                get_model_base_permission_class(ActiveModel, PermissionActionName.View)
            ])
        elif self.action == 'list':
            permission_classes.extend([
                get_model_base_permission_class(ActiveModel, PermissionActionName.List)
            ])
        elif self.action in ['view_trash', 'view_trash_item']:
            permission_classes.extend([
                get_model_base_permission_class(ActiveModel, PermissionActionName.ViewTrash)
            ])
        elif self.action == 'hard_delete':
            permission_classes.extend([
                get_model_base_permission_class(ActiveModel, PermissionActionName.Delete)
            ])
        elif self.action == 'restore':
            permission_classes.extend([
                get_model_base_permission_class(ActiveModel, PermissionActionName.Restore)
            ])
        elif self.action == 'duplicate':
            permission_classes.extend([
                get_model_base_permission_class(ActiveModel, PermissionActionName.Duplicate)
            ])
        # elif self.action == "metadata":
        #     self.permission_classes = [permissions.AllowAny]

        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        if "list" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        self.user = request.user
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        if "retrieve" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        self.user = request.user
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(responses=ResultSerializer)
    def create(self, request, *args, **kwargs):
        if "create" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        self.user = request.user
        override_field_values = self.get_override_field_values()
        data = request.data
        if override_field_values:
            data = deepcopy(data)
            for key, value in override_field_values.items():
                data[key] = value

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        if hasattr(serializer, 'result'):
            result = serializer.result
            if result.is_error:
                return Response(result.to_dict(), headers=headers, status=status.HTTP_400_BAD_REQUEST)
            return Response(result.to_dict(), headers=headers)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(responses=ResultSerializer)
    def update(self, request, *args, **kwargs):
        if "update" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        self.user = request.user
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        override_field_values = self.get_override_field_values()
        data = request.data
        if override_field_values:
            data = deepcopy(data)
            for key, value in override_field_values.items():
                data[key] = value

        serializer = self.get_serializer(instance=instance, data=data, partial=partial)

        serializer.is_valid(raise_exception=True)

        if not request.data:
            return Response(serializer.data)

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        if hasattr(serializer, 'result'):
            return Response(serializer.result.to_dict())
        return Response(serializer.data)

    @extend_schema(responses=ResultSerializer)
    def destroy(self, request, *args, **kwargs):
        if "destroy" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        self.user = request.user
        object = self.get_object()
        result = object.delete(user=self.user)
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        return Response(result.to_dict(), status=status.HTTP_200_OK)

    def options(self, request, *args, **kwargs):
        if "metadata" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        self.user = request.user
        return super().options(request, *args, **kwargs)

    @extend_schema(responses=ResultSerializer)
    @action(detail=True, methods=["POST"])
    def duplicate(self, request, pk):
        if "duplicate" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        self.user = request.user
        obj = self.get_object()
        result = obj.duplicate(user=self.user)
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        return Response(result.to_dict(), status=status.HTTP_200_OK)

    # # Specify operation ID for get and list APIs
    # list.operation_id = f"object_viewset_list"
    # retrieve.operation_id = f"object_viewset_retrieve"

    # Trash specific Views
    @extend_schema(responses=list_serializer_class or serializer_class)
    @action(detail=False, methods=["GET"], url_path="trash")
    def view_trash(self, request, *args, **kwargs):
        if "trash" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        self.user = request.user
        self.trash = True
        return super().list(request, *args, **kwargs)

    @extend_schema(responses=retrieve_serializer_class or serializer_class)
    @action(detail=False, methods=["GET"], url_path='trash/(?P<pk>[^/.]+)')
    def view_trash_item(self, request, *args, **kwargs):
        if "trash" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        self.user = request.user
        self.trash = True
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(responses=ResultSerializer)
    @action(detail=False, methods=["POST"], url_path='trash/(?P<pk>[^/.]+)/delete')
    def hard_delete(self, request, *args, **kwargs):
        if "trash" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        self.user = request.user
        self.trash = True
        object = self.get_object()
        result = object.delete(user=self.user, soft_delete=False)
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        return Response(result.to_dict(), status=status.HTTP_200_OK)

    @extend_schema(responses=ResultSerializer)
    @action(detail=False, methods=["POST"], url_path='trash/(?P<pk>[^/.]+)/restore')
    def restore(self, request, *args, **kwargs):
        if "restore" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        self.user = request.user
        self.trash = True
        obj = self.get_object()
        result = obj.restore(user=self.user)
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        return Response(result.to_dict(), status=status.HTTP_200_OK)



class ReadOnlyBaseModelViewSet(ReadOnlyModelViewSet):

    pagination_class = LavaPageNumberPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        permission_classes = super().permission_classes()

        if self.action == 'create':
            permission_classes = [ActionNotAllowed]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [ActionNotAllowed]
        elif self.action == 'destroy':
            permission_classes = [ActionNotAllowed]
        elif self.action in ['view_trash', 'view_trash_item']:
            permission_classes = [ActionNotAllowed]
        elif self.action == 'hard_delete':
            permission_classes = [ActionNotAllowed]
        elif self.action == 'restore':
            permission_classes = [ActionNotAllowed]
        elif self.action == 'duplicate':
            permission_classes = [ActionNotAllowed]
        return [permission() for permission in permission_classes]
