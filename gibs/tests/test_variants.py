"""Experimental variants (OUR adaptations): symmetric truncation (C1) and multi-component MCS (C2)."""
import pytest

from gibs.graph.event_projection import project
from gibs.graph.step_graph import build_step_graph
from gibs.mcs.consensus import consensus_masks
from gibs.mcs.mcs import MCSConfig, find_mcs
from gibs.mcs.multi_component import find_mcs_multi
from gibs.mcs.nli import Similarity, StubEntailment, symmetric_input_ids
from gibs.mcs.structured_fields import StructuredFieldValidator
from gibs.tests.helpers import make_sim


# ------------------------------------------------------------------ symmetric truncation (tokenizer only, no model)
@pytest.fixture(scope="module")
def tok():
    transformers = pytest.importorskip("transformers")
    try:
        return transformers.AutoTokenizer.from_pretrained("microsoft/deberta-large-mnli", local_files_only=True)
    except OSError:
        pytest.skip("tokenizer not cached locally")


LONG = "Tool result: " + "; ".join(f"field_{i}: value_{i}" for i in range(220)) + "."


@pytest.mark.parametrize("encoding", ["code_sep_string", "pair"])
def test_identical_long_texts_both_represented_within_limit(tok, encoding):
    ids, info = symmetric_input_ids(tok, LONG, LONG, 512, encoding)
    # the second text is tokenized with a leading space, so its length can differ by one token
    assert min(info["len_a"], info["len_b"]) > 509 and abs(info["len_a"] - info["len_b"]) <= 1
    assert len(ids) == info["total"] <= 512
    assert info["kept_a"] + info["kept_b"] == 512 - info["n_special"] and abs(info["kept_a"] - info["kept_b"]) <= 1
    sep = tok.sep_token_id
    mid = ids.index(sep, 1)
    a_text = tok.decode(ids[1:mid]).strip()
    b_text = tok.decode(ids[mid + info["n_special"] - 2:-1]).strip()
    assert len(a_text) > 500 and len(b_text) > 500
    assert LONG.startswith(a_text) and LONG.startswith(b_text)         # both are prefixes of the same record


def test_author_truncation_drops_the_second_text_but_symmetric_keeps_it(tok):
    author = tok(f"{LONG} [SEP] {LONG}", truncation=True, max_length=512)["input_ids"]
    assert tok.sep_token_id not in author[1:-1]                        # no separator left: hypothesis lost
    ids, info = symmetric_input_ids(tok, LONG, LONG, 512)
    assert ids.count(tok.sep_token_id) == 2 and info["kept_b"] > 250


def test_short_text_is_kept_whole_when_paired_with_a_long_one(tok):
    short = "Tool result: status: cancelled."
    ids, info = symmetric_input_ids(tok, short, LONG, 512)
    assert info["kept_a"] == info["len_a"] and info["kept_b"] == 512 - info["n_special"] - info["len_a"]


def test_short_pairs_are_unchanged(tok):
    a, b = "Call get_reservation_details with reservation_id = 3RK2T9.", "Hi! How can I help you today?"
    ids, info = symmetric_input_ids(tok, a, b, 512)
    assert ids == tok(f"{a} [SEP] {b}")["input_ids"]                   # identical to the author-code encoding
    assert (info["kept_a"], info["kept_b"]) == (info["len_a"], info["len_b"])


def test_conflicting_field_at_the_head_survives_truncation(tok):
    a = "Tool result: status: cancelled; " + LONG
    b = "Tool result: status: null; " + LONG
    ids, _ = symmetric_input_ids(tok, a, b, 512)
    text = tok.decode(ids)
    assert "cancelled" in text and "null" in text


# ------------------------------------------------------------------ multi-component MCS (stub NLI)
def graph(events, sim_id):
    s = build_step_graph(make_sim(events, sim_id=sim_id))
    return s, project(s)


TWO_PIECES_Q = [("agent", "Hi"), ("user", "Go ahead."), ("agent", "Okay."), ("user", "Thanks"), ("agent", "Bye")]
TWO_PIECES_R = [("agent", "Hi"), ("user", "Do not."), ("agent", "Okay."), ("user", "Thanks"), ("agent", "Bye")]


def test_multi_component_recovers_a_disconnected_identical_step():
    (_, q), (_, r) = graph(TWO_PIECES_Q, "q"), graph(TWO_PIECES_R, "r")
    base = find_mcs(q, r, Similarity(StubEntailment()))
    multi = find_mcs_multi(q, r, Similarity(StubEntailment()))
    assert "N:s0" not in base.node_map and "N:s0" in multi.node_map
    assert multi.components[0]["edges"] == sorted(base.edge_map)      # component 0 is exactly the baseline
    assert len(multi.components) == 2 and multi.components[1]["edges"] == ["ROOT->N:s0"]


def test_multi_component_keeps_contradicting_user_turns_unmatched():
    (_, q), (_, r) = graph(TWO_PIECES_Q, "q"), graph(TWO_PIECES_R, "r")
    multi = find_mcs_multi(q, r, Similarity(StubEntailment()))
    assert "N:u1" not in multi.node_map and "N:u1->N:s2" not in multi.edge_map


LOOKUP = ("call", "get_reservation_details", {"reservation_id": "ABC123"}, {"reservation_id": "ABC123"})


def test_multi_component_mappings_stay_one_to_one():
    (_, q), (_, r) = graph([("agent", "Hi"), ("user", "id ABC123"), LOOKUP, ("user", "x"), LOOKUP], "q"), \
                     graph([("agent", "Hi"), ("user", "id ABC123"), LOOKUP, ("user", "y")], "r")
    multi = find_mcs_multi(q, r, Similarity(StubEntailment()))
    assert len(set(multi.node_map.values())) == len(multi.node_map)
    assert len(set(multi.edge_map.values())) == len(multi.edge_map)
    assert sum(n in multi.node_map for n in ("N:s2", "N:s4")) == 1      # one reference lookup -> one match


def test_multi_component_preserves_contradictory_instruction_target():
    cancel = ("call", "cancel_reservation", {"reservation_id": "ABC123"}, {"reservation_id": "ABC123", "status": "cancelled"})
    yes, no = "Yes, please cancel it.", "No, do not cancel it."
    ev = lambda conf: [("agent", "Hi"), ("user", "Please look at reservation ABC123."),
                       ("agent", "Shall I cancel reservation ABC123?"), ("user", conf), cancel, ("agent", "Done.")]
    (qs, q), (rs, r) = graph(ev(no), "q"), graph(ev(yes), "r")
    sim = Similarity(StubEntailment({(yes, no): 0.02, (no, yes): 0.02}))
    m = consensus_masks(q, [find_mcs_multi(q, r, sim, MCSConfig(), field_check=StructuredFieldValidator(qs, rs))])
    assert m["s4"]["m_ctx"] == 0.0


def test_multi_component_never_adds_a_field_rejected_pair():
    res = lambda st: {"reservation_id": "ABC123", "flights": [], "status": st}
    q_ev = [("agent", "Hi"), ("user", "Check ABC123."), ("call", "get_reservation_details", {"reservation_id": "ABC123"}, res("cancelled"))]
    r_ev = [("agent", "Hi"), ("user", "Check ABC123."), ("call", "get_reservation_details", {"reservation_id": "ABC123"}, res(None))]
    (qs, q), (rs, r) = graph(q_ev, "q"), graph(r_ev, "r")
    multi = find_mcs_multi(q, r, Similarity(StubEntailment(default=0.95)), field_check=StructuredFieldValidator(qs, rs))
    rejected = {(x["e1"], x["e2"]) for x in multi.rejected}
    assert rejected and not any(multi.edge_map.get(e1) == e2 for e1, e2 in rejected)
    assert "N:s2" not in multi.node_map
