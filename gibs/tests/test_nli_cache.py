import json
import pytest
from gibs.mcs.nli import read_cache


def test_interrupted_tail_is_archived_and_removed_for_safe_resume(tmp_path):
    p=tmp_path/'scores.jsonl';valid=json.dumps({'k':'a','p':.75})+'\n'
    p.write_text(valid+'{"k":')
    assert read_cache(p)=={'a':.75}
    assert p.read_text()==valid
    assert len(list(tmp_path.glob('scores.jsonl.interrupted-*')))==1


def test_complete_corruption_is_not_silently_dropped(tmp_path):
    p=tmp_path/'scores.jsonl';p.write_text('not json\n')
    with pytest.raises(json.JSONDecodeError):read_cache(p)
    assert p.read_text()=='not json\n'


def test_complete_final_record_without_newline_remains_appendable(tmp_path):
    p=tmp_path/'scores.jsonl';p.write_text(json.dumps({'k':'a','p':.5}))
    assert read_cache(p)=={'a':.5}
    with p.open('a') as f:f.write(json.dumps({'k':'b','p':.9})+'\n')
    assert read_cache(p)=={'a':.5,'b':.9}
