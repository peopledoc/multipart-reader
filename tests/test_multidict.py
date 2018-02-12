import sys
import unittest

from multipart_reader.multidict import (MultiDictProxy,
                                        MultiDict,
                                        CIMultiDictProxy,
                                        CIMultiDict)


from multipart_reader import multidict


class _Root:

    cls = None

    proxy_cls = None

    def test_exposed_names(self):
        name = self.cls.__name__
        while name.startswith('_'):
            name = name[1:]
        self.assertIn(name, multidict.__all__)


class _BaseTest(_Root):

    @property
    def isCIMultiDict(self):
        return self.cls == CIMultiDict

    def _dict(self, expected):
        if not self.isCIMultiDict:
            return expected
        return {k.upper(): v for k, v in expected.items()}

    def _items(self, expected):
        if not self.isCIMultiDict:
            return expected
        return [(k.upper(), v) for k, v in expected]

    def _key(self, expected):
        if not self.isCIMultiDict:
            return expected
        return expected.upper()

    def _list(self, expected):
        if not self.isCIMultiDict:
            return expected
        return [e.upper() for e in expected]

    def _set(self, expected):
        return set(self._list(expected))

    def _tuple(self, expected):
        if not self.isCIMultiDict:
            return expected
        return (expected[0].upper(), expected[1])

    def test_instantiate__empty(self):
        d = self.make_dict()
        self.assertEqual(d, {})
        self.assertEqual(len(d), 0)
        self.assertEqual(list(d.keys()), [])
        self.assertEqual(list(d.values()), [])
        self.assertEqual(list(d.values()), [])
        self.assertEqual(list(d.items()), [])
        self.assertEqual(list(d.items()), [])

        self.assertNotEqual(self.make_dict(), list())
        with self.assertRaisesRegexp(TypeError, "\(2 given\)"):
            self.make_dict(('key1', 'value1'), ('key2', 'value2'))

    def test_instantiate__from_arg0(self):
        d = self.make_dict([('key', 'value1')])

        self.assertEqual(d, self._dict({'key': 'value1'}))
        self.assertEqual(len(d), 1)
        self.assertEqual(list(d.keys()), self._list(['key']))
        self.assertEqual(list(d.values()), ['value1'])
        self.assertEqual(list(d.items()), self._items([('key', 'value1')]))

    def test_instantiate__from_arg0_dict(self):
        d = self.make_dict({'key': 'value1'})

        self.assertEqual(d, self._dict({'key': 'value1'}))
        self.assertEqual(len(d), 1)
        self.assertEqual(list(d.keys()), self._list(['key']))
        self.assertEqual(list(d.values()), ['value1'])
        self.assertEqual(list(d.items()), self._items([('key', 'value1')]))

    def test_instantiate__with_kwargs(self):
        d = self.make_dict([('key', 'value1')], key2='value2')

        self.assertEqual(d, self._dict({'key': 'value1', 'key2': 'value2'}))
        self.assertEqual(len(d), 2)
        self.assertEqual(sorted(d.keys()), self._list(['key', 'key2']))
        self.assertEqual(sorted(d.values()), ['value1', 'value2'])
        self.assertEqual(sorted(d.items()), self._items([('key', 'value1'),
                                                         ('key2', 'value2')]))

    def test_getone(self):
        d = self.make_dict([('key', 'value1')], key='value2')
        self.assertEqual(d.getone('key'), 'value1')
        self.assertEqual(d.get('key'), 'value1')
        self.assertEqual(d['key'], 'value1')

        with self.assertRaises(KeyError):
            d['key2']
        with self.assertRaises(KeyError):
            d.getone('key2')

        self.assertEqual('default', d.getone('key2', 'default'))

    def test__iter__(self):
        d = self.make_dict([('key', 'one'), ('key2', 'two'), ('key', 3)])
        self.assertEqual(self._list(['key', 'key2', 'key']), list(d))

    def test_keys__contains(self):
        d = self.make_dict([('key', 'one'), ('key2', 'two'), ('key', 3)])
        self.assertEqual(d.keys(), {'key', 'key2', 'key'})

        self.assertIn(self._key('key'), d.keys())
        self.assertIn(self._key('key2'), d.keys())

        self.assertNotIn(self._key('foo'), d.keys())

    def test_values__contains(self):
        d = self.make_dict([('key', 'one'), ('key', 'two'), ('key', 3)])
        self.assertEqual(d.values(), {'one', 'two', 3})

        self.assertIn('one', d.values())
        self.assertIn('two', d.values())
        self.assertIn(3, d.values())

        self.assertNotIn('foo', d.values())

    def test_items__contains(self):
        d = self.make_dict([('key', 'one'), ('key', 'two'), ('key', 3)])

        self.assertEqual(list(d.items()),
                         self._items([('key', 'one'), ('key', 'two'),
                                      ('key', 3)]))

        self.assertIn(self._tuple(('key', 'one')), d.items())
        self.assertIn(self._tuple(('key', 'two')), d.items())
        self.assertIn(self._tuple(('key', 3)), d.items())

        self.assertNotIn(('foo', 'bar'), d.items())

    def test_cannot_create_from_unaccepted(self):
        with self.assertRaises(TypeError):
            self.make_dict([(1, 2, 3)])

    def test_keys_is_set_less(self):
        d = self.make_dict([('key', 'value1')])

        self.assertLess(set(d.keys()), self._set({'key', 'key2'}))

    def test_keys_is_set_less_equal(self):
        d = self.make_dict([('key', 'value1')])

        self.assertLessEqual(set(d.keys()), self._set({'key'}))

    def test_keys_is_set_equal(self):
        d = self.make_dict([('key', 'value1')])

        self.assertEqual(set(d.keys()), self._set({'key'}))

    def test_keys_is_set_greater(self):
        d = self.make_dict([('key', 'value1')])

        self.assertGreater(self._set({'key', 'key2'}), set(d.keys()))

    def test_keys_is_set_greater_equal(self):
        d = self.make_dict([('key', 'value1')])

        self.assertGreaterEqual(self._set({'key'}), set(d.keys()))

    def test_keys_is_set_not_equal(self):
        d = self.make_dict([('key', 'value1')])

        self.assertNotEqual(set(d.keys()), self._set({'key2'}))

    def test_eq(self):
        d = self.make_dict([('key', 'value1')])
        self.assertEqual(self._dict({'key': 'value1'}), d)

    def test_ne(self):
        d = self.make_dict([('key', 'value1')])
        self.assertNotEqual(d, {'key': 'another_value'})

    def test_and(self):
        d = self.make_dict([('key', 'value1')])
        self.assertEqual(self._set({'key'}), d.keys() & {'key', 'key2'})

    def test_or(self):
        d = self.make_dict([('key', 'value1')])
        self.assertEqual(self._set({'key', 'key2'}), d.keys() | {'key2'})

    def test_sub(self):
        d = self.make_dict([('key', 'value1'), ('key2', 'value2')])
        self.assertEqual(self._set({'key'}), d.keys() - {'key2'})

    def test_xor(self):
        d = self.make_dict([('key', 'value1'), ('key2', 'value2')])
        self.assertEqual(self._set({'key', 'key3'}),
                         d.keys() ^ {'key2', 'key3'})

    def test_isdisjoint(self):
        d = self.make_dict([('key', 'value1')])
        self.assertTrue(d.keys().isdisjoint({'key2'}))

    def test_isdisjoint2(self):
        d = self.make_dict([('key', 'value1')])
        self.assertFalse(d.keys().isdisjoint({'key'}))

    def test_repr_issue_410(self):
        d = self.make_dict()
        try:
            raise Exception
            self.fail("Sould never happen")  # pragma: no cover
        except Exception as e:
            repr(d)
            self.assertIs(sys.exc_info()[1], e)

    def test_or_issue_410(self):
        d = self.make_dict([('key', 'value')])
        try:
            raise Exception
            self.fail("Sould never happen")  # pragma: no cover
        except Exception as e:
            set(d.keys()) | {'other'}
            self.assertIs(sys.exc_info()[1], e)

    def test_and_issue_410(self):
        d = self.make_dict([('key', 'value')])
        try:
            raise Exception
            self.fail("Sould never happen")  # pragma: no cover
        except Exception as e:
            set(d.keys()) & {'other'}
            self.assertIs(sys.exc_info()[1], e)

    def test_sub_issue_410(self):
        d = self.make_dict([('key', 'value')])
        try:
            raise Exception
            self.fail("Sould never happen")  # pragma: no cover
        except Exception as e:
            set(d.keys()) - {'other'}
            self.assertIs(sys.exc_info()[1], e)

    def test_xor_issue_410(self):
        d = self.make_dict([('key', 'value')])
        try:
            raise Exception
            self.fail("Sould never happen")  # pragma: no cover
        except Exception as e:
            set(d.keys()) ^ {'other'}
            self.assertIs(sys.exc_info()[1], e)


class _MultiDictTests(_BaseTest):

    def test__repr__(self):
        d = self.make_dict()
        cls = self.proxy_cls if self.proxy_cls is not None else self.cls

        self.assertEqual(str(d), "<%s()>" % cls.__name__)
        d = self.make_dict([('key', 'one'), ('key', 'two')])

        if self.isCIMultiDict:
            self.assertEqual(
                str(d),
                "<%s('KEY': 'one', 'KEY': 'two')>" % cls.__name__)
        else:
            self.assertEqual(
                str(d),
                "<%s('key': 'one', 'key': 'two')>" % cls.__name__)

    def test_getall(self):
        d = self.make_dict([('key', 'value1')], key='value2')

        self.assertNotEqual(d, {'key': 'value1'})
        self.assertEqual(len(d), 2)

        self.assertEqual(d.getall('key'), ['value1', 'value2'])

        with self.assertRaisesRegexp(KeyError, self._key("some_key")):
            d.getall('some_key')

        default = object()
        self.assertIs(d.getall('some_key', default), default)

    def test_preserve_stable_ordering(self):
        d = self.make_dict([('a', 1), ('b', '2'), ('a', 3)])
        s = '&'.join('{}={}'.format(k, v) for k, v in d.items())

        if self.isCIMultiDict:
            exp = 'A=1&B=2&A=3'
        else:
            exp = 'a=1&b=2&a=3'

        self.assertEqual(exp, s)

    def test_get(self):
        d = self.make_dict([('a', 1), ('a', 2)])
        self.assertEqual(1, d['a'])

    def test_items__repr__(self):
        d = self.make_dict([('key', 'value1')], key='value2')
        self.assertEqual(repr(d.items()),
                         "_ItemsView('key': 'value1', 'key': 'value2')")

    def test_keys__repr__(self):
        d = self.make_dict([('key', 'value1')], key='value2')
        self.assertEqual(repr(d.keys()),
                         "_KeysView('key', 'key')")

    def test_values__repr__(self):
        d = self.make_dict([('key', 'value1')], key='value2')
        self.assertEqual(repr(d.values()),
                         "_ValuesView('value1', 'value2')")


class _CIMultiDictTests(_Root):

    def test_basics(self):
        d = self.make_dict([('KEY', 'value1')], KEY='value2')
        self.assertEqual(d.getone('key'), 'value1')
        self.assertEqual(d.get('key'), 'value1')
        self.assertEqual(d.get('key2', 'val'), 'val')
        self.assertEqual(d['key'], 'value1')
        self.assertIn('key', d)

        with self.assertRaises(KeyError):
            d['key2']
        with self.assertRaises(KeyError):
            d.getone('key2')

    def test_getall(self):
        d = self.make_dict([('KEY', 'value1')], KEY='value2')

        self.assertNotEqual(d, {'KEY': 'value1'})
        self.assertEqual(len(d), 2)

        self.assertEqual(d.getall('key'), ['value1', 'value2'])

        with self.assertRaisesRegexp(KeyError, "SOME_KEY"):
            d.getall('some_key')

    def test_get(self):
        d = self.make_dict([('A', 1), ('a', 2)])
        self.assertEqual(1, d['a'])

    def test_items__repr__(self):
        d = self.make_dict([('KEY', 'value1')], key='value2')
        self.assertEqual(repr(d.items()),
                         "_ItemsView('KEY': 'value1', 'KEY': 'value2')")

    def test_keys__repr__(self):
        d = self.make_dict([('KEY', 'value1')], key='value2')
        self.assertEqual(repr(d.keys()),
                         "_KeysView('KEY', 'KEY')")

    def test_values__repr__(self):
        d = self.make_dict([('KEY', 'value1')], key='value2')
        self.assertEqual(repr(d.values()),
                         "_ValuesView('value1', 'value2')")


class _TestProxy(_MultiDictTests):

    def make_dict(self, *args, **kwargs):
        dct = self.cls(*args, **kwargs)
        return self.proxy_cls(dct)

    def test_copy(self):
        d1 = self.cls(key='value', a='b')
        p1 = self.proxy_cls(d1)

        d2 = p1.copy()
        self.assertEqual(d1, d2)
        self.assertIsNot(d1, d2)


class _TestCIProxy(_CIMultiDictTests):

    def make_dict(self, *args, **kwargs):
        dct = self.cls(*args, **kwargs)
        return self.proxy_cls(dct)

    def test_copy(self):
        d1 = self.cls(key='value', a='b')
        p1 = self.proxy_cls(d1)

        d2 = p1.copy()
        self.assertEqual(d1, d2)
        self.assertIsNot(d1, d2)


class _BaseMutableMultiDictTests(_BaseTest):

    def test_copy(self):
        d1 = self.make_dict(key='value', a='b')

        d2 = d1.copy()
        self.assertEqual(d1, d2)
        self.assertIsNot(d1, d2)

    def make_dict(self, *args, **kwargs):
        return self.cls(*args, **kwargs)

    def test__repr__(self):
        d = self.make_dict()
        self.assertEqual(str(d), "<%s()>" % self.cls.__name__)

        d = self.make_dict([('key', 'one'), ('key', 'two')])

        self.assertEqual(
            str(d),
            "<%s('key': 'one', 'key': 'two')>" % self.cls.__name__)

    def test_getall(self):
        d = self.make_dict([('key', 'value1')], key='value2')
        self.assertEqual(len(d), 2)

        self.assertEqual(d.getall('key'), ['value1', 'value2'])

        with self.assertRaisesRegexp(KeyError, "some_key"):
            d.getall('some_key')

        default = object()
        self.assertIs(d.getall('some_key', default), default)

    def test_add(self):
        d = self.make_dict()

        self.assertEqual(d, {})
        d['key'] = 'one'
        self.assertEqual(d, {'key': 'one'})
        self.assertEqual(d.getall('key'), ['one'])

        d['key'] = 'two'
        self.assertEqual(d, {'key': 'two'})
        self.assertEqual(d.getall('key'), ['two'])

        d.add('key', 'one')
        self.assertEqual(2, len(d))
        self.assertEqual(d.getall('key'), ['two', 'one'])

        d.add('foo', 'bar')
        self.assertEqual(3, len(d))
        self.assertEqual(d.getall('foo'), ['bar'])

    def test_extend(self):
        d = self.make_dict()
        self.assertEqual(d, {})

        d.extend([('key', 'one'), ('key', 'two')], key=3, foo='bar')
        self.assertNotEqual(d, {'key': 'one', 'foo': 'bar'})
        self.assertEqual(4, len(d))
        itms = d.items()
        # we can't guarantee order of kwargs
        self.assertTrue(('key', 'one') in itms)
        self.assertTrue(('key', 'two') in itms)
        self.assertTrue(('key', 3) in itms)
        self.assertTrue(('foo', 'bar') in itms)

        other = self.make_dict(bar='baz')
        self.assertEqual(other, {'bar': 'baz'})

        d.extend(other)
        self.assertIn(('bar', 'baz'), d.items())

        d.extend({'foo': 'moo'})
        self.assertIn(('foo', 'moo'), d.items())

        d.extend()
        self.assertEqual(6, len(d))

        with self.assertRaises(TypeError):
            d.extend('foo', 'bar')

    def test_extend_from_proxy(self):
        d = self.make_dict([('a', 'a'), ('b', 'b')])
        proxy = self.proxy_cls(d)

        d2 = self.make_dict()
        d2.extend(proxy)

        self.assertEqual([('a', 'a'), ('b', 'b')], list(d2.items()))

    def test_clear(self):
        d = self.make_dict([('key', 'one')], key='two', foo='bar')

        d.clear()
        self.assertEqual(d, {})
        self.assertEqual(list(d.items()), [])

    def test_del(self):
        d = self.make_dict([('key', 'one'), ('key', 'two')], foo='bar')

        del d['key']
        self.assertEqual(d, {'foo': 'bar'})
        self.assertEqual(list(d.items()), [('foo', 'bar')])

        with self.assertRaises(KeyError):
            del d['key']

    def test_set_default(self):
        d = self.make_dict([('key', 'one'), ('key', 'two')], foo='bar')
        self.assertEqual('one', d.setdefault('key', 'three'))
        self.assertEqual('three', d.setdefault('otherkey', 'three'))
        self.assertIn('otherkey', d)
        self.assertEqual('three', d['otherkey'])

    def test_popitem(self):
        d = self.make_dict()
        d.add('key', 'val1')
        d.add('key', 'val2')

        self.assertEqual(('key', 'val1'), d.popitem())
        self.assertEqual([('key', 'val2')], list(d.items()))

    def test_popitem_empty_multidict(self):
        d = self.make_dict()

        with self.assertRaises(KeyError):
            d.popitem()

    def test_pop(self):
        d = self.make_dict()
        d.add('key', 'val1')
        d.add('key', 'val2')

        self.assertEqual('val1', d.pop('key'))
        self.assertFalse(d)

    def test_pop_default(self):
        d = self.make_dict(other='val')

        self.assertEqual('default', d.pop('key', 'default'))
        self.assertIn('other', d)

    def test_pop_raises(self):
        d = self.make_dict(other='val')

        with self.assertRaises(KeyError):
            d.pop('key')

        self.assertIn('other', d)

    def test_update(self):
        d = self.make_dict()
        d.add('key', 'val1')
        d.add('key', 'val2')
        d.add('key2', 'val3')

        d.update(key='val')

        self.assertEqual([('key2', 'val3'), ('key', 'val')], list(d.items()))


class _CIMutableMultiDictTests(_Root):

    def make_dict(self, *args, **kwargs):
        return self.cls(*args, **kwargs)

    def test_getall(self):
        d = self.make_dict([('KEY', 'value1')], KEY='value2')

        self.assertNotEqual(d, {'KEY': 'value1'})
        self.assertEqual(len(d), 2)

        self.assertEqual(d.getall('key'), ['value1', 'value2'])

        with self.assertRaisesRegexp(KeyError, "SOME_KEY"):
            d.getall('some_key')

    def test_ctor(self):
        d = self.make_dict(k1='v1')
        self.assertEqual('v1', d['K1'])

    def test_setitem(self):
        d = self.make_dict()
        d['k1'] = 'v1'
        self.assertEqual('v1', d['K1'])

    def test_delitem(self):
        d = self.make_dict()
        d['k1'] = 'v1'
        self.assertIn('K1', d)
        del d['k1']
        self.assertNotIn('K1', d)

    def test_copy(self):
        d1 = self.make_dict(key='KEY', a='b')

        d2 = d1.copy()
        self.assertEqual(d1, d2)
        self.assertIsNot(d1, d2)

    def test__repr__(self):
        d = self.make_dict()
        self.assertEqual(str(d), "<%s()>" % self.cls.__name__)

        d = self.make_dict([('KEY', 'one'), ('KEY', 'two')])

        self.assertEqual(
            str(d),
            "<%s('KEY': 'one', 'KEY': 'two')>" % self.cls.__name__)

    def test_add(self):
        d = self.make_dict()

        self.assertEqual(d, {})
        d['KEY'] = 'one'
        self.assertEqual(d, {'KEY': 'one'})
        self.assertEqual(d.getall('key'), ['one'])

        d['KEY'] = 'two'
        self.assertEqual(d, {'KEY': 'two'})
        self.assertEqual(d.getall('key'), ['two'])

        d.add('KEY', 'one')
        self.assertEqual(2, len(d))
        self.assertEqual(d.getall('key'), ['two', 'one'])

        d.add('FOO', 'bar')
        self.assertEqual(3, len(d))
        self.assertEqual(d.getall('foo'), ['bar'])

    def test_extend(self):
        d = self.make_dict()
        self.assertEqual(d, {})

        d.extend([('KEY', 'one'), ('key', 'two')], key=3, foo='bar')
        self.assertNotEqual(d, {'KEY': 'one', 'FOO': 'bar'})
        self.assertEqual(4, len(d))
        itms = d.items()
        # we can't guarantee order of kwargs
        self.assertTrue(('KEY', 'one') in itms)
        self.assertTrue(('KEY', 'two') in itms)
        self.assertTrue(('KEY', 3) in itms)
        self.assertTrue(('FOO', 'bar') in itms)

        other = self.make_dict(bar='baz')
        self.assertEqual(other, {'BAR': 'baz'})

        d.extend(other)
        self.assertIn(('BAR', 'baz'), d.items())

        d.extend({'FOO': 'moo'})
        self.assertIn(('FOO', 'moo'), d.items())

        d.extend()
        self.assertEqual(6, len(d))

        with self.assertRaises(TypeError):
            d.extend('foo', 'bar')

    def test_extend_from_proxy(self):
        d = self.make_dict([('a', 'a'), ('b', 'b')])
        proxy = self.proxy_cls(d)

        d2 = self.make_dict()
        d2.extend(proxy)

        self.assertEqual([('A', 'a'), ('B', 'b')], list(d2.items()))

    def test_clear(self):
        d = self.make_dict([('KEY', 'one')], key='two', foo='bar')

        d.clear()
        self.assertEqual(d, {})
        self.assertEqual(list(d.items()), [])

    def test_del(self):
        d = self.make_dict([('KEY', 'one'), ('key', 'two')], foo='bar')

        del d['key']
        self.assertEqual(d, {'FOO': 'bar'})
        self.assertEqual(list(d.items()), [('FOO', 'bar')])

        with self.assertRaises(KeyError):
            del d['key']

    def test_set_default(self):
        d = self.make_dict([('KEY', 'one'), ('key', 'two')], foo='bar')
        self.assertEqual('one', d.setdefault('key', 'three'))
        self.assertEqual('three', d.setdefault('otherkey', 'three'))
        self.assertIn('otherkey', d)
        self.assertEqual('three', d['OTHERKEY'])

    def test_popitem(self):
        d = self.make_dict()
        d.add('KEY', 'val1')
        d.add('key', 'val2')

        self.assertEqual(('KEY', 'val1'), d.popitem())
        self.assertEqual([('KEY', 'val2')], list(d.items()))

    def test_popitem_empty_multidict(self):
        d = self.make_dict()

        with self.assertRaises(KeyError):
            d.popitem()

    def test_pop(self):
        d = self.make_dict()
        d.add('KEY', 'val1')
        d.add('key', 'val2')

        self.assertEqual('val1', d.pop('KEY'))
        self.assertFalse(d)

    def test_pop_default(self):
        d = self.make_dict(OTHER='val')

        self.assertEqual('default', d.pop('key', 'default'))
        self.assertIn('other', d)

    def test_pop_raises(self):
        d = self.make_dict(OTHER='val')

        with self.assertRaises(KeyError):
            d.pop('KEY')

        self.assertIn('other', d)

    def test_update(self):
        d = self.make_dict()
        d.add('KEY', 'val1')
        d.add('key', 'val2')
        d.add('key2', 'val3')

        d.update(key='val')

        self.assertEqual([('KEY2', 'val3'), ('KEY', 'val')], list(d.items()))


class TestMultiDictProxy(_TestProxy, unittest.TestCase):

    cls = MultiDict
    proxy_cls = MultiDictProxy


class TestCIMultiDictProxy(_TestCIProxy, unittest.TestCase):

    cls = CIMultiDict
    proxy_cls = CIMultiDictProxy


class MutableMultiDictTests(_BaseMutableMultiDictTests, unittest.TestCase):

    cls = MultiDict
    proxy_cls = MultiDictProxy


class CIMutableMultiDictTests(_CIMutableMultiDictTests, unittest.TestCase):

    cls = CIMultiDict
    proxy_cls = CIMultiDictProxy
