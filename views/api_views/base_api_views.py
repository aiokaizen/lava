from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from lava.messages import ACTION_NOT_ALLOWED
from lava.utils import Result
from lava.pagination import LavaPageNumberPagination


class ReadOnlyBaseModelViewSet(ReadOnlyModelViewSet):

    pagination_class = LavaPageNumberPagination
    permission_classes = [permissions.IsAuthenticated]

    list_serializer_class = None
    retrieve_serializer_class = None

    denied_actions = []

    def get_queryset(self):
        ActiveModel = self.queryset.model
        return ActiveModel.filter(user=self.user, kwargs=self.request.GET)
    
    def get_serializer(self, *args, **kwargs):
        self.serializer_class = self.list_serializer_class or self.serializer_class
        if self.action == 'retrieve' and self.retrieve_serializer_class:
            self.serializer_class = self.retrieve_serializer_class
        elif self.action == 'metadata' and self.detail:
            serializer_class = self.get_serializer_class
        elif self.action == 'metadata':
            serializer_class = self.list_serializer_class

        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        serializer = serializer_class(*args, user=self.user, **kwargs)
        return serializer

    def get_permissions(self):
        permission_classes = [permissions.IsAuthenticated]
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
    
    def options(self, request, *args, **kwargs):
        if "metadata" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
            
        self.user = request.user
        return super().options(request, *args, **kwargs)
   

class BaseModelViewSet(ModelViewSet):

    pagination_class = LavaPageNumberPagination

    list_serializer_class = None
    retrieve_serializer_class = None
    create_serializer_class = None
    update_serializer_class = None
    delete_serializer_class = None

    denied_actions = []

    def get_queryset(self):
        ActiveModel = self.queryset.model
        return ActiveModel.filter(user=self.user, kwargs=self.request.GET)
    
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
        serializer = serializer_class(*args, user=self.user, **kwargs)
        return serializer

    def get_metadata_serializer_class(self):
        serializer_class = self.list_serializer_class
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
        permission_classes = self.permission_classes
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
    
    def create(self, request, *args, **kwargs):
        if "create" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        self.user = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        if hasattr(serializer, 'result'):
            result = serializer.result
            if result.is_error:
                return Response(result.to_dict(), headers=headers, status=status.HTTP_400_BAD_REQUEST)
            return Response(result.to_dict(), headers=headers)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        if "update" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        self.user = request.user
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
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
    
    @action(detail=True, methods=["POST"])
    def restore(self, request, pk):
        if "restore" in self.denied_actions:
            return Response(
                Result(False, ACTION_NOT_ALLOWED).to_dict(),
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        self.user = request.user
        ActiveModel = self.queryset.model
        product = get_object_or_404(ActiveModel.trash.all(), pk=pk)
        result = product.restore(user=self.user)
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        return Response(result.to_dict(), status=status.HTTP_200_OK)
