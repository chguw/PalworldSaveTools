from __future__ import annotations
import pytest
from tests.dynamic_importer import import_from

_utils = import_from('palworld_aio.utils')
safe_str = _utils.safe_str
sanitize_filename = _utils.sanitize_filename
as_uuid = _utils.as_uuid
format_duration = _utils.format_duration
format_duration_short = _utils.format_duration_short
is_valid_level = _utils.is_valid_level
normalize_uid = _utils.normalize_uid
safe_dict_get = _utils.safe_dict_get
safe_nested_get = _utils.safe_nested_get
resolve_name = _utils.resolve_name
extract_value = _utils.extract_value


def test_safe_str():
    assert safe_str('hello') == 'hello'
    assert safe_str('123') == '123'
    assert safe_str('None') == 'None'


def test_sanitize_filename():
    assert sanitize_filename('hello.txt') == 'hello.txt'
    result = sanitize_filename('a/b:c*d?e')
    assert '/' not in result


def test_as_uuid():
    u = as_uuid('00112233-4455-6677-8899-aabbccddeeff')
    assert u is not None
    assert str(u) == '00112233-4455-6677-8899-aabbccddeeff'


def test_as_uuid_invalid():
    u = as_uuid('not-a-uuid')
    assert u == 'not-a-uuid'


def test_format_duration():
    assert format_duration(0) == '0d:0h:0m'
    assert format_duration(60) == '0d:0h:1m'
    result = format_duration(3661)
    assert 'h' in result or 'm' in result


def test_format_duration_short():
    assert isinstance(format_duration_short(0), str)
    assert isinstance(format_duration_short(3600), str)


def test_is_valid_level():
    assert is_valid_level(1) is True
    assert is_valid_level(0) is False
    assert is_valid_level(-1) is False


def test_normalize_uid():
    assert normalize_uid('test') is not None


def test_safe_dict_get():
    data = {'a': {'b': 42}}
    assert safe_dict_get(data, 'a', 'b') == 42
    assert safe_dict_get(data, 'x', default=0) == 0


def test_safe_nested_get():
    data = {'a': {'b': {'c': 99}}}
    assert safe_nested_get(data, ['a', 'b', 'c']) == 99
    assert safe_nested_get(data, ['a', 'x']) is None


def test_resolve_name():
    name_map = {'char_001': 'Human'}
    assert resolve_name('char_001', name_map) == 'Human'
    assert resolve_name('unknown', name_map) is None


def test_extract_value():
    data = {'nested': {'key': 'value'}}
    assert extract_value(data, 'key', 'default') == 'default'
