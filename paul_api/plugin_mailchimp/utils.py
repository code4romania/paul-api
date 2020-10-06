from django.contrib.auth.models import User
from django.utils import timezone
from api import models
from mailchimp3 import MailChimp
from pprint import pprint



from . import table_fields


def get_or_create_table(table_type, table_name):
    db = models.Database.objects.last()
    user, _ = User.objects.get_or_create(username='paul-sync')

    table, created = models.Table.objects.get_or_create(
        name=table_name,
        database=db,
        owner=user)
    table.last_edit_date = timezone.now()
    table.last_edit_user = user
    table.active = True
    table.save()

    if created:
        table_fields_defs = table_fields.TABLE_MAPPING[table_type]
        for field_name, field_details in table_fields_defs.items():
            column, _ = models.TableColumn.objects.get_or_create(
                table=table,
                name=field_name
                )
            column.display_name = field_details['display_name']
            column.field_type = field_details['type']
            column.save()

    return table


def run_sync(key,
             audiences_table_name,
             audiences_stats_table_name,
             audience_segments_table_name,
             audience_members_table_name,
             segment_members_table_name):
    '''
    Do the actual sync.

    Return success (bool), updates(json), errors(json)
    '''
    success = True
    stats = {
        'audiences': {
            'created': 0,
            'updated': 0,
        },
        'audiences_stats': {
            'created': 0,
            'updated': 0,
        },
        'audience_segments': {
            'created': 0,
            'updated': 0,
        },
        'audience_members': {
            'created': 0,
            'updated': 0,
        },
        'segment_members': {
            'created': 0,
            'updated': 0,
        }

    }
    client = MailChimp(key)
    lists = client.lists.all()

    audiences_table = get_or_create_table('audiences', audiences_table_name)
    audiences_stats_table = get_or_create_table('audiences_stats', audiences_stats_table_name)
    audience_segments_table = get_or_create_table('audience_segments', audience_segments_table_name)
    audience_members_table = get_or_create_table('audience_members', audience_members_table_name)
    segment_members_table = get_or_create_table('segment_members', segment_members_table_name)

    audiences_table_fields_defs = table_fields.TABLE_MAPPING['audiences']
    audiences_stats_table_fields_defs = table_fields.TABLE_MAPPING['audiences_stats']
    audience_segments_table_fields_defs = table_fields.TABLE_MAPPING['audience_segments']
    audience_members_table_fields_defs = table_fields.TABLE_MAPPING['audience_members']
    segment_members_table_fields_defs = table_fields.TABLE_MAPPING['segment_members']

    for list in lists['lists']:
        print('List:', list['name'])
        # Sync lists
        audience_exists = models.Entry.objects.filter(
            table=audiences_table, data__id=list['id'])

        if audience_exists:
            audience_entry = audience_exists[0]
            stats['audiences']['updated'] += 1
        else:
            stats['audiences']['created'] += 1
            audience_entry = models.Entry.objects.create(
                table=audiences_table,
                data={'id': list['id']})

        for field in audiences_table_fields_defs:
            try:
                audience_entry.data[field] = list[field]
            except:
                field_def = audiences_table_fields_defs[field]
                audience_entry.data[field] = list[field_def['mailchimp_parent_key_name']][field_def['mailchimp_key_name']]

        audience_entry.save()

        # Sync list stats
        audience_stats_exists = models.Entry.objects.filter(
            table=audiences_stats_table, data__audience_id=list['id'])
        if audience_stats_exists:
            audience_stats_entry = audience_stats_exists[0]
            stats['audiences_stats']['updated'] += 1
        else:
            stats['audiences_stats']['created'] += 1
            audience_stats_entry = models.Entry.objects.create(
                table=audiences_stats_table,
                data={
                    'audience_id': list['id'],
                    'audience_name': list['name']
                    })
        for field in audiences_stats_table_fields_defs:
            try:
                audience_stats_entry.data[field] = list['stats'][field]
            except:
                pass

        audience_stats_entry.save()

        # Sync list segments
        list_segments = client.lists.segments.all(list_id=list['id'], get_all=True)

        for segment in list_segments['segments']:
            print('     Segment:', segment['name'])
            audience_segments_exists = models.Entry.objects.filter(
                table=audience_segments_table, data__audience_id=segment['list_id'])
            if audience_segments_exists:
                audience_segments_entry = audience_segments_exists[0]
                stats['audience_segments']['updated'] += 1
            else:
                stats['audience_segments']['created'] += 1
                audience_segments_entry = models.Entry.objects.create(
                    table=audience_segments_table,
                    data={
                        'audience_id': segment['list_id'],
                        'audience_name': list['name']
                        })
            for field in audience_segments_table_fields_defs:
                try:
                    audience_segments_entry.data[field] = segment[field]
                except:
                    pass

            audience_segments_entry.save()

            # Sync segment members
            segment_members = client.lists.segments.members.all(list_id=list['id'], segment_id=segment['id'], get_all=True)

            for member in segment_members['members']:
                print('         Segment member:', member['email_address'])
                segment_members_exists = models.Entry.objects.filter(
                    table=segment_members_table, data__id=member['id'], data__segment_id=segment['id'])
                if segment_members_exists:
                    segment_members_entry = segment_members_exists[0]
                    stats['segment_members']['updated'] += 1
                else:
                    stats['segment_members']['created'] += 1
                    segment_members_entry = models.Entry.objects.create(
                        table=segment_members_table,
                        data={
                            'audience_id': member['list_id'],
                            'segment_id': segment['id'],
                            'audience_name': list['name'],
                            'segment_name': segment['name']
                            })
                for field in segment_members_table_fields_defs:
                    field_def = segment_members_table_fields_defs[field]
                    if field in member.keys():
                        if field_def['type'] == 'enum':
                            table_column = models.TableColumn.objects.get(table=segment_members_table, name=field)
                            if not table_column.choices:
                                table_column.choices = []
                            if 'is_list' in field_def.keys():
                                for item in member[field]:
                                    if item not in table_column.choices:
                                        table_column.choices.append(item)
                                        table_column.save()
                            else:
                                if member[field] not in table_column.choices:
                                    table_column.choices.append(member[field])
                                    table_column.save()
                        if 'is_list' in field_def.keys():
                            segment_members_entry.data[field] = ','.join(member[field])
                        else:
                            segment_members_entry.data[field] = member[field]
                    else:
                        try:
                            segment_members_entry.data[field] = member[field_def['mailchimp_parent_key_name']][field_def['mailchimp_key_name']]
                        except Exception as e:
                                pass

                segment_members_entry.save()

        # # Sync list members
        list_members = client.lists.members.all(list_id=list['id'], get_all=True)

        for member in list_members['members']:
            print('     List member:', member['email_address'])
            audience_members_exists = models.Entry.objects.filter(
                table=audience_members_table, data__id=member['id'], data__audience_id=list['id'])
            if audience_members_exists:
                audience_members_entry = audience_members_exists[0]
                stats['audience_members']['updated'] += 1
            else:
                stats['audience_members']['created'] += 1
                audience_members_entry = models.Entry.objects.create(
                    table=audience_members_table,
                    data={
                        'audience_id': member['list_id'],
                        'audience_name': list['name']
                        })
            for field in audience_members_table_fields_defs:
                field_def = audience_members_table_fields_defs[field]
                if field in member.keys():
                    if field_def['type'] == 'enum':
                        table_column = models.TableColumn.objects.get(table=audience_members_table, name=field)
                        if not table_column.choices:
                            table_column.choices = []
                        if 'is_list' in field_def.keys():
                            for item in member[field]:
                                if item not in table_column.choices:
                                    table_column.choices.append(item)
                                    table_column.save()
                        else:
                            if member[field] not in table_column.choices:
                                table_column.choices.append(member[field])
                                table_column.save()
                    if 'is_list' in field_def.keys():
                        audience_members_entry.data[field] = ','.join(member[field])
                    else:
                        audience_members_entry.data[field] = member[field]
                else:
                    try:
                        audience_members_entry.data[field] = member[field_def['mailchimp_parent_key_name']][field_def['mailchimp_key_name']]
                    except Exception as e:
                        pass

            audience_members_entry.save()
    return success, stats
