from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.models import User

from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status

from rest_framework_guardian.filters import ObjectPermissionsFilter

from django_filters import rest_framework as filters


from . import serializers, models
from .permissions import BaseModelPermissions

from pprint import pprint


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
    page_size = 10


class CanView(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to access it.
    Assumes the model instance has an `user` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Instance must have an attribute named `user`.
        return obj.owner == request.user


class MyFilterBackend(filters.DjangoFilterBackend):
    def get_filterset_kwargs(self, request, queryset, view):
        kwargs = super().get_filterset_kwargs(request, queryset, view)

        # merge filterset kwargs provided by view class
        if hasattr(view, 'get_filterset_kwargs'):
            kwargs.update(view.get_filterset_kwargs())

        return kwargs


class TableViewSet(viewsets.ModelViewSet):
    queryset = models.Table.objects.all()
    # lookup_field = "slug"
    pagination_class = EntriesPagination
    permission_classes = (BaseModelPermissions, )
    filter_backends = [ObjectPermissionsFilter, filters.DjangoFilterBackend]
    filterset_fields = ['active']
    # def get_queryset(self):
    #     user = self.request.user
    #     return models.Table.objects.filter(owner=user)

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.DatabaseTableListSerializer
        elif self.action == "create":
            return serializers.TableCreateSerializer
        return serializers.TableSerializer


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
        if self.action == "list":
            return serializers.FilterListSerializer

        # elif self.action == "create":
        elif self.action == "retrieve":
            # print('this ser')
            return serializers.FilterDetailSerializer
        return serializers.FilterListSerializer


    @action(methods=["get"], detail=True, url_path="entries", url_name="entries")
    def entries(self, request, pk):
        obj = self.get_object()
        str_fields = request.GET.get("fields", "") if request else None

        fields = str_fields.split(",") if str_fields else None
        primary_table_fields = ['data__{}'.format(x) for x in obj.primary_table_fields.values_list("name", flat=True).order_by('name')]

        primary_table = obj.primary_table
        secondary_table = obj.filter_join_tables.all()[0]
        secondary_table_name = secondary_table.table.slug
        secondary_table_join_field = secondary_table.join_field.name

        join_tables_fileds = ['data__{}'.format(x) for x in obj.filter_join_tables.values_list("fields__name", flat=True).order_by('fields__name')]
        join_tables_fileds.append('data__{}'.format(secondary_table_join_field))
        secondary_table_fields = ['{}__{}'.format(x[0].lower(), x[1]) for x in obj.filter_join_tables.values_list("table__name", "fields__name").order_by('fields__name')]
        join_values = models.Entry.objects.filter(table=primary_table).values('data__{}'.format(obj.join_field.name))

        result_values = models.Entry.objects.filter(
            table__slug=secondary_table_name).filter(
                **{'data__{}__in'.format(secondary_table_join_field): join_values}).\
            values(*join_tables_fileds)

        queryset = result_values

        if not fields:
            fields = [x.replace('data__', '{}__'.format(primary_table.slug)) for x in primary_table_fields] 
            fields +=  [x.replace('data__', '{}__'.format(secondary_table_name)) for x in join_tables_fileds]

        # pprint(queryset)
        page = self.paginate_queryset(queryset)

        if page is not None:
            final_page = []
            for entry in page:
                final_entry = {}
                final_entry_primary_table_values = {}
                entry_primary_table_values = models.Entry.objects.filter(
                    table=primary_table).filter(
                        **{'data__{}'.format(obj.join_field.name): entry['data__{}'.format(secondary_table_join_field)]}).\
                    values(*primary_table_fields)[0]

                for key in entry:
                    final_entry[key.replace('data__', '{}__'.format(secondary_table_name))] = entry[key]
                for key in entry_primary_table_values:
                    final_entry_primary_table_values[key.replace('data__', '{}__'.format(primary_table.slug))] = entry_primary_table_values[key]

                final_entry.update(final_entry_primary_table_values)
                final_page.append(final_entry)

            # serializer = serializers.FilterEntrySerializer(page, many=True, context={"fields": ['test']})
            serializer = serializers.FilterEntrySerializer(final_page, many=True, context={"fields": fields})
            return self.get_paginated_response(serializer.data)
        serializer = serializers.FilterEntrySerializer(queryset, many=True)
        return Response(serializer.data)


class EntryViewSet(viewsets.ModelViewSet):
    pagination_class = EntriesPagination

    def get_queryset(self):
        return models.Entry.objects.filter(table=self.kwargs['table_pk'])

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.EntrySerializer
        # elif self.action == "create":
        #     print('this ser')
        #     return serializers.TableCreateSerializer
        return serializers.EntrySerializer

    def list(self, request, table_pk):
        table = models.Table.objects.get(pk=table_pk)
        str_q = request.GET.get("q", "") if request else None
        str_fields = request.GET.get("fields", "") if request else None

        fields = str_fields.split(",") if str_fields else None
        if not fields:
            fields = table.fields.values_list("name", flat=True).order_by('name')[:4]

        q = Q()

        queryset = table.entries.filter(q)

        page = self.paginate_queryset(queryset.filter())

        if page is not None:
            serializer = serializers.EntrySerializer(page, many=True, context={"fields": fields, "table": table, "request": request})
            return self.get_paginated_response(serializer.data)
        serializer = serializers.EntrySerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, table_pk, pk):
        table = models.Table.objects.get(pk=table_pk)
        object = models.Entry.objects.get(pk=pk)

        fields = table.fields.values_list("name", flat=True).order_by('name')
        serializer = serializers.EntrySerializer(object, context={"fields": fields, "table": table, "request": request})


        return Response(serializer.data)

    def update(self, request, table_pk, pk, *args, **kwargs):
        table = models.Table.objects.get(pk=table_pk)
        object = self.get_object()

        fields = table.fields.values_list("name", flat=True).order_by('name')
        serializer = serializers.EntrySerializer(object, data=request.data, context={"fields": fields, "table": table, "request": request})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def create(self, request, table_pk):
        table = models.Table.objects.get(pk=table_pk)
        # object = self.get_object()
        data = request.data
        data['table'] = table.pk
        fields = table.fields.values_list("name", flat=True).order_by('name')

        serializer = serializers.EntrySerializer(data=data, context={"fields": fields, "table": table, "request": request})
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)