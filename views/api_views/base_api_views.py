from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet

from lava.pagination import LavaPageNumberPagination


class ReadOnlyBaseModelViewSet(ReadOnlyModelViewSet):

    pagination_class = LavaPageNumberPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        ActiveModel = self.queryset.model
        return ActiveModel.filter(user=self.user, kwargs=self.request.GET)
    
    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        serializer = serializer_class(*args, user=self.user, **kwargs)
        return serializer

    def get_permissions(self):
        permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        self.user = request.user
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        self.user = request.user
        return super().retrieve(request, *args, **kwargs)
    
    def options(self, request, *args, **kwargs):
        self.user = request.user
        return super().options(request, *args, **kwargs)
   

class BaseModelViewSet(ModelViewSet):

    pagination_class = LavaPageNumberPagination

    def get_queryset(self):
        ActiveModel = self.queryset.model
        return ActiveModel.filter(user=self.user, kwargs=self.request.GET)
    
    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        serializer = serializer_class(*args, user=self.user, **kwargs)
        return serializer

    def get_permissions(self):
        permission_classes = self.permission_classes
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        self.user = request.user
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        self.user = request.user
        return super().retrieve(request, *args, **kwargs)
    
    def create(self, request, *args, **kwargs):
        self.user = request.user
        return super().create(request, *args, **kwargs)
    
    def update(self, request, *args, **kwargs):
        self.user = request.user
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        self.user = request.user
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        self.user = request.user
        object = self.get_object()
        result = object.delete(user=self.user)
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        return Response(result.to_dict(), status=status.HTTP_200_OK)

    def options(self, request, *args, **kwargs):
        self.user = request.user
        return super().options(request, *args, **kwargs)
    
    @action(detail=True, methods=["POST"])
    def restore(self, request, pk):
        self.user = request.user
        ActiveModel = self.queryset.model
        product = get_object_or_404(ActiveModel.trash.all(), pk=pk)
        result = product.restore(user=self.user)
        if result.is_error:
            return Response(result.to_dict(), status=status.HTTP_400_BAD_REQUEST)
        return Response(result.to_dict(), status=status.HTTP_200_OK)
