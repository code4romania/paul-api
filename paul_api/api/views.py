from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.models import User
from django.http import HttpResponse

from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status
from rest_framework_guardian.filters import ObjectPermissionsFilter

from rest_framework import filters as drf_filters
from django_filters import rest_framework as filters

from silk.profiling.profiler import silk_profile

import csv
from io import StringIO
import os
from datetime import datetime

from . import serializers, models
from . import permissions as api_permissions
from .permissions import BaseModelPermissions
from . import utils
from pprint import pprint


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer

    def get_serializer_class(self):
        if self.action == "create":
            return serializers.UserCreateSerializer
        return serializers.UserSerializer


class UserView(APIView):
    """
    View to list all users in the system.

    * Requires token authentication.
    * Only admin users are able to access this view.
    """

    def get(self, request, format=None):
        """
        Return a list of all users.
        """
        user = request.user
        response = {"username": user.username}
        return Response(response)


class DatabaseViewSet(viewsets.ModelViewSet):
    queryset = models.Database.objects.all()
    serializer_class = serializers.DatabaseSerializer


class EntriesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "perPage"
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response(
            {
                "links": {
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "results": data,
            }
        )


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
        if hasattr(view, "get_filterset_kwargs"):
            kwargs.update(view.get_filterset_kwargs())

        return kwargs


class TableViewSet(viewsets.ModelViewSet):
    queryset = (
        models.Table.objects.all()
        .prefetch_related("fields")
        .select_related("database")
    )
    pagination_class = EntriesPagination
    # permission_classes = (BaseModelPermissions, api_permissions.IsAuthenticatedOrGetToken )
    permission_classes = (BaseModelPermissions,)
    filter_backends = [ObjectPermissionsFilter, filters.DjangoFilterBackend]
    filterset_fields = ["active"]

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.DatabaseTableListSerializer
        elif self.action in ["create", "update"]:
            return serializers.TableCreateSerializer
        return serializers.TableSerializer

    def get_permissions(self):
        base_permissions = super(self.__class__, self).get_permissions()
        if self.action == "csv_export":
            base_permissions = (api_permissions.IsAuthenticatedOrGetToken(),)
        return base_permissions

    # @action(
    #     detail=True,
    #     methods=["put"],
    #     name="Uploader View",
    #     url_path="csv-prepare-fields",
    # )
    # def csv_prepare_fields(self, request, pk):
    #     file = request.FILES["file"]
    #     delimiter = request.POST.get("delimiter")
    #     fields = []
    #     table = self.get_object()

    #     decoded_file = file.read().decode("utf-8").splitlines()
    #     csv_import = models.CsvImport.objects.create(
    #         table=table, file=file, delimiter=delimiter
    #     )
    #     reader = csv.DictReader(decoded_file, delimiter=delimiter)

    #     for field in reader.fieldnames:
    #         csv_field_map = models.CsvFieldMap.objects.create(
    #             table=table, original_name=field, field_name=field
    #         )
    #         fields.append(
    #             {
    #                 "original_name": field.encode(),
    #                 "field_name": field,
    #                 "field_type": "text",
    #                 "field_format": "",
    #             }
    #         )

    #     response = {
    #         "table": table.name,
    #         "import_id": csv_import.pk,
    #         "fields": fields,
    #     }
    #     return Response(response)

    # @action(
    #     detail=True,
    #     methods=["post"],
    #     name="CSV import view",
    #     url_path="csv-import/(?P<csv_import_pk>[^/.]+)",
    # )
    # def csv_import(self, request, pk, csv_import_pk):
    #     fields = request.data.get("fields")
    #     csv_import = models.CsvImport.objects.get(pk=csv_import_pk)
    #     table = self.get_object()

    #     table.csv_field_mapping.all().delete()
    #     for field in fields:
    #         csv_field_map = models.CsvFieldMap.objects.create(
    #             table=table,
    #             original_name=field["original_name"],
    #             field_name=field["field_name"],
    #             field_type=field["field_type"],
    #             field_format=field["field_format"],
    #         )
    #         table_column, _ = models.TableColumn.objects.get_or_create(
    #             table=table,
    #             name=utils.snake_case(field["field_name"]),
    #             display_name=field["field_name"],
    #             field_type=field["field_type"],
    #         )

    #     reader = csv.DictReader(
    #         StringIO(csv_import.file.read().decode("utf-8")),
    #         delimiter=csv_import.delimiter,
    #     )
    #     errors, errors_count, imports_count = utils.import_csv(reader, table)
    #     csv_import.errors = errors
    #     csv_import.errors_count = errors_count
    #     csv_import.imports_count = imports_count
    #     csv_import.save()
    #     response = {
    #         "errors_count": errors_count,
    #         "imports_count": imports_count,
    #         "errors": errors,
    #     }
    #     return Response(response)

    def create(self, request):
        fields = request.data.get("fields")
        csv_import_pk = request.data.get("import_id")
        data = request.data

        serializer = serializers.TableCreateSerializer(
            data=data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)

        if not csv_import_pk:
            headers = self.get_success_headers(serializer.data)
            return Response(
                serializer.data, status=status.HTTP_201_CREATED, headers=headers
            )

        table = models.Table.objects.get(pk=serializer.data["id"])
        csv_import = models.CsvImport.objects.get(pk=csv_import_pk)

        for field in fields:
            csv_field_map = models.CsvFieldMap.objects.create(
                table=table,
                original_name=field["original_name"],
                field_name=field["display_name"],
                field_type=field["field_type"],
                field_format=field["field_format"],
            )
            table_column, _ = models.TableColumn.objects.get_or_create(
                table=table,
                name=utils.snake_case(field["display_name"]),
                display_name=field["display_name"],
                field_type=field["field_type"],
            )

        reader = csv.DictReader(
            StringIO(csv_import.file.read().decode("utf-8")),
            delimiter=csv_import.delimiter,
        )
        errors, errors_count, imports_count = utils.import_csv(reader, table)
        csv_import.errors = errors
        csv_import.errors_count = errors_count
        csv_import.imports_count = imports_count
        csv_import.save()
        response = {
            "errors_count": errors_count,
            "imports_count": imports_count,
            "errors": errors,
            "id": table.id,
        }
        return Response(response)

    @action(
        detail=True,
        methods=["put"],
        name="CSV manual import view",
        url_path="csv-manual-import",
    )
    def csv_manual_import(self, request, pk):
        file = request.FILES["file"]
        delimiter = request.POST.get("delimiter")
        fields = []
        table = self.get_object()

        decoded_file = file.read().decode("utf-8").splitlines()
        csv_import = models.CsvImport.objects.create(
            table=table, file=file, delimiter=delimiter
        )
        reader = csv.DictReader(decoded_file, delimiter=delimiter)

        errors, errors_count, imports_count = utils.import_csv(reader, table)
        csv_import.errors = errors
        csv_import.errors_count = errors_count
        csv_import.imports_count = imports_count
        csv_import.save()
        response = {
            "import_id": csv_import.pk,
            "errors_count": errors_count,
            "imports_count": imports_count,
            "errors": errors,
        }
        return Response(response)

    # @permission_classes([api_permissions.IsAuthenticatedOrGetToken])
    @action(
        detail=True,
        methods=["get"],
        name="CSV Export",
        url_path="csv-export",
    )
    def csv_export(self, request, pk):
        table = models.Table.objects.get(pk=pk)
        table_fields = {x.name: x for x in table.fields.all()}

        filter_dict = {}
        for key in request.GET:
            if key and key.split("__")[0] in table_fields.keys():
                value = request.GET.get(key).split(",")
                if len(value) == 1:
                    value = value[0]
                else:
                    key = key + "__in"

                if table_fields[key.split("__")[0]].field_type in [
                    "float",
                    "int",
                ]:
                    filter_dict["data__{}".format(key)] = float(value)
                else:
                    filter_dict["data__{}".format(key)] = value

        file_name = "{}__{}.csv".format(
            table.name, datetime.now().strftime("%d.%m.%Y")
        )
        with open(
            "/tmp/{}".format(file_name), "w", encoding="utf-8-sig"
        ) as csv_export_file:
            writer = csv.DictWriter(
                csv_export_file,
                delimiter=";",
                quoting=csv.QUOTE_MINIMAL,
                fieldnames=table.fields.values_list("name", flat=True),
            )
            writer.writeheader()
            for row in table.entries.filter(**filter_dict):
                writer.writerow(row.data)

        with open("/tmp/{}".format(file_name), "rb") as csv_export_file:
            response = HttpResponse(
                csv_export_file.read(), content_type="application/vnd.ms-excel"
            )
            response[
                "Content-Disposition"
            ] = 'attachment; filename="{}"'.format(file_name)
        os.remove("/tmp/{}".format(file_name))
        return response


class FilterViewSet(viewsets.ModelViewSet):
    queryset = models.Filter.objects.all()
    pagination_class = EntriesPagination

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.FilterListSerializer
        elif self.action == "retrieve":
            return serializers.FilterDetailSerializer
        elif self.action in ["create", "update"]:
            return serializers.FilterCreateSerializer

        return serializers.FilterListSerializer

    @action(
        methods=["get"], detail=True, url_path="entries", url_name="entries"
    )
    def entries(self, request, pk):
        obj = models.Filter.objects.filter(pk=pk).prefetch_related(
            "primary_table", "join_tables"
        )[0]
        str_fields = request.GET.get("fields", "") if request else None

        fields = str_fields.split(",") if str_fields else None

        primary_table = obj.primary_table
        primary_table_slug = primary_table.table.slug
        primary_table_join_field = primary_table.join_field.name

        secondary_table = obj.join_tables.all()[0]
        secondary_table_slug = secondary_table.table.slug
        secondary_table_join_field = secondary_table.join_field.name

        primary_table_fields = [
            "data__{}".format(x)
            for x in primary_table.fields.values_list(
                "name", flat=True
            ).order_by("name")
        ]

        join_tables_fields = [
            "data__{}".format(x)
            for x in obj.join_tables.values_list(
                "fields__name", flat=True
            ).order_by("fields__name")
        ]
        join_tables_fields.append("data__{}".format(secondary_table_join_field))

        join_values = models.Entry.objects.filter(
            table=primary_table.table
        ).values("data__{}".format(primary_table_join_field))

        result_values = (
            models.Entry.objects.filter(table__slug=secondary_table_slug)
            .filter(
                **{
                    "data__{}__in".format(
                        secondary_table_join_field
                    ): join_values
                }
            )
            .values(*join_tables_fields)
            .order_by("data__{}".format(secondary_table_join_field))
        )

        queryset = result_values

        if not fields:
            fields = [
                x.replace("data__", "{}__".format(primary_table_slug))
                for x in primary_table_fields
            ]
            fields += [
                x.replace("data__", "{}__".format(secondary_table_slug))
                for x in join_tables_fields
            ]

        page = self.paginate_queryset(queryset)

        if page is not None:
            final_page = []
            page_join_values = [
                x["data__{}".format(secondary_table_join_field)] for x in page
            ]
            q_primary_table_page = {
                "data__{}__in".format(
                    primary_table_join_field
                ): page_join_values
            }

            primary_table_values = {
                x.data[primary_table_join_field]: {
                    "data__" + key: value for key, value in x.data.items()
                }
                for x in models.Entry.objects.filter(table=primary_table.table)
                .filter(**q_primary_table_page)
                .exclude(data=None)
            }

            for entry in page:
                final_entry = {}
                final_entry_primary_table_values = {}

                entry_primary_table_values = primary_table_values[
                    entry["data__{}".format(secondary_table_join_field)]
                ]

                for key in entry:
                    final_entry[
                        key.replace(
                            "data__", "{}__".format(secondary_table_slug)
                        )
                    ] = entry[key]
                for key in entry_primary_table_values:
                    final_entry_primary_table_values[
                        key.replace("data__", "{}__".format(primary_table_slug))
                    ] = entry_primary_table_values[key]

                final_entry.update(final_entry_primary_table_values)
                final_page.append(final_entry)

            # serializer = serializers.FilterEntrySerializer(page, many=True, context={"fields": ['test']})
            serializer = serializers.FilterEntrySerializer(
                final_page, many=True, context={"fields": fields}
            )
            return self.get_paginated_response(serializer.data)
        serializer = serializers.FilterEntrySerializer(queryset, many=True)
        return Response(serializer.data)


from collections import OrderedDict


class EntryViewSet(viewsets.ModelViewSet):
    pagination_class = EntriesPagination
    filter_backends = (drf_filters.SearchFilter,)
    serializer_class = serializers.EntrySerializer
    search_fields = ["data__nume"]

    def get_queryset(self):
        return models.Entry.objects.filter(table=self.kwargs["table_pk"])

    def list(self, request, table_pk):
        table = models.Table.objects.get(pk=table_pk)
        str_fields = request.GET.get("__fields", "") if request else None
        str_order = request.GET.get("__order", "") if request else None
        table_fields = {x.name: x for x in table.fields.all().order_by("id")}

        if str_fields == "ALL":
            fields = [x for x in table_fields.keys()]
        else:
            fields = str_fields.split(",") if str_fields else None
            if not fields:
                fields = [x for x in table_fields.keys()][:7]

        filter_dict = {}
        for key in request.GET:
            if key and key.split("__")[0] in table_fields.keys():
                value = request.GET.get(key).split(",")
                if len(value) == 1:
                    value = value[0]
                else:
                    key = key + "__in"

                if table_fields[key.split("__")[0]].field_type in [
                    "float",
                    "int",
                ]:
                    filter_dict["data__{}".format(key)] = float(value)
                else:
                    filter_dict["data__{}".format(key)] = value

        if str_order and str_order.replace("-", "") in fields:
            if str_order.startswith("-"):
                queryset = table.entries.filter(**filter_dict).order_by(
                    "-data__{}".format(str_order[1:])
                )
            else:
                queryset = table.entries.filter(**filter_dict).order_by(
                    "data__{}".format(str_order)
                )
        else:
            queryset = table.entries.filter(**filter_dict).order_by("id")

        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = serializers.EntrySerializer(
                page,
                many=True,
                context={"fields": fields, "table": table, "request": request},
            )
            return self.get_paginated_response(serializer.data)
        serializer = serializers.EntrySerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, table_pk, pk):
        table = models.Table.objects.get(pk=table_pk)
        object = models.Entry.objects.get(pk=pk)

        fields = table.fields.values_list("name", flat=True).order_by("name")
        serializer = serializers.EntrySerializer(
            object,
            context={"fields": fields, "table": table, "request": request},
        )

        return Response(serializer.data)

    def update(self, request, table_pk, pk, *args, **kwargs):
        table = models.Table.objects.get(pk=table_pk)
        object = self.get_object()

        fields = table.fields.values_list("name", flat=True).order_by("name")

        serializer = serializers.EntrySerializer(
            object,
            data=request.data,
            context={"fields": fields, "table": table, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def create(self, request, table_pk):
        table = models.Table.objects.get(pk=table_pk)
        data = request.data
        fields = table.fields.values_list("name", flat=True).order_by("name")

        serializer = serializers.EntrySerializer(
            data=data,
            context={"fields": fields, "table": table, "request": request},
        )
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class CsvImportViewSet(viewsets.ModelViewSet):
    queryset = models.CsvImport.objects.all()
    # permission_classes = (BaseModelPermissions,)

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.CsvImportListSerializer
        return serializers.CsvImportSerializer

    def get_permissions(self):
        base_permissions = super(self.__class__, self).get_permissions()
        if self.action == "export_errors":
            base_permissions = (api_permissions.IsAuthenticatedOrGetToken(),)
        return base_permissions

    @action(
        detail=True,
        methods=["get"],
        name="Csv errors Export",
        url_path="export-errors",
    )
    def export_errors(self, request, pk):
        csv_import = self.get_object()

        file_name = "errors__" + csv_import.file.name.split("/")[-1]
        with open(
            "/tmp/{}".format(file_name), "w", encoding="utf-8-sig"
        ) as csv_export_file:
            writer = csv.DictWriter(
                csv_export_file,
                delimiter=";",
                quoting=csv.QUOTE_MINIMAL,
                fieldnames=csv_import.errors[0]["row"].keys(),
            )
            writer.writeheader()
            for row in csv_import.errors:
                writer.writerow(row["row"])

        with open("/tmp/{}".format(file_name), "rb") as csv_export_file:
            # response = HttpResponse(FileWrapper(csv_export_file), content_type='application/vnd.ms-excel')
            response = HttpResponse(
                csv_export_file.read(), content_type="application/vnd.ms-excel"
            )
            response[
                "Content-Disposition"
            ] = 'attachment; filename="{}"'.format(file_name)
        os.remove("/tmp/{}".format(file_name))
        return response

    def create(self, request):
        file = request.FILES["file"]
        delimiter = request.POST.get("delimiter")
        fields = []

        decoded_file = file.read().decode("utf-8").splitlines()
        csv_import = models.CsvImport.objects.create(
            file=file, delimiter=delimiter
        )
        reader = csv.DictReader(decoded_file, delimiter=delimiter)

        for field in reader.fieldnames:
            csv_field_map = models.CsvFieldMap.objects.create(
                csv_import=csv_import, original_name=field, field_name=field
            )
            fields.append(
                {
                    "original_name": field.encode(),
                    "display_name": field,
                    "field_type": "text",
                    "field_format": "",
                }
            )

        response = {
            "import_id": csv_import.pk,
            "fields": fields,
        }
        return Response(response)
