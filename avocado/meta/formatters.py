try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from django.utils.encoding import force_unicode
from avocado.utils import loader
from avocado.conf import settings

DATA_CHOICES_MAP = settings.DATA_CHOICES_MAP

class Formatter(object):
    """Provides support for the core data formats with sensible defaults
    for handling converting Python datatypes to their formatted equivalent.

    Each core format method must return one of the following:
        Single formatted Value
        OrderedDict/sequence of key-value pairs

        If ta format method is unable to do either of these for the given
        value a FormatException must be raised.

        ``values`` - an OrderedDict containing each value along with the field
        instance it represents.

        ::

            values = OrderedDict({
                'first_name': 'Bob',
                'last_name': 'Smith',
            })

    """
    name = ''

    def __init__(self, cfields, **context):
        self.cfields = OrderedDict((x.field.field_name, x) \
            for x in cfields)
        self.context = context

    def __call__(self, values, preferred_formats=None):
        # Create a copy of the preferred formats since each set values may
        # be processed slightly differently (e.g. mixed data type in column)
        # which could cause exceptions that would not be present during
        # processing of other values
        if not preferred_formats:
            preferred_formats = []
        preferred_formats = list(preferred_formats) + ['raw']

        # Iterate over all preferred formats and attempt to process the values.
        # For formatter methods that process all values must be tracked and
        # attempted only once. They are removed from the list once attempted.
        # If no preferred multi-value methods succeed, each value is processed
        # independently with the remaining formats
        for f in iter(preferred_formats):
            method = getattr(self, 'to_{0}'.format(f), None)
            # This formatter does not support this format, remove it
            # from the available list
            if not method:
                preferred_formats.pop(0)
                continue

            # The implicit behavior when handling multiple values is to process
            # them independently since, in most cases, they are not dependent on
            # on one another, but rather should be represented together since the
            # data is related. A formatter method can be flagged to process all values
            # together by setting the attribute ``process_multiple=True``. we must
            # check to if that flag has been set and simply pass through the values
            # and context to the method as is. if ``process_multiple`` is not set,
            # each value is handled independently
            if getattr(method, 'process_multiple', False):
                try:
                    return method(values, cfields=self.cfields, **self.context)
                # Remove from the preferred formats list since it failed
                except:
                    preferred_formats.pop(0)

        # The output is independent of the input. Formatters may output more
        # or less values than what was entered.
        output = OrderedDict()

        # Attempt to process each
        for i, (key, value) in enumerate(values.iteritems()):
            for f in preferred_formats:
                method = getattr(self, 'to_{0}'.format(f))
                try:
                    fvalue = method(value, cfield=self.cfields[key], **self.context)
                    if type(fvalue) is dict:
                        output.update(fvalue)
                    else:
                        output[key] = fvalue
                    break
                except:
                    pass
        return output

    def __contains__(self, choice):
        return hasattr(self, 'to_%s' % choice)

    def __unicode__(self):
        return u'%s' % self.name

    def to_string(self, value, cfield, **context):
        # attempt to coerce non-strings to strings. depending on the data
        # types that are being passed into this, this may not be good
        # enough for certain datatypes or complext data structures
        if value is None:
            return u''
        return force_unicode(value, strings_only=False)

    def to_boolean(self, value, cfield, **context):
        # if value is native True or False value, return it
        # Change value to bool if value is a string of false or true
        if type(value) is bool:
            return value
        if value in ('true', 'True', '1', 1):
            return True
        if value in ('false', 'False', '0', 0):
            return False
        raise Exception('Cannot convert {0} to boolean'.format(value))

    def to_number(self, value, cfield, **context):
        # attempts to convert a number. Starting with ints and floats
        # Eventually create to_decimal using the decimal library.
        if type(value) is int or type(value) is float:
            return value
        try:
            value = int(value)
        except (ValueError, TypeError):
            value = float(value)
        return value

    def to_coded(self, value, cfield, **context):
        # attempts to convert value to its coded representation
        for key, cvalue in cfield.field.coded_values:
            if key == value:
                return cvalue
        raise ValueError('No coded value for {}'.format(value))

    def to_raw(self, value, cfield, **context):
        return value


# initialize the registry that will contain all classes for this type of
# registry
registry = loader.Registry(default=Formatter)

# this will be invoked when it is imported by models.py to use the
# registry choices
loader.autodiscover('formatters')