from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.contrib.admin.utils import flatten_fieldsets
from api import models, forms
from pprint import pprint

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
    fields = ("name", "field_type", "slug", "required", "unique", "choices", "help_text")
    can_delete = True
    can_add = False
    verbose_name_plural = "Columns"
    extra = 0


# class EntryAdminForm(BaseDynamicEntityForm):
#     model = models.Entry


# @admin.register(models.Entry)
# class EntriesInline(BaseEntityAdmin):
#     form = EntryAdminForm


class EntryAdminForm(forms.BaseDynamicEntityForm):
    model = models.Entry

from django.utils.safestring import mark_safe
class BaseEntityAdmin(admin.ModelAdmin):
    def render_change_form(self, request, context, *args, **kwargs):
        """
        Wrapper for ``ModelAdmin.render_change_form``. Replaces standard static
        ``AdminForm`` with an EAV-friendly one. The point is that our form
        generates fields dynamically and fieldsets must be inferred from a
        prepared and validated form instance, not just the form class. Django
        does not seem to provide hooks for this purpose, so we simply wrap the
        view and substitute some data.
        """
        form = context['adminform'].form

        # Infer correct data from the form.
        fieldsets = self.fieldsets or [(None, {'fields': form.fields.keys()})]
        adminform = admin.helpers.AdminForm(form, fieldsets, self.prepopulated_fields)
        media = mark_safe(self.media + adminform.media)

        context.update(adminform=adminform, media=media)

        return super(BaseEntityAdmin, self).render_change_form(
            request, context, *args, **kwargs
        )


@admin.register(models.Entry)
class EntryAdmin(BaseEntityAdmin):
    list_display = ("table", "data")
    exclude= ()
    # readonly_fields = ('table', )
    form = EntryAdminForm
    list_filter = ("table__name",)


    # def get_form(self, request, obj=None, **kwargs):
    #     # By passing 'fields', we prevent ModelAdmin.get_form from
    #     # looking up the fields itself by calling self.get_fieldsets()
    #     # If you do not do this you will get an error from 
    #     # modelform_factory complaining about non-existent fields.

    #     # use this line only for django before 1.9 (but after 1.5??)
    #     kwargs['fields'] =  flatten_fieldsets(self.fieldsets)

    #     return super(EntryAdmin, self).get_form(request, obj, **kwargs)

    # def get_fieldsets(self, request, obj=None):
    #     fieldsets = super(EntryAdmin, self).get_fieldsets(request, obj)

    #     newfieldsets = list(fieldsets)
    #     fields =  [x for x in self.instance.table.fields.values_list('name', flat=True)]
    #     newfieldsets.append(['Dynamic Fields', { 'fields': fields }])

    #     return newfieldsets

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
        for table in obj.filter_join_tables.all():
            tables[table.table.name] = ', '.join(table.fields.values_list('name', flat=True))
        pprint(tables)
        return ', '.join(['{} ({})'.format(t, f) for t, f in tables.items()])
