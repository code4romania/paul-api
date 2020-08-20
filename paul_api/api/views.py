from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.models import User

from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework import permissions

from rest_framework_guardian.filters import ObjectPermissionsFilter


from . import serializers, models
from .permissions import BaseModelPermissions


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    lookup_field = "username"

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.UserCreateSerializer
        return serializers.UserSerializer


class DatabaseViewSet(viewsets.ModelViewSet):
    queryset = models.Database.objects.all()
    serializer_class = serializers.DatabaseSerializer
    # lookup_field = "slug"


class EntriesPagination(PageNumberPagination):
    page_size = 100


class CanView(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.
    Assumes the model instance has an `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Instance must have an attribute named `user`.
        return obj.owner == request.user


class TableViewSet(viewsets.ModelViewSet):
    queryset = models.Table.objects.all()
    # lookup_field = "slug"
    pagination_class = EntriesPagination
    permission_classes = (BaseModelPermissions, )
    filter_backends = [ObjectPermissionsFilter]

    # def get_queryset(self):
    #     user = self.request.user
    #     return models.Table.objects.filter(owner=user)

    def get_serializer_class(self):
        print('action:', self.action)
        if self.action == "list":
            return serializers.DatabaseTableListSerializer
        elif self.action == "create":
            print('this ser')
            return serializers.TableCreateSerializer
        return serializers.TableSerializer

    @action(methods=["get"], detail=True, url_path="entries", url_name="entries")
    def entries(self, request, pk):
        obj = self.get_object()
        str_q = request.GET.get("q", "") if request else None
        str_fields = request.GET.get("fields", "") if request else None

        fields = str_fields.split(",") if str_fields else None
        if not fields:
            fields = obj.fields.values_list("name", flat=True).order_by('name')[:4]

        q = Q()
        # if str_q:
        #     values = eav_models.Value.objects.filter(value_text__icontains=str_q, Entry__table=obj, attribute__slug__in=fields).values_list('entity_id', flat=True)
        #     q = Q(id__in=values)

        queryset = obj.entries.filter(q)
        page = self.paginate_queryset(queryset.filter())

        if page is not None:
            serializer = serializers.EntrySerializer(page, many=True, context={"fields": fields})
            return self.get_paginated_response(serializer.data)
        serializer = serializers.EntrySerializer(queryset, many=True)
        return Response(serializer.data)


class FilterViewSet(viewsets.ModelViewSet):
    queryset = models.Filter.objects.all()
    # lookup_field = "slug"
    pagination_class = EntriesPagination
    # permission_classes = (BaseModelPermissions, )
    # filter_backends = [ObjectPermissionsFilter]

    # def get_queryset(self):
    #     user = self.request.user
    #     return models.Table.objects.filter(owner=user)

    def get_serializer_class(self):
        print('action:', self.action)
        if self.action == "list":
            return serializers.FilterListSerializer

        # elif self.action == "create":
        elif self.action == "retrieve":
            # print('this ser')
            return serializers.FilterDetailSerializer
        return serializers.FilterListSerializer

    @action(methods=["get"], detail=True, url_path="entries", url_name="entries")
    def entries(self, request, slug):
        obj = self.get_object()
        str_q = request.GET.get("q", "") if request else None
        str_fields = request.GET.get("fields", "") if request else None

        fields = str_fields.split(",") if str_fields else None
        primary_table_fields = list(obj.primary_table_fields.values_list("name", flat=True).order_by('name'))
        join_tables_fileds = list(obj.filter_join_tables.values_list("fields__name", flat=True).order_by('fields__name'))
        if not fields:
            fields = primary_table_fields + join_tables_fileds

        # q = Q()
        # if str_q:
        #     values = eav_models.Value.objects.filter(value_text__icontains=str_q, Entry__table=obj, attribute__slug__in=fields).values_list('entity_id', flat=True)
        #     q = Q(id__in=values)
        print(primary_table_fields)
        queryset = obj.primary_table.entries.values('eav_values')
        return Response(queryset)
        result = []
        for entry in queryset:
            for table in obj.filter_join_tables.all():
                pass

        page = self.paginate_queryset(queryset.filter())

        if page is not None:
            serializer = serializers.EntrySerializer(page, many=True, context={"fields": fields})
            return self.get_paginated_response(serializer.data)
        serializer = serializers.EntrySerializer(queryset, many=True)
        return Response(serializer.data)
