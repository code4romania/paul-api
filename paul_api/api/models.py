from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ValidationError
import uuid


datatypes = (
    ("int", "int"),
    ("float", "float"),
    ("text", "text"),
    ("date", "date"),
    ("bool", "bool"),
    ("object", "object"),
    ("enum", "enum"),
)


class Userprofile(models.Model):
    """
    Description: Model Description
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="userprofile"
    )

    dashboard_filters = models.ManyToManyField('Filter')
    token = models.UUIDField(default=uuid.uuid4)
    avatar = models.ImageField(upload_to="avatars", null=True, blank=True)

    class Meta:
        pass


class Database(models.Model):
    """
    Description: Model Description
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, null=True, blank=True)

    class Meta:
        pass

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        value = self.name
        self.slug = slugify(value, allow_unicode=True)
        super().save(*args, **kwargs)

    def active_tables(self):
        return self.tables.filter(active=True)

    def archived_tables(self):
        return self.tables.filter(active=False)

    def tables_count(self):
        return self.tables.count()


class Table(models.Model):
    """
    Description: Model Description
    """

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, null=True, blank=True)
    database = models.ForeignKey(
        "Database", on_delete=models.CASCADE, related_name="tables"
    )
    active = models.BooleanField(default=False)

    date_created = models.DateTimeField(auto_now_add=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    last_edit_date = models.DateTimeField(null=True, blank=True)
    last_edit_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="last_table_edits",
    )

    class Meta:
        permissions = (
            ("view", "View"),
            ("change", "View"),
            ("delete", "View"),
        )
        unique_together = ["name", "database"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        value = self.name
        self.slug = slugify(value, allow_unicode=True)
        self.last_edit_date = timezone.now()
        super().save(*args, **kwargs)

    def entries_count(self):
        return self.entries.count()


class TableColumn(models.Model):
    """
    Description: Model Description
    """

    table = models.ForeignKey(
        "Table", on_delete=models.CASCADE, related_name="fields"
    )
    name = models.CharField(max_length=50, null=True, blank=True)
    display_name = models.CharField(max_length=50, null=True, blank=True)
    slug = models.SlugField(max_length=50, null=True, blank=True)
    field_type = models.CharField(max_length=20, choices=datatypes)
    help_text = models.CharField(max_length=255, null=True, blank=True)
    choices = ArrayField(
        models.CharField(max_length=100), null=True, blank=True
    )
    required = models.BooleanField(default=False)
    unique = models.BooleanField(default=False)

    class Meta:
        unique_together = ["table", "name"]

    def __str__(self):
        return "[{}] {} ({})".format(self.table, self.name, self.field_type)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)


class CsvFieldMap(models.Model):
    """
    Description: Model Description
    """

    table = models.ForeignKey(
        "Table", on_delete=models.CASCADE, related_name="csv_field_mapping",
        null=True, blank=True
    )
    csv_import = models.ForeignKey(
        "CsvImport", on_delete=models.CASCADE, related_name="csv_field_mapping",
        null=True, blank=True
    )
    original_name = models.CharField(max_length=100)
    field_name = models.CharField(max_length=100)
    field_type = models.CharField(
        max_length=20, choices=datatypes, default=datatypes[0]
    )
    field_format = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        pass


class CsvImport(models.Model):
    """
    Description: Model Description
    """

    file = models.FileField(upload_to="csvs/")
    delimiter = models.CharField(
        max_length=2, default=';',
        null=True, blank=True
    )
    table = models.ForeignKey(
        "Table", related_name="csv_imports", on_delete=models.CASCADE,
        null=True, blank=True
    )

    errors = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    errors_count = models.IntegerField(default=0)
    imports_count = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        pass


class Entry(models.Model):
    """
    Description: Model Description
    """

    table = models.ForeignKey(
        "Table", on_delete=models.CASCADE, related_name="entries"
    )
    data = models.JSONField(encoder=DjangoJSONEncoder, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Entries"

    def __str__(self):
        return self.table.name

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        fields = {x.name: x for x in self.table.fields.all()}

        for field, field_obj in fields.items():
            value = self.data.get(field, None)
            if field_obj.required:
                if not value or value == "":
                    # raise ValidationError({
                    #     field: 'This field is required'
                    #     })
                    raise ValidationError("{} field is required".format(field))
            if field_obj.field_type == "enum":
                if value not in field_obj.choices:
                    raise ValidationError(
                        "{} field value must be one of: {}".format(
                            field, ", ".join(field_obj.choices)
                        )
                    )


class FilterJoinTable(models.Model):
    """
    Description: Model Description
    """

    filter = models.ForeignKey(
        "Filter", on_delete=models.CASCADE, related_name="filter_join_tables"
    )
    table = models.ForeignKey(Table, on_delete=models.CASCADE)
    fields = models.ManyToManyField(
        TableColumn, related_name="filter_join_table_fields"
    )
    join_field = models.ForeignKey(TableColumn, on_delete=models.CASCADE)

    class Meta:
        pass


class Filter(models.Model):
    """
    Description: Model Description
    """

    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, null=True, blank=True)
    primary_table = models.ForeignKey(Table, on_delete=models.CASCADE)
    primary_table_fields = models.ManyToManyField(
        TableColumn, related_name="filter_primary_table_field"
    )
    join_field = models.ForeignKey(
        TableColumn,
        on_delete=models.CASCADE,
        related_name="filter_primary_table_join_field",
    )
    join_tables = models.ManyToManyField(
        Table, through=FilterJoinTable, related_name="filter_join_table"
    )
    creation_date = models.DateTimeField(auto_now_add=True, null=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    last_edit_date = models.DateTimeField(null=True, blank=True)
    last_edit_user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="last_filter_edits",
    )

    class Meta:
        pass

    def save(self, *args, **kwargs):
        value = self.name
        self.slug = slugify(value, allow_unicode=True)
        super().save(*args, **kwargs)
