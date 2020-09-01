import inflection
from . import models

from datetime import datetime


def snake_case(text):
    return inflection.underscore(inflection.parameterize(text))


def import_csv(reader, table):
    errors_count = 0
    imports_count = 0
    errors = []
    csv_field_mapping = {
        x.original_name: x for x in table.csv_field_mapping.all()
    }
    table_fields = {x.name: x for x in table.fields.all()}
    field_choices = {x.name: x.choices for x in table.fields.all()}
    i = 0

    for row in reader:
        i += 1
        print(i)
        # if i > 100:
        #     continue
        entry_dict = {}
        error_in_row = False
        errors_in_row = {}
        try:
            for key, field in csv_field_mapping.items():
                field_name = snake_case(field.field_name)
                try:
                    if row[key]:
                        if field.field_type == "int":
                            entry_dict[field_name] = int(row[key])
                        elif field.field_type == "float":
                            entry_dict[field_name] = float(row[key])
                        elif field.field_type == "date":
                            value = datetime.strptime(
                                row[key], field.field_format
                            )
                            entry_dict[field_name] = value
                        elif field.field_type == "enum":
                            value = row[key]
                            if not field_choices[field_name]:
                                print('not')
                                field_choices[field_name] = []
                            if value not in field_choices[field_name]:
                                field_choices[field_name].append(value)
                                table_fields[field_name].choices = list(
                                    set(field_choices[field_name])
                                )
                                table_fields[field_name].save()
                            entry_dict[field_name] = value
                        else:
                            entry_dict[field_name] = row[key]
                    else:
                        if table_fields[field_name].required:
                            error_in_row = True
                            errors_in_row[key] = "This field is required"
                        entry_dict[field_name] = None
                except Exception as e:
                    print(e)
                    error_in_row = True
                    errors_in_row[key] = e.__class__.__name__
            if not error_in_row:
                models.Entry.objects.create(table=table, data=entry_dict)
                imports_count += 1
            else:
                errors.append({"row": row, "errors": errors_in_row})
                errors_count += 1

        except Exception as e:
            print("=====", e)
            errors_count += 1

    print("errors: {} imports: {}".format(errors_count, imports_count))
    return errors, errors_count, imports_count
