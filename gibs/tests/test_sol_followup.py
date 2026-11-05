"""Only checkpoint timeouts and preemption may trigger another GPU allocation."""
import pytest
import gibs.fresh.sol_followup as monitor


@pytest.mark.parametrize('status,code,elapsed,expected',[
    ('TIMEOUT','0:15',14400,True),('PREEMPTED','0:15',100,True),
    ('FAILED','143:0',14280,True),('FAILED','143:0',100,False),
    ('FAILED','1:0',14280,False),('CANCELLED','0:15',14280,False),
    ('COMPLETED','0:0',14280,False)])
def test_allocation_retry_does_not_restart_failures_or_user_cancellations(monkeypatch,status,code,elapsed,expected):
    monkeypatch.setattr(monitor,'ssh',lambda _:f'123|{elapsed}|240|')
    assert monitor.resumable_timeout(123,status,code)==expected


def test_unknown_deadline_does_not_authorize_retry(monkeypatch):
    monkeypatch.setattr(monitor,'ssh',lambda _:'123|14280|UNLIMITED|')
    assert not monitor.resumable_timeout(123,'FAILED','143:0')
