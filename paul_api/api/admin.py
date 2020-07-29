from django.contrib import admin
from api import models
from eav.admin import BaseEntityInline, BaseEntityAdmin
from eav.forms import BaseDynamicEntityForm

@admin.register(models.Database)
class DatabaseAdmin(admin.ModelAdmin):
    list_display = ("name",)
    list_filter = ()
    search_fields = ("name",)


class TableColumnInline(admin.TabularInline):
    model = models.TableColumn
    fields = ("name", "column_type")
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
    list_display = ('table', 'values')
    form = EntryAdminForm
    list_filter = ('table__name',)


    def values(self, obj):
        print(dir(obj.eav))
        return obj.eav.get_values_dict()


@admin.register(models.Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("name", "database", "columns", "entries")
    list_filter = ('database__name', )
    search_fields = ("name",)
    inlines = (TableColumnInline, )

    def columns(self, obj):
        return obj.columns.count()

    def entries(self, obj):
        return obj.entries.count()
