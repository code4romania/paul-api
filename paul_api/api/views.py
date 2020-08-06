from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.models import User

from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from eav import models as eav_models

from . import serializers, models


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer
    lookup_field = "username"


class DatabaseViewSet(viewsets.ModelViewSet):
    queryset = models.Database.objects.all()
    serializer_class = serializers.DatabaseSerializer
    lookup_field = "slug"


class EntriesPagination(PageNumberPagination):
    page_size = 100


class TableViewSet(viewsets.ModelViewSet):
    queryset = models.Table.objects.all()
    lookup_field = "slug"
    pagination_class = EntriesPagination

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.DatabaseTableListSerializer
        return serializers.TableSerializer

    @action(methods=["get"], detail=True, url_path="entries", url_name="entries")
    def entries(self, request, slug):
        obj = self.get_object()
        str_q = request.GET.get("q", "") if request else None
        str_fields = request.GET.get("fields", "") if request else None

        fields = str_fields.split(",") if str_fields else None
        if not fields:
            fields = obj.fields.values_list("name", flat=True).order_by('name')[:4]

        q = Q()
        if str_q:
            values = eav_models.Value.objects.filter(value_text__icontains=str_q, Entry__table=obj, attribute__slug__in=fields).values_list('entity_id', flat=True)
            q = Q(id__in=values)

        queryset = obj.entries.filter(q)
        page = self.paginate_queryset(queryset.filter())

        if page is not None:
            serializer = serializers.EntrySerializer(page, many=True, context={"fields": fields})
            return self.get_paginated_response(serializer.data)
        serializer = serializers.EntrySerializer(queryset, many=True)
        return Response(serializer.data)
