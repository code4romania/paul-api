import inflection
from . import models

from datetime import datetime


def snake_case(text):
    return inflection.underscore(inflection.parameterize(text))


def import_csv(reader, table):
    errors_count = 0
    imports_count = 0
    errors = []
    csv_field_mapping = {x.original_name: x for x in table.csv_field_mapping.all()}
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
                            value = datetime.strptime(row[key], field.field_format)
                            entry_dict[field_name] = value
                        elif field.field_type == "enum":
                            value = row[key]
                            if not field_choices[field_name]:
                                print("not")
                                field_choices[field_name] = []
                            if value not in field_choices[field_name]:
                                field_choices[field_name].append(value)
                                table_fields[field_name].choices = list(set(field_choices[field_name]))
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


def prepare_chart_data(chart, chart_data, timeline=True):
    data_dict = {}
    data = {
        'labels': [],
        'datasets': [{
            'label': '',
            'data': []
        }],
        'options': {}
    }
    # colors = ["#e3713c","#b4dfe5","#303c6c","#fbe8a6","#d2fdff","#c59fc9","#dbbadd","#fffc31","#ffcb47","#fc60a8"]
    colors = ['#223E6D','#87C700','#8E0101','#FF6231','#175B1E','#A2D3E4','#4B0974','#ED1A3B','#0081BB','#9CCB98','#DF3D84','#FD7900','#589674','#C2845D','#AA44E8','#EFAD88','#8590FF','#00B3A8','#FF8DB8','#FBB138']
    colors.reverse()
    if timeline == False:
        for entry in chart_data:
            data_dict.setdefault(entry['series'], 0)
            data_dict[entry['series']] = entry['value']

        for key, value in data_dict.items():
            data['labels'].append(key)
            if chart.x_axis_field:
                data['datasets'][0]['label'] = chart.x_axis_field.display_name
            data['datasets'][0]['data'].append(value)
            data['datasets'][0]['backgroundColor'] = colors[0]

    else:
        labels = []
        labels_dict = {}

        for entry in chart_data:
            if chart.timeline_period == 'year':
                time = entry['time'].year
            elif chart.timeline_period == 'month':
                time = entry['time'].strftime('%Y-%m')
            elif chart.timeline_period == 'week':
                time = entry['time'].strftime('%Y-%V')
            elif chart.timeline_period == 'day':
                time = entry['time'].strftime('%Y-%m-%d')
            elif chart.timeline_period == 'hour':
                time = entry['time'].strftime('%Y-%m-%d %H')
            elif chart.timeline_period == 'minute':
                time = entry['time'].strftime('%Y-%m-%d %H:%M')
            data_dict.setdefault(time, {})
            data_dict[time][entry.get('series', '')] = entry['value']
            if entry.get('series', '') not in labels:
                labels.append(entry.get('series', ''))
        # pprint(data_dict)

        for key, value in data_dict.items():
            data['labels'].append(key)

            for label in labels:
                labels_dict.setdefault(label, [])
                labels_dict[label].append(value.get(label, 0))
        data['datasets'] = []
        i = 0
        for label, label_values in labels_dict.items():
            i += 1
            data['datasets'].append(
                {
                    'label': label,
                    'data': label_values,
                    'backgroundColor': colors[i%10]
                })

    if chart.y_axis_field:
        y_axis_label = '{} ({})'.format(chart.y_axis_function, chart.y_axis_field.display_name)
    else:
        y_axis_label = chart.y_axis_function
    if chart.x_axis_field:
        if chart.timeline_field:
            x_axis_label = '{} ({})'.format(chart.x_axis_field.display_name, chart.timeline_field.display_name)
        else:
            x_axis_label = chart.x_axis_field.display_name
    else:
        if chart.timeline_field:
            x_axis_label = '{} ({})'.format(chart.timeline_field.display_name, chart.timeline_period.capitalize())
        else:
            x_axis_label = chart.table.name

    data['options'] = {
        'maintainAspectRatio': False,
        'scales': {
        'yAxes': [{
            'scaleLabel': {
                'display': True,
                'labelString': y_axis_label
            }
        }],
        'xAxes': [{
            'scaleLabel': {
                'display': True,
                'labelString': x_axis_label
            }
        }]
        }
      }
    return data
