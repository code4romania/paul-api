from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User
import eav

datatypes = (
    ("int", "int"),
    ("float", "float"),
    ("text", "text"),
    ("date", "date"),
    ("bool", "bool"),
    ("object", "object"),
    ("enum", "enum"),
)


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
    database = models.ForeignKey("Database", on_delete=models.CASCADE, related_name="tables")
    active = models.BooleanField(default=False)

    date_created = models.DateTimeField(auto_now_add=True)

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    last_edit_date = models.DateTimeField(null=True, blank=True)
    last_edit_user = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="last_table_edits",
    )

    class Meta:
        permissions = (
            ("view", "View"),
            ("change", "View"),
            ("delete", "View"),
        )

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

    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, null=True, blank=True)
    field_type = models.CharField(max_length=20, choices=datatypes)

    table = models.ForeignKey("Table", on_delete=models.CASCADE, related_name="fields")

    class Meta:
        unique_together = ["table", "slug"]

    def __str__(self):
        return "{} [{}]".format(self.name, self.field_type)


class Entry(models.Model):
    """
    Description: Model Description
    """

    table = models.ForeignKey("Table", on_delete=models.CASCADE, related_name="entries")
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Entries"

    def __str__(self):
        return self.table.name


eav.register(Entry)
