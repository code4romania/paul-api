from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.urls import reverse

from rest_framework import serializers

from api import models, utils
from pprint import pprint

from guardian.shortcuts import assign_perm, remove_perm
from guardian.core import ObjectPermissionChecker


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email"]

    def create(self, validated_data):
        new_user = User.objects.create(**validated_data)
        userprofile = models.Userprofile.objects.create(user=new_user)
        user_group, _ = Group.objects.get_or_create(name="user")
        new_user.groups.add(user_group)
        print("TODO: send mail")
        return new_user


class UserUpdateSerializer(serializers.ModelSerializer):
    tables_permissions = serializers.SerializerMethodField()
    avatar = serializers.ImageField(source="userprofile.avatar", allow_null=True)

    class Meta:
        model = User
        fields = ["email", "avatar", "first_name", "last_name", "tables_permissions"]

    def update(self, instance, validated_data):
        userprofile_data = validated_data.pop("userprofile")
        tables_permissions = self.initial_data.get("tables_permissions")
        if tables_permissions:
            for table_permission in tables_permissions:
                table = models.Table.objects.get(pk=table_permission["id"])
                if table_permission["permissions"] == "Can edit":
                    assign_perm("change_table", instance, table)
                    assign_perm("view_table", instance, table)
                    assign_perm("delete_table", instance, table)
                elif table_permission["permissions"] == "Can view":
                    assign_perm("view_table", instance, table)
                    remove_perm("change_table", instance, table)
                    remove_perm("delete_table", instance, table)
                else:
                    remove_perm("view_table", instance, table)
                    remove_perm("change_table", instance, table)
                    remove_perm("delete_table", instance, table)

        User.objects.filter(pk=instance.pk).update(**validated_data)
        models.Userprofile.objects.filter(user=instance).update(**userprofile_data)
        instance.refresh_from_db()

        return instance

    def get_tables_permissions(self, obj):
        tables = []

        checker = ObjectPermissionChecker(obj)

        for table in models.Table.objects.all():
            user_perms = checker.get_perms(table)

            if "change_table" in user_perms:
                table_perm = "Can edit"
            elif "view_table" in user_perms:
                table_perm = "Can view"
            else:
                table_perm = "No rights"
            tables.append({"name": table.name, "id": table.id, "permissions": table_perm})
        return tables


class UserDetailSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    tables_permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["url", "id", "username", "email", "avatar", "first_name", "last_name", "tables_permissions"]

    def get_avatar(self, obj):
        try:
            request = self.context.get("request")
            avatar_url = obj.userprofile.avatar.url
            return request.build_absolute_uri(avatar_url)
        except:
            pass

    def get_tables_permissions(self, obj):
        tables = []

        checker = ObjectPermissionChecker(obj)

        for table in models.Table.objects.all():
            user_perms = checker.get_perms(table)

            if "change_table" in user_perms:
                table_perm = "Can edit"
            elif "view_table" in user_perms:
                table_perm = "Can view"
            else:
                table_perm = "No rights"
            tables.append({"name": table.name, "id": table.id, "permissions": table_perm})
        return tables


class UserListDataSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "avatar",
            "first_name",
            "last_name",
        ]

    def get_avatar(self, obj):
        try:
            request = self.context.get("request")
            avatar_url = obj.userprofile.avatar.url
            return request.build_absolute_uri(avatar_url)
        except:
            pass


class UserListSerializer(serializers.ModelSerializer):
    data = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "url",
            "id",
            "data"
        ]

    def get_data(self, obj):
        serializer = UserListDataSerializer(obj, context=self.context)
        return serializer.data


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "url",
            "id",
            "username",
            "email",
            "avatar",
            "first_name",
            "last_name",
        ]

    def get_avatar(self, obj):
        try:
            request = self.context.get("request")
            avatar_url = obj.userprofile.avatar.url
            return request.build_absolute_uri(avatar_url)
        except:
            pass


class OwnerSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ["url", "username", "first_name", "last_name"]
