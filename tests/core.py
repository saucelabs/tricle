from monocle import _o
from monocle import core

from o_test import test


@test
@_o
def test_none():
    r = core.Return()
    assert r.value is None


@test
@_o
def test_single():
    r = core.Return('ok')
    assert r.value == 'ok'


@test
@_o
def test_multi():
    r = core.Return('one', 'two')
    r.value == ('one', 'two')
