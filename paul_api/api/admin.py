from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from api import models
from eav.admin import BaseEntityInline, BaseEntityAdmin
from eav.forms import BaseDynamicEntityForm


class UserprofileAdmin(admin.TabularInline):
    model = models.Userprofile
    fields = ("avatar", "token")
    readonly_field = ("token",)
    can_delete = False
    can_add = False
    extra = 0


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (UserprofileAdmin,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(models.Database)
class DatabaseAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    list_filter = ()
    search_fields = ("name",)


class TableColumnInline(admin.TabularInline):
    model = models.TableColumn
    fields = ("name", "field_type")
    can_delete = False
    can_add = False
    verbose_name_plural = "Columns"
    extra = 0


# class EntryAdminForm(BaseDynamicEntityForm):
#     model = models.Entry


# @admin.register(models.Entry)
# class EntriesInline(BaseEntityAdmin):
#     form = EntryAdminForm


class EntryAdminForm(BaseDynamicEntityForm):
    model = models.Entry


@admin.register(models.Entry)
class EntryAdmin(BaseEntityAdmin):
    list_display = ("table", "values")
    form = EntryAdminForm
    list_filter = ("table__name",)

    def values(self, obj):
        print(dir(obj.eav))
        return obj.eav.get_values_dict()


@admin.register(models.Table)
class TableAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "database",
        "columns",
        "entries",
        "last_edit_date",
        "last_edit_user",
        "active",
    )
    list_filter = ("database__name",)
    search_fields = ("name",)
    inlines = (TableColumnInline,)

    def columns(self, obj):
        return obj.fields.count()

    def entries(self, obj):
        return obj.entries.count()

    def save_model(self, request, obj, form, change):
        obj.last_edit_user = request.user
        super().save_model(request, obj, form, change)


class FilterJoinTableInline(admin.TabularInline):
    model = models.FilterJoinTable
    fields = ("table", "fields", "join_field",)
    can_delete = False
    # can_add = False
    verbose_name_plural = "Join Tables"
    # extra = 0


@admin.register(models.Filter)
class FilterAdmin(admin.ModelAdmin):
    list_display = ("primary_table", "get_primary_table_fields", "join_field", "get_join_tables")
    list_filter = ()
    search_fields = ()
    inlines = (FilterJoinTableInline,)

    def get_primary_table_fields(self, obj):
        return ', '.join(obj.primary_table_fields.values_list('name', flat=True))

    def get_join_tables(self, obj):
        tables = {}
        for table in obj.join_tables.all():
            tables[table.name] = ', '.join(table.fields.values_list('name', flat=True))
        return ', '.join(['{} ({})'.format(t, f) for t, f in tables.items()])
