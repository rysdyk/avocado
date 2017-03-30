from copy import deepcopy
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core import management
from avocado.query import oldparsers as parsers
from avocado.models import DataConcept, DataField, DataConceptField
from ....models import Employee


class DataContextParserTestCase(TestCase):
    fixtures = ['employee_data.json']

    def setUp(self):
        management.call_command('avocado', 'init', 'tests', quiet=True)

    def test_valid(self):
        title = DataField.objects.get_by_natural_key('tests.title.name')

        # Single by id (deprecated)
        attrs = {
            'id': title.pk,
            'operator': 'exact',
            'value': 'CEO',
            'cleaned_value': {'value': 'CEO', 'label': 'CEO'},
            'language': 'Name is CEO'
        }
        self.assertEqual(
            parsers.datacontext.validate(deepcopy(attrs), tree=Employee),
            attrs)

        # Single by dotted label
        attrs = {
            'field': 'tests.title.name',
            'operator': 'exact',
            'value': 'CEO',
            'cleaned_value': {'value': 'CEO', 'label': 'CEO'},
            'language': 'Name is CEO'
        }
        self.assertEqual(
            parsers.datacontext.validate(deepcopy(attrs), tree=Employee),
            attrs)

        # Single by label list
        attrs = {
            'field': ['tests', 'title', 'name'],
            'operator': 'exact',
            'value': 'CEO',
            'cleaned_value': {'value': 'CEO', 'label': 'CEO'},
            'language': 'Name is CEO'
        }
        self.assertEqual(
            parsers.datacontext.validate(deepcopy(attrs), tree=Employee),
            attrs)

        # Single by field
        attrs = {
            'field': title.pk,
            'operator': 'exact',
            'value': 'CEO',
            'cleaned_value': {'value': 'CEO', 'label': 'CEO'},
            'language': 'Name is CEO'
        }
        self.assertEqual(
            parsers.datacontext.validate(deepcopy(attrs), tree=Employee),
            attrs)

        # Branch node
        attrs = {
            'type': 'and',
            'children': [{
                'field': 'tests.title.name',
                'operator': 'exact',
                'value': 'CEO',
                'cleaned_value': {'value': 'CEO', 'label': 'CEO'},
                'language': 'Name is CEO'
            }, {
                'field': 'tests.employee.first_name',
                'operator': 'exact',
                'value': 'John',
                'cleaned_value': {'value': 'John', 'label': 'John'},
                'language': 'First Name is John'
            }],
        }

        self.assertEqual(
            parsers.datacontext.validate(deepcopy(attrs), tree=Employee),
            attrs)

        # No children
        attrs = {
            'type': 'and',
            'children': [],
        }
        self.assertEqual(
            parsers.datacontext.validate(deepcopy(attrs), tree=Employee),
            attrs)

        # 1 child
        attrs = {
            'type': 'and',
            'children': [{
                'field': 'tests.title.name',
                'operator': 'exact',
                'value': 'CEO',
                'cleaned_value': {'value': 'CEO', 'label': 'CEO'},
                'language': 'Name is CEO'
            }]
        }
        self.assertEqual(
            parsers.datacontext.validate(deepcopy(attrs), tree=Employee),
            attrs)

    def test_invalid(self):
        # Non-existent data field
        attrs = parsers.datacontext.validate({
            'field': 999,
            'operator': 'exact',
            'value': 'CEO'
        })
        self.assertFalse(attrs['enabled'])

        # Object must be a dict
        self.assertRaises(ValidationError, parsers.datacontext.validate, 1)

        # Invalid logical operator
        attrs = parsers.datacontext.validate({'type': 'foo', 'children': []})
        self.assertFalse(attrs['enabled'])

        # Missing 'value' key in first condition
        attrs = parsers.datacontext.validate({
            'type': 'and',
            'children': [{
                'field': 'tests.title.name',
                'operator': 'exact'
            }, {
                'field': 'tests.title.name',
                'operator': 'exact',
                'value': 'CEO'
            }]
        }, tree=Employee)

        self.assertTrue(attrs.get('enabled', True))
        self.assertFalse(attrs['children'][0]['enabled'])
        self.assertTrue(attrs['children'][1].get('enabled', True))

    def test_field_for_concept(self):
        f = DataField.objects.get(model_name='title', field_name='name')
        c1 = DataConcept()
        c2 = DataConcept()
        c1.save()
        c2.save()
        cf = DataConceptField(concept=c1, field=f)
        cf.save()

        attrs = {
            'concept': c1.pk,
            'field': f.pk,
            'operator': 'exact',
            'value': 'CEO',
            'cleaned_value': {'value': 'CEO', 'label': 'CEO'},
            'language': 'Name is CEO'
        }

        self.assertEqual(
            parsers.datacontext.validate(deepcopy(attrs), tree=Employee),
            attrs)

        # Invalid concept
        attrs = parsers.datacontext.validate({
            'concept': c2.pk,
            'field': f.pk,
            'operator': 'exact',
            'value': 'CEO',
        }, tree=Employee)

        self.assertFalse(attrs['enabled'])

    def test_parsed_node(self):
        node = parsers.datacontext.parse({
            'type': 'and',
            'children': [],
        }, tree=Employee)

        # No condition has been defined..
        self.assertEqual(node.condition, None)

        node = parsers.datacontext.parse({
            'type': 'and',
            'children': [{
                'field': 'tests.title.name',
                'operator': 'exact',
                'value': 'CEO',
            }]
        }, tree=Employee)

        # Only the one condition is represented
        self.assertEqual(str(node.condition),
                         "(AND: ('title__name__exact', u'CEO'))")

    def test_apply(self):
        f = DataField.objects.get_by_natural_key('tests',
                                                 'title',
                                                 'boss')
        f1 = DataField.objects.get_by_natural_key('tests',
                                                  'employee',
                                                  'first_name')
        node = parsers.datacontext.parse({
            'field': 'tests.title.boss',
            'operator': 'exact',
            'value': True
        }, tree=Employee)

        self.assertEqual(
            unicode(node.apply().values('id').query)
            .replace(' ', '').replace('`','"'),
            'SELECT DISTINCT "tests_employee"."id" FROM "tests_employee" '
            'INNER JOIN "tests_title" ON ("tests_employee"."title_id" = '
            '"tests_title"."id") WHERE "tests_title"."boss" = True '
            .replace(' ', ''))

        self.assertEqual(node.language, {
            'operator': 'exact',
            'language': u'Boss is True',
            'field': f.pk,
            'value': True
        })

        # Branch node
        node = parsers.datacontext.parse({
            'type': 'and',
            'children': [{
                'field': 'tests.title.boss',
                'operator': 'exact',
                'value': True,
            }, {
                'field': 'tests.employee.first_name',
                'operator': 'exact',
                'value': 'John',
            }]
        }, tree=Employee)

        self.assertEqual(
            unicode(node.apply().values('id').query)
            .replace(' ', '').replace('`','"'),
            'SELECT DISTINCT "tests_employee"."id" FROM "tests_employee" '
            'INNER JOIN "tests_title" ON ("tests_employee"."title_id" = '
            '"tests_title"."id") WHERE ("tests_employee"."first_name" = John '
            'AND "tests_title"."boss" = True )'.replace(' ', ''))

        self.assertEqual(node.language, {
            'type': 'and',
            'children': [{
                'field': f.pk,
                'operator': 'exact',
                'value': True,
                'language': 'Boss is True',
            }, {
                'field': f1.pk,
                'operator': 'exact',
                'value': 'John',
                'language': 'First Name is John',
            }]
        })


class DataViewParserTestCase(TestCase):
    fixtures = ['tests/fixtures/employee_data.json']

    def setUp(self):
        management.call_command('avocado', 'init', 'tests', publish=False,
                                concepts=False, quiet=True)
        f1 = DataField.objects.get_by_natural_key('tests',
                                                  'employee',
                                                  'first_name')
        f2 = DataField.objects.get_by_natural_key('tests',
                                                  'employee',
                                                  'last_name')

        self.c = DataConcept()
        self.c.save()

        DataConceptField(concept=self.c, field=f1).save()
        DataConceptField(concept=self.c, field=f2).save()

    def test_valid(self):
        # Single by id
        self.assertEqual(parsers.dataview.validate([{
            'concept': self.c.pk
        }], tree=Employee), [{
            'concept': self.c.pk,
        }])

        self.assertEqual(parsers.dataview.validate([{
            'concept': self.c.pk,
            'sort': 'desc',
        }], tree=Employee), [{
            'concept': self.c.pk,
            'sort': 'desc',
        }])

    def test_valid_legacy(self):
        # Single by id
        self.assertEqual(parsers.dataview.validate({
            'columns': [self.c.pk],
        }, tree=Employee), [{
            'concept': self.c.pk,
            'visible': True,
            'sort': None,
            'sort_index': None,
        }])

        self.assertEqual(parsers.dataview.validate({
            'ordering': [(self.c.pk, 'desc')],
        }, tree=Employee), [{
            'concept': self.c.pk,
            'visible': False,
            'sort': 'desc',
            'sort_index': 0,
        }])

    def test_invalid(self):
        # Non-existent data field
        facets = parsers.dataview.validate({'columns': [999]})
        self.assertFalse(facets[0]['enabled'])
        self.assertTrue(facets[0]['errors'])

        # Invalid ordering
        facets = parsers.dataview.validate([{
            'concept': self.c.pk,
            'sort': 'foo',
        }])
        self.assertTrue(facets[0]['warnings'])

    def test_apply(self):
        node = parsers.dataview.parse([{
            'concept': self.c.pk,
        }], tree=Employee)

        self.assertEqual(
            unicode(node.apply().query)
            .replace(' ', '').replace('`','"'),
            'SELECT "tests_employee"."id", "tests_employee"."first_name", '
            '"tests_employee"."last_name" FROM "tests_employee"'
            .replace(' ', ''))

        node = parsers.dataview.parse([{
            'concept': self.c.pk,
            'sort': 'desc',
            'visible': False,
        }], tree=Employee)

        self.assertEqual(
            unicode(node.apply().query)
            .replace(' ', '').replace('`','"'),
            'SELECT "tests_employee"."id" FROM "tests_employee" '
            'ORDER BY "tests_employee"."first_name" DESC, '
            '"tests_employee"."last_name" DESC'
            .replace(' ', ''))

    def test_apply_distinct(self):
        node = parsers.dataview.parse([{
            'concept': self.c.pk,
        }], tree=Employee)

        self.assertEqual(
            unicode(node.apply(Employee.objects.distinct()).query)
            .replace(' ', '').replace('`','"'),
            'SELECT DISTINCT "tests_employee"."id", '
            '"tests_employee"."first_name", '
            '"tests_employee"."last_name" FROM "tests_employee"'
            .replace(' ', ''))

    def test_implicit_apply_distinct(self):
        f1 = DataField.objects.get_by_natural_key('tests',
                                                  'office',
                                                  'location')
        f2 = DataField.objects.get_by_natural_key('tests',
                                                  'title',
                                                  'name')
        c = DataConcept()
        c.save()

        DataConceptField(concept=c, field=f1).save()
        DataConceptField(concept=c, field=f2).save()

        # Due to the use of distinct, the concept fields appear in the SELECT
        # statement at this point. This is not a bug, but a requirement of SQL.
        # These columns are stripped downstream by the exporter.
        node = parsers.dataview.parse([{
            'concept': c.pk,
            'sort': 'desc',
            'visible': False,
        }], tree=Employee)

        self.assertEqual(
            unicode(node.apply(Employee.objects.distinct()).query)
            .replace(' ', '').replace('`','"'),
            'SELECT DISTINCT "tests_employee"."id", '
            '"tests_office"."location", "tests_title"."name" FROM '
            '"tests_employee" INNER JOIN "tests_office" ON '
            '("tests_employee"."office_id" = "tests_office"."id") LEFT OUTER '
            'JOIN "tests_title" ON ("tests_employee"."title_id" = '
            '"tests_title"."id") ORDER BY "tests_office"."location" DESC, '
            '"tests_title"."name" DESC'
            .replace(' ', ''))


class DataQueryParserTestCase(TestCase):
    fixtures = ['employee_data.json']

    def setUp(self):
        management.call_command('avocado', 'init', 'tests', publish=False,
                                concepts=False, quiet=True)
        f1 = DataField.objects.get_by_natural_key('tests',
                                                  'employee',
                                                  'first_name')
        f2 = DataField.objects.get_by_natural_key('tests',
                                                  'employee',
                                                  'last_name')

        self.c = DataConcept()
        self.c.save()

        DataConceptField(concept=self.c, field=f1).save()
        DataConceptField(concept=self.c, field=f2).save()

    def test_valid(self):
        self.assertEqual(parsers.dataquery.validate({}, tree=Employee), None)

        attrs = {
            'context': {
                'field': 'tests.title.name',
                'operator': 'exact',
                'value': 'CEO',
                'cleaned_value': {'value': 'CEO', 'label': 'CEO'},
                'language': 'Name is CEO'
            },
            'view': [{
                'concept': self.c.pk,
            }],
        }

        exp_attrs = deepcopy(attrs)

        self.assertEqual(parsers.dataquery.validate(attrs, tree=Employee),
                         exp_attrs)

        # Only the context
        attrs = {
            'context': {
                'field': 'tests.title.name',
                'operator': 'exact',
                'value': 'CEO',
                'cleaned_value': {
                    'value': 'CEO',
                    'label': 'CEO',
                },
                'language': 'Name is CEO'
            }
        }

        exp_attrs = deepcopy(attrs)
        exp_attrs['view'] = None

        self.assertEqual(parsers.dataquery.validate(attrs, tree=Employee),
                         exp_attrs)

        # Only the view
        attrs = {
            'view': [{
                'concept': self.c.pk,
                'visible': False,
                'sort': 'desc',
            }]
        }

        exp_attrs = {
            'context': None,
            'view': [{
                'visible': False,
                'concept': self.c.pk,
                'sort': 'desc',
            }],
        }
        self.assertEqual(parsers.dataquery.validate(attrs, tree=Employee),
                         exp_attrs)

    def test_parsed_node(self):
        # Make sure no context or view subnodes are created
        node = parsers.dataquery.parse({}, tree=Employee)
        self.assertEqual(node.datacontext_node, None)
        self.assertEqual(node.dataview_node, None)

        node = parsers.dataquery.parse({
            'context': {
                'type': 'and',
                'children': [],
            }
        }, tree=Employee)

        # No condition has been defined..
        self.assertEqual(node.datacontext_node.condition, None)

        node = parsers.dataquery.parse({
            'context': {
                'type': 'and',
                'children': [{
                    'field': 'tests.title.name',
                    'operator': 'exact',
                    'value': 'CEO',
                }]
            }
        }, tree=Employee)

        # Only the one condition is represented
        self.assertEqual(str(node.datacontext_node.condition),
                         "(AND: ('title__name__exact', u'CEO'))")

    def test_apply(self):
        node = parsers.dataquery.parse({
            'context': {
                'field': 'tests.title.boss',
                'operator': 'exact',
                'value': True
            },
            'view': [{
                'concept': self.c.pk,
            }],
        }, tree=Employee)

        self.assertEqual(
            unicode(node.apply().query)
            .replace(' ', '').replace('`','"'),
            'SELECT DISTINCT "tests_employee"."id", '
            '"tests_employee"."first_name", "tests_employee"."last_name" FROM '
            '"tests_employee" INNER JOIN "tests_title" ON '
            '("tests_employee"."title_id" = "tests_title"."id") '
            'WHERE "tests_title"."boss" = True '
            .replace(' ', ''))

        # Just the view
        node = parsers.dataquery.parse({
            'view': [{
                'concept': self.c.pk,
                'sort': 'desc',
            }]
        }, tree=Employee)

        self.assertEqual(
            unicode(node.apply().query)
            .replace(' ', '').replace('`','"'),
            'SELECT DISTINCT "tests_employee"."id", '
            '"tests_employee"."first_name", '
            '"tests_employee"."last_name" FROM "tests_employee" '
            'ORDER BY "tests_employee"."first_name" DESC, '
            '"tests_employee"."last_name" DESC'.replace(' ', ''))

        # Just the context
        node = parsers.dataquery.parse({
            'context': {
                'field': 'tests.title.boss',
                'operator': 'exact',
                'value': True
            }
        }, tree=Employee)

        self.assertEqual(
            unicode(node.apply().values('id').query)
            .replace(' ', '').replace('`','"'),
            'SELECT DISTINCT "tests_employee"."id" FROM "tests_employee" '
            'INNER JOIN "tests_title" ON ("tests_employee"."title_id" = '
            '"tests_title"."id") WHERE "tests_title"."boss" = True '
            .replace(' ', ''))

        f = DataField.objects.get_by_natural_key('tests', 'title', 'boss')
        self.assertEqual(node.datacontext_node.language, {
            'operator': 'exact',
            'language': u'Boss is True',
            'field': f.pk,
            'value': True
        })
