import pytest

from diskbench.core import retry_logic


def test_exponential_backoff_eventual_success(monkeypatch):
    calls = {'count': 0}
    sleep_calls = []

    monkeypatch.setattr(retry_logic.time, 'sleep', sleep_calls.append)

    @retry_logic.exponential_backoff(max_retries=2, initial_delay=0.5, backoff_multiplier=2.0, jitter=False)
    def flaky():
        calls['count'] += 1
        if calls['count'] < 3:
            raise ValueError('temporary')
        return 'ok'

    assert flaky() == 'ok'
    assert sleep_calls == [0.5, 1.0]


def test_exponential_backoff_raises_after_retries(monkeypatch):
    sleep_calls = []
    monkeypatch.setattr(retry_logic.time, 'sleep', lambda delay: sleep_calls.append(delay))

    @retry_logic.exponential_backoff(max_retries=1, initial_delay=0.25, jitter=False)
    def always_fail():
        raise RuntimeError('boom')

    with pytest.raises(RuntimeError):
        always_fail()

    assert sleep_calls == [0.25]


def test_retryable_operation_retries_then_succeeds(monkeypatch):
    sleep_calls = []
    monkeypatch.setattr(retry_logic.time, 'sleep', lambda delay: sleep_calls.append(delay))

    op = retry_logic.RetryableOperation('write', max_retries=2, initial_delay=0.1, retriable_exceptions=(ValueError,))

    with op:
        raise ValueError('timeout while writing')

    assert sleep_calls == [0.1]

    with op:
        pass


def test_retryable_operation_non_retriable_propagates(monkeypatch):
    monkeypatch.setattr(retry_logic.time, 'sleep', lambda delay: None)
    op = retry_logic.RetryableOperation('read', max_retries=1, initial_delay=0.1, retriable_exceptions=(ValueError,))

    with pytest.raises(KeyError):
        with op:
            raise KeyError('permanent')


def test_retryable_operation_should_retry_logic():
    op = retry_logic.RetryableOperation('check', max_retries=3, retriable_exceptions=(RuntimeError,))
    op.attempt = 1
    assert op.should_retry(RuntimeError('Connection timeout')) is True

    op.attempt = 4
    assert op.should_retry(RuntimeError('Connection timeout')) is False

    op.attempt = 1
    assert op.should_retry(RuntimeError('Permission denied')) is False


def test_with_retry_decorator(monkeypatch):
    sleep_calls = []
    monkeypatch.setattr(retry_logic.time, 'sleep', lambda delay: sleep_calls.append(delay))

    calls = {'count': 0}

    @retry_logic.with_retry(max_retries=2, delay=0.05, retriable_exceptions=(ValueError,))
    def flaky():
        calls['count'] += 1
        if calls['count'] < 3:
            raise ValueError('transient issue')
        return 'done'

    assert flaky() == 'done'
    assert sleep_calls == [0.05, 0.05]


def test_with_retry_non_retriable_exception(monkeypatch):
    monkeypatch.setattr(retry_logic.time, 'sleep', lambda delay: None)

    @retry_logic.with_retry(max_retries=1, delay=0.1, retriable_exceptions=(ValueError,))
    def fail():
        raise RuntimeError('fatal')

    with pytest.raises(RuntimeError):
        fail()
