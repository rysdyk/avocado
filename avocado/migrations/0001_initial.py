# -*- coding: utf-8 -*-


from django.db import migrations, models
import datetime
import avocado.query.oldparsers.datacontext
import jsonfield.fields
from django.conf import settings
import avocado.query.oldparsers.dataview


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DataCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('keywords', models.CharField(max_length=100, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('published', models.BooleanField(default=False)),
                ('archived', models.BooleanField(default=False, help_text='Note: archived takes precedence over being published')),
                ('order', models.FloatField(null=True, db_column='_order', blank=True)),
                ('parent', models.ForeignKey(related_name='children', blank=True, to='avocado.DataCategory', help_text='Sub-categories are limited to one-level deep', null=True)),
            ],
            options={
                'ordering': ('parent__order', 'parent__name', 'order', 'name'),
                'verbose_name_plural': 'data categories',
            },
        ),
        migrations.CreateModel(
            name='DataConcept',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('keywords', models.CharField(max_length=100, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name_plural', models.CharField(max_length=200, null=True, blank=True)),
                ('published', models.BooleanField(default=False)),
                ('archived', models.BooleanField(default=False, help_text='Note: archived takes precedence over being published')),
                ('type', models.CharField(max_length=100, null=True, blank=True)),
                ('order', models.FloatField(null=True, db_column='_order', blank=True)),
                ('formatter', models.CharField(blank=True, max_length=100, null=True, verbose_name='formatter', choices=[('Default', 'Default')])),
                ('viewable', models.BooleanField(default=True)),
                ('queryable', models.BooleanField(default=True)),
                ('sortable', models.BooleanField(default=True)),
                ('indexable', models.BooleanField(default=True)),
                ('category', models.ForeignKey(blank=True, to='avocado.DataCategory', null=True)),
            ],
            options={
                'ordering': ('category__order', 'category__name', 'order', 'name'),
                'permissions': (('view_dataconcept', 'Can view dataconcept'),),
            },
        ),
        migrations.CreateModel(
            name='DataConceptField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, null=True, blank=True)),
                ('name_plural', models.CharField(max_length=100, null=True, blank=True)),
                ('order', models.FloatField(null=True, db_column='_order', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('concept', models.ForeignKey(related_name='concept_fields', to='avocado.DataConcept')),
            ],
            options={
                'ordering': ('order', 'name'),
            },
        ),
        migrations.CreateModel(
            name='DataContext',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('keywords', models.CharField(max_length=100, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('json', jsonfield.fields.JSONField(default=dict, null=True, blank=True, validators=[avocado.query.oldparsers.datacontext.validate])),
                ('session', models.BooleanField(default=False)),
                ('template', models.BooleanField(default=False)),
                ('default', models.BooleanField(default=False)),
                ('session_key', models.CharField(max_length=40, null=True, blank=True)),
                ('accessed', models.DateTimeField(default=datetime.datetime(2017, 1, 11, 22, 1, 1, 250639), editable=False)),
                ('parent', models.ForeignKey(related_name='forks', blank=True, to='avocado.DataContext', null=True)),
                ('user', models.ForeignKey(related_name='datacontext+', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='DataField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('keywords', models.CharField(max_length=100, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name_plural', models.CharField(max_length=200, null=True, blank=True)),
                ('published', models.BooleanField(default=False)),
                ('archived', models.BooleanField(default=False, help_text='Note: archived takes precedence over being published')),
                ('app_name', models.CharField(max_length=200)),
                ('model_name', models.CharField(max_length=200)),
                ('field_name', models.CharField(max_length=200)),
                ('label_field_name', models.CharField(help_text='Label field to the reference field', max_length=200, null=True, blank=True)),
                ('search_field_name', models.CharField(help_text='Search field to the reference field', max_length=200, null=True, blank=True)),
                ('order_field_name', models.CharField(help_text='Order field to the reference field', max_length=200, null=True, blank=True)),
                ('code_field_name', models.CharField(help_text='Order field to the reference field', max_length=200, null=True, blank=True)),
                ('unit', models.CharField(max_length=30, null=True, blank=True)),
                ('unit_plural', models.CharField(max_length=40, null=True, blank=True)),
                ('enumerable', models.BooleanField(default=False)),
                ('indexable', models.BooleanField(default=True)),
                ('type', models.CharField(help_text='Logical type of this field. Typically used downstream for defining behavior and semantics around the field.', max_length=100, null=True, blank=True)),
                ('translator', models.CharField(blank=True, max_length=100, null=True, choices=[('Default', 'Default')])),
                ('data_version', models.IntegerField(default=1, help_text='The current version of the underlying data for this field as of the last modification/update.')),
                ('order', models.FloatField(null=True, db_column='_order', blank=True)),
                ('category', models.ForeignKey(blank=True, to='avocado.DataCategory', null=True)),
                ('sites', models.ManyToManyField(related_name='_datafield_sites_+', to='sites.Site', blank=True)),
            ],
            options={
                'ordering': ('category__order', 'category__name', 'order', 'name'),
                'permissions': (('view_datafield', 'Can view datafield'),),
            },
        ),
        migrations.CreateModel(
            name='DataQuery',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('keywords', models.CharField(max_length=100, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('session', models.BooleanField(default=False)),
                ('template', models.BooleanField(default=False)),
                ('default', models.BooleanField(default=False)),
                ('session_key', models.CharField(max_length=40, null=True, blank=True)),
                ('accessed', models.DateTimeField(default=datetime.datetime.now, editable=False)),
                ('public', models.BooleanField(default=False)),
                ('context_json', jsonfield.fields.JSONField(default=dict, null=True, blank=True, validators=[avocado.query.oldparsers.datacontext.validate])),
                ('view_json', jsonfield.fields.JSONField(default=dict, null=True, blank=True, validators=[avocado.query.oldparsers.dataview.validate])),
                ('parent', models.ForeignKey(related_name='forks', blank=True, to='avocado.DataQuery', null=True)),
                ('shared_users', models.ManyToManyField(related_name='_dataquery_shared_users_+', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='dataquery+', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'verbose_name_plural': 'data queries',
            },
        ),
        migrations.CreateModel(
            name='DataView',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('keywords', models.CharField(max_length=100, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('json', jsonfield.fields.JSONField(default=dict, null=True, blank=True, validators=[avocado.query.oldparsers.dataview.validate])),
                ('session', models.BooleanField(default=False)),
                ('template', models.BooleanField(default=False)),
                ('default', models.BooleanField(default=False)),
                ('session_key', models.CharField(max_length=40, null=True, blank=True)),
                ('accessed', models.DateTimeField(default=datetime.datetime(2017, 1, 11, 22, 1, 1, 252000), editable=False)),
                ('parent', models.ForeignKey(related_name='forks', blank=True, to='avocado.DataView', null=True)),
                ('user', models.ForeignKey(related_name='dataview+', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField(null=True, blank=True)),
                ('event', models.CharField(max_length=200)),
                ('data', jsonfield.fields.JSONField(null=True, blank=True)),
                ('session_key', models.CharField(max_length=40, null=True, blank=True)),
                ('timestamp', models.DateTimeField(default=datetime.datetime.now)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('user', models.ForeignKey(related_name='+', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Revision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField(db_index=True)),
                ('data', jsonfield.fields.JSONField(null=True, blank=True)),
                ('session_key', models.CharField(max_length=40, null=True, blank=True)),
                ('timestamp', models.DateTimeField(default=datetime.datetime.now, db_index=True)),
                ('deleted', models.BooleanField(default=False)),
                ('changes', jsonfield.fields.JSONField(null=True, blank=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user', models.ForeignKey(related_name='revision', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-timestamp',),
                'get_latest_by': 'timestamp',
            },
        ),
        migrations.AddField(
            model_name='dataconceptfield',
            name='field',
            field=models.ForeignKey(related_name='concept_fields', to='avocado.DataField'),
        ),
        migrations.AddField(
            model_name='dataconcept',
            name='fields',
            field=models.ManyToManyField(related_name='concepts', through='avocado.DataConceptField', to='avocado.DataField'),
        ),
        migrations.AddField(
            model_name='dataconcept',
            name='sites',
            field=models.ManyToManyField(related_name='_dataconcept_sites_+', to='sites.Site', blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='datafield',
            unique_together=set([('app_name', 'model_name', 'field_name')]),
        ),
    ]
