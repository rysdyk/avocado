import re
import os
import sys
import tempfile
import logging
from django.apps import apps
from django.core import serializers, management
from django.core.exceptions import ImproperlyConfigured
from django.db import models, transaction, router, DEFAULT_DB_ALIAS, \
    DatabaseError, IntegrityError
from avocado.models import DataField, DataConcept, DataConceptField, \
    DataCategory

FIXTURE_FORMAT = 'json'
FIXTURE_FILENAME_RE = re.compile(r'^[0-9]{4}_[0-9a-zA-Z_]+(\.json)$')

MIGRATION_MODEL_LABELS = ('avocado.datafield', 'avocado.dataconcept',
                          'avocado.dataconceptfield', 'avocado.datacategory')

log = logging.getLogger(__name__)


def _check_app():
    from avocado.conf import settings
    app_name = settings.METADATA_MIGRATION_APP
    if not app_name or not apps.get_app_config(app_name.split('.')[-1]):
        raise ImproperlyConfigured('{0} is not a valid app name. The '
                                   'backup/migration API requires '
                                   'METADATA_MIGRATION_APP to be a valid '
                                   'app name to be used.'
                                   .format(settings.METADATA_MIGRATION_APP))


def _fixture_filenames(dirname):
    filenames = []
    for f in os.listdir(dirname):
        if FIXTURE_FILENAME_RE.match(os.path.basename(f)):
            filenames.append(f)
    filenames.sort()
    return filenames


def next_fixture_name(name, dirname):
    filenames = _fixture_filenames(dirname)
    if not filenames:
        version = '0001'
    else:
        version = str(int(filenames[-1][:4]) + 1).zfill(4)
    return '{0}_{1}'.format(version, name)


def full_fixture_path(name):
    return '{0}.{1}'.format(os.path.join(get_fixture_dir(), name),
                             FIXTURE_FORMAT)


def get_fixture_dir():
    from avocado.conf import settings
    _check_app()

    fixture_dir = settings.METADATA_FIXTURE_DIR
    if fixture_dir:
        return fixture_dir
    app = apps.get_app_config(settings.METADATA_MIGRATION_APP.split('.')[-1])
    return os.path.join(app.path, 'fixtures')


def create_fixture(name, using=DEFAULT_DB_ALIAS, silent=False):
    "Dumps data in the fixture format optionally to a particular path."
    if os.path.isabs(name):
        fixture_path = name
    else:
        fixture_path = full_fixture_path(name)
    with open(fixture_path, 'w') as fout:
        management.call_command('dumpdata', *MIGRATION_MODEL_LABELS,
                                database=using, stdout=fout)
    if not silent:
        log.info('Created fixture {0}'.format(name))


def create_temp_fixture(*args, **kwargs):
    "Creates a fixture to a temporary file."
    fh, path = tempfile.mkstemp()
    create_fixture(path, *args, **kwargs)
    return path


def load_fixture(name, using=DEFAULT_DB_ALIAS):
    """Progammatic way to load a fixture given some path. This does not
    assume the path is a fixture within some app and assumes a full path.
    """
    if os.path.isabs(name):
        fixture_path = name
    else:
        fixture_path = full_fixture_path(name)

    with open(fixture_path) as fixture:
        objects = serializers.deserialize(FIXTURE_FORMAT, fixture, using=using)

        try:
            with transaction.atomic(using):
                for obj in objects:
                    if (
                        hasattr(router, "allow_migrate") and
                        router.allow_migrate(using, obj.object.__class__)
                    ) or (
                        hasattr(router, "allow_syncdb") and
                        router.allow_syncdb(using, obj.object.__class__)
                    ):
                        obj.save(using=using)
        except (DatabaseError, IntegrityError) as e:
            msg = 'Could not load {0}.{1}(pk={2}): {3}'.format(
                obj.object._meta.app_label,
                obj.object._meta.object_name, obj.object.pk, e)
            raise e.__class__(e.__class__(msg)).with_traceback(sys.exc_info()[2])
    log.info('Loaded data from fixture {0}'.format(name))


def delete_metadata(using=DEFAULT_DB_ALIAS):
    "Deletes all metadata in the target database."
    DataConceptField.objects.using(using).delete()
    DataConcept.objects.using(using).delete()
    DataField.objects.using(using).delete()
    DataCategory.objects.using(using).delete()
    log.debug('Metadata deleted from database "{0}"'.format(using))


def safe_load(name, backup_path=None, using=DEFAULT_DB_ALIAS):
    """Creates a backup of the current state of the metadata, attempts to load
    the new fixture and falls back to the backup fixture if the load fails for
    any reason.
    """
    _check_app()

    try:
        with transaction.atomic(using):
            # Create the backup fixture
            if backup_path:
                create_fixture(os.path.abspath(backup_path), using=using,
                               silent=True)
            else:
                backup_path = create_temp_fixture(using=using, silent=True)
            log.info('Backup fixture written to {0}'.format(os.path.abspath(
                backup_path)))
            delete_metadata(using=using)
            load_fixture(name, using=using)
    except (DatabaseError, IntegrityError):
        log.error('Fixture load failed, reverting from backup: {0}'
                  .format(backup_path))
        load_fixture(os.path.abspath(backup_path), using=using)
        raise
    return backup_path
