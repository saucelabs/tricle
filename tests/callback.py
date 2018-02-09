import pytest
from monocle import _o
from monocle.callback import Callback, defer
from monocle.util import sleep
from o_test import test


@test
@_o
def test_result():
    cb = Callback()
    assert not hasattr(cb, 'result')
    cb('ok')
    assert cb.result == 'ok'


@test
@_o
def test_add():
    cb = Callback()
    calls = []
    assert cb.future._callbacks == []
    cb.add(calls.append)
    assert len(cb.future._callbacks) == 1
    pytest.raises(TypeError, cb.add, False)
    assert len(cb.future._callbacks) == 1
    assert calls == []
    cb('ok')
    yield sleep(0)
    assert calls == ['ok']
    cb.add(calls.append)
    yield sleep(0)
    assert calls == ['ok', 'ok']
    pytest.raises(TypeError, cb.add, False)


@test
@_o
def test_defer():
    cb = defer('ok')
    assert isinstance(cb, Callback)
    assert cb.result == 'ok'
    calls = []
    cb.add(calls.append)
    yield sleep(0)
    assert calls == ['ok']
