from django.db.models import (
    Count, Sum, Min, Max, Avg,
    DateTimeField, CharField, FloatField, IntegerField)
from django.db.models.functions import Trunc, Cast
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.urls import reverse


from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template

from collections import OrderedDict
import inflection

# from api.views import FilterViewSet
from . import models

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import requests
from pprint import pprint

DB_FUNCTIONS = {
    "Count": Count,
    "Sum": Sum,
    "Min": Min,
    "Max": Max,
    "Avg": Avg,
}

def send_email(template, context, subject, to):
    html = get_template(template)
    html_content = html.render(context)

    msg = EmailMultiAlternatives(subject, html_content, settings.NO_REPLY_EMAIL, [to])
    msg.attach_alternative(html_content, "text/html")

    return msg.send()


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


def get_chart_data(request, chart, table, preview=False):
    y_axis_function = DB_FUNCTIONS[chart.y_axis_function]

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

    chart_data = models.Entry.objects \
        .filter(table=chart.table) \
        .filter(**filter_dict)
    if preview:
        chart_data = chart_data[:100]

    if chart.timeline_field:

        chart_data = chart_data.annotate(date_field=Cast(
                KeyTextTransform(chart.timeline_field.name, "data"), DateTimeField()
            )) \
            .annotate(time=Trunc('date_field', chart.timeline_period.lower(), is_dst=False)) \
            .values('time')
    else:
        chart_data = chart_data \
            .annotate(series=Cast(
                KeyTextTransform(chart.x_axis_field.name, "data"), CharField()))
        if chart.x_axis_field_2:
            chart_data = chart_data \
                .annotate(series_group=Cast(
                    KeyTextTransform(chart.x_axis_field_2.name, "data"), CharField()))\
                .values('series', 'series_group')
        else:
            chart_data = chart_data.values('series')

    # if we have Y axis field
    if chart.y_axis_field:
        chart_data = chart_data \
            .annotate(value=y_axis_function(Cast(
                KeyTextTransform(chart.y_axis_field.name, "data"), FloatField()
            )))
    else:
        chart_data = chart_data.annotate(value=Count('id'))

    # if we have X axis field
    if chart.x_axis_field and chart.timeline_field:
        chart_data = chart_data \
            .annotate(series=Cast(
                KeyTextTransform(chart.x_axis_field.name, "data"), CharField()
            ))
        if chart.x_axis_field_2:
            chart_data = chart_data \
                .annotate(series_group=Cast(
                    KeyTextTransform(chart.x_axis_field_2.name, "data"), CharField()))\
                .values('time', 'series', 'series_group', 'value')
        else:
            chart_data = chart_data.values('time', 'value', 'series')
    elif chart.x_axis_field:
        if chart.x_axis_field_2:
            chart_data = chart_data.values('series', 'series_group', 'value')
        else:
            chart_data = chart_data.values('series', 'value')

    if chart.timeline_field:
        chart_data = chart_data.order_by('time')
        data = prepare_chart_data(chart, chart_data, timeline=True)

    else:
        chart_data = chart_data.order_by('data__' +  chart.x_axis_field.name)
        data = prepare_chart_data(chart, chart_data, timeline=False)

    return data

def get_strftime(date, period):
    if not date:
        return None
    if period == 'year':
        date_str = date.strftime('%Y')
    elif period == 'month':
        date_str = date.strftime('%Y-%m')
    elif period == 'week':
        date_str = date.strftime('%Y-%V')
    elif period == 'day':
        date_str = date.strftime('%Y-%m-%d')
    elif period == 'hour':
        date_str = date.strftime('%Y-%m-%d %H')
    elif period == 'minute':
        date_str = date.strftime('%Y-%m-%d %H:%M')
    return date_str


def get_strptime(date_str, period):
    if period == 'year':
        date = datetime.strptime(date_str, '%Y')
    elif period == 'month':
        date = datetime.strptime(date_str, '%Y-%m')
    elif period == 'week':
        date = datetime.strptime(date_str + '-1', '%G-%V-%w')
    elif period == 'day':
        date = datetime.strptime(date_str, '%Y-%m-%d')
    elif period == 'hour':
        date = datetime.strptime(date_str, '%Y-%m-%d %H')
    elif period == 'minute':
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
    return date


def prepare_chart_data(chart, chart_data, timeline=True):
    data_dict = {}
    timeline_period = chart.timeline_period
    data = {
        'labels': [],
        'datasets': [{
            'label': '',
            'data': []
        }],
        # 'options': {}
    }
    colors = ['#223E6D','#87C700','#8E0101','#FF6231','#175B1E','#A2D3E4','#4B0974','#ED1A3B','#0081BB','#9CCB98','#DF3D84','#FD7900','#589674','#C2845D','#AA44E8','#EFAD88','#8590FF','#00B3A8','#FF8DB8','#FBB138']
    colors.reverse()
    if timeline == False:
        has_series_group = False
        for entry in chart_data:
            if 'series_group' in entry.keys():
                has_series_group = True
                data_dict.setdefault(entry['series'], {})
                data_dict[entry['series']].setdefault(entry['series_group'], 0)
                data_dict[entry['series']][entry['series_group']] = entry['value']
            else:
                data_dict.setdefault(entry['series'], 0)
                data_dict[entry['series']] = entry['value']
        if not has_series_group:
            i = 0
            data['datasets'][0]['backgroundColor'] = []
            for key, value in data_dict.items():
                i += 1
                data['labels'].append(key)
                if chart.x_axis_field:
                    data['datasets'][0]['label'] = chart.x_axis_field.display_name
                data['datasets'][0]['data'].append(value)
                if chart.chart_type in ['Pie', 'Doughnut']:
                    data['datasets'][0]['backgroundColor'].append(colors[i%20])
                elif chart.chart_type in ['Line']:
                    data['datasets'][0]['backgroundColor'] = 'rgba(0, 0, 0, 0)'
                    data['datasets'][0]['borderColor'] = colors[0]
                else:
                    data['datasets'][0]['backgroundColor'] = colors[0]
        else:
            data['datasets'] = []
            labels = []
            labels_dict = {}
            for serie, group in data_dict.items():
                data['labels'].append(serie)
                for group_name in group:
                    if group_name not in labels:
                        labels.append(group_name)
            for serie, group in data_dict.items():
                for label in labels:
                    labels_dict.setdefault(label, [])
                    labels_dict[label].append(group.get(label, 0))

            i = 0
            for label, label_values in labels_dict.items():
                i += 1
                if chart.chart_type == 'Line':
                    dataset = {
                        'label': label,
                        'data': label_values,
                        'backgroundColor': 'rgba(0, 0, 0, 0)',
                        'borderColor': colors[i % 10]
                    }
                else:
                    dataset = {
                        'label': label,
                        'data': label_values,
                        'backgroundColor': colors[i % 10]
                    }
                data['datasets'].append(dataset)
    else:
        labels = []
        labels_dict = {}

        for entry in chart_data:
            time = get_strftime(entry['time'], timeline_period)
            data_dict.setdefault(time, {})
            data_dict[time][entry.get('series', '')] = entry['value']
            if entry.get('series', '') not in labels:
                labels.append(entry.get('series', ''))

        if chart.timeline_include_nulls:
            first_entry = list(data_dict)[0]
            last_entry = get_strptime(list(data_dict)[-1], timeline_period)
            relativetime_increment = {}
            relativetime_increment[timeline_period + 's'] = 1

            time_period = get_strptime(first_entry, timeline_period)

            ordered_data_dict = OrderedDict()
            while time_period <= last_entry:
                time_period_str = get_strftime(time_period, timeline_period)
                data_dict.setdefault(time_period_str, {})
                ordered_data_dict[time_period_str] = data_dict[time_period_str]
                time_period += relativedelta(**relativetime_increment)
            data_dict = ordered_data_dict

        for key, value in data_dict.items():
            data['labels'].append(key)

            for label in labels:
                labels_dict.setdefault(label, [])
                labels_dict[label].append(value.get(label, 0))

        data['datasets'] = []
        i = 0
        for label, label_values in labels_dict.items():
            i += 1
            if chart.chart_type == 'Line':
                dataset = {
                    'label': label,
                    'data': label_values,
                    'backgroundColor': 'rgba(0, 0, 0, 0)',
                    'borderColor': colors[i % 10]
                }
            else:
                dataset = {
                    'label': label,
                    'data': label_values,
                    'backgroundColor': colors[i % 10]
                }
            data['datasets'].append(dataset)

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
            x_axis_label = '{} ({})'.format(chart.timeline_field.display_name, timeline_period.capitalize())
        else:
            x_axis_label = chart.table.name

    data['options'] = {
        'maintainAspectRatio': False,
        'tooltips': {
            'mode': 'index',
            'position': 'nearest'
        },
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
        } if chart.chart_type not in ['Pie', 'Doughnut'] else {}
      }
    # pprint(data)
    return data
