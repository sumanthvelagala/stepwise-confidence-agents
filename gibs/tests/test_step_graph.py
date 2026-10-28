import hashlib
import json

import pytest

from gibs.graph.step_graph import (build_step_graph, dependency_values, load_simulation, normalize_text,
                                   value_occurs, verbalize_observation, verbalize_tool_call, verbalize_utterance)
from gibs.tests.helpers import REPO, TASK48_FAILURE, TASK48_FILE, TASK48_SUCCESS, make_sim

V01 = REPO / "gibs/examples/task48_success/trajectory_graph.json"


@pytest.fixture(scope="module")
def success():
    return build_step_graph(*load_simulation(str(TASK48_FILE), TASK48_SUCCESS))


@pytest.fixture(scope="module")
def failure():
    return build_step_graph(*load_simulation(str(TASK48_FILE), TASK48_FAILURE))


def deps(g):
    return {(e["source"], e["target"], v) for e in g["edges"] if e["type"] == "data_dependency" for v in e["values"]}


# ---------------------------------------------------------------- real Task 48 trajectories
def test_every_raw_message_maps_to_one_node(success, failure):
    for g, sim_prefix in ((success, TASK48_SUCCESS), (failure, TASK48_FAILURE)):
        sim, _, _ = load_simulation(str(TASK48_FILE), sim_prefix)
        covered = sorted(i for n in g["nodes"] for i in n["raw_message_indices"])
        assert covered == list(range(len(sim["messages"])))
        assert sum(n["type"] == "AgentStep" for n in g["nodes"]) == sum(m["role"] == "assistant" for m in sim["messages"])
        assert sum(n["type"] == "UserTurn" for n in g["nodes"]) == sum(m["role"] == "user" for m in sim["messages"])


def test_automatic_rule_reproduces_hand_verified_v01_dependencies(success):
    v01 = json.load(open(V01))
    hand = {(e["source"], e["target"], e["value"]) for e in v01["edges"] if e["type"] == "data_dependency"}
    assert deps(success) == hand == {("u3", "s4", "3RK2T9"), ("s4", "s8", "2024-05-02")}


def test_failure_dependencies_and_alternative_sources(failure):
    assert deps(failure) == {("u3", "s4", "3RK2T9"), ("u3", "s6", "3RK2T9")}
    cancel = next(e for e in failure["edges"] if e["type"] == "data_dependency" and e["target"] == "s6")
    assert cancel["alternative_sources"] == {"3RK2T9": ["s4"]}   # also in the lookup observation


def test_response_links(failure):
    resp = {n["id"]: n["response_node"] for n in failure["nodes"] if n["type"] == "AgentStep"}
    assert resp == {"s0": "u1", "s2": "u3", "s4": "s4", "s6": "s6", "s8": "u9", "s10": "u11", "s12": "u13"}


V01_HASHES = {
    "trajectory_graph.json": "49ac93e1e94e8ffe3fc8d6c7e494d0930df624379bd9a1e4272c2c425a33e2b5",
    "trajectory_graph.mmd": "5449156a416f9787ebba90b901916299bb5b89719dc11a99aac6413239101a08",
    "README.md": "ab4b64772724d05cc565d1db1820a10fba626bf33ca0c7d2335aacc3d5aa6c90",
}


def test_existing_v01_example_files_are_unchanged():
    for name, digest in V01_HASHES.items():
        assert hashlib.sha256((V01.parent / name).read_bytes()).hexdigest() == digest, name


def test_metadata_is_separate_from_matching_fields(success):
    for n in success["nodes"]:
        assert "task_gold_actions" not in n and "op_text" in n and "result_text" in n


# ---------------------------------------------------------------- text rendering
def test_normalize_text_handles_markdown_and_unicode():
    assert normalize_text("created on **2024‑05‑02**, ok") == "created on 2024-05-02, ok"


def test_control_tokens_are_verbalized():
    assert verbalize_utterance("###STOP###") == "The user ended the conversation."
    assert verbalize_utterance("###TRANSFER###") == "The user was transferred to a human agent."


def test_tool_call_and_observation_flattening():
    assert verbalize_tool_call("update", {"passengers": [{"dob": "1989-12-13"}], "id": "X"}) == \
        "Call update with passengers[0].dob = 1989-12-13; id = X."
    assert verbalize_tool_call("list_all_airports", {}) == "Call list_all_airports with no arguments."
    assert verbalize_observation('{"status": null, "n": 2}', False) == "Tool result: status: null; n: 2."
    assert verbalize_observation("Error: not found", True) == "Tool error: Error: not found"


# ---------------------------------------------------------------- dependency rule
def test_dependency_values_rules():
    args = {"reservation_id": "3RK2T9", "cabin": "economy", "insurance": "no", "amount": 128,
            "summary": "User claims booking was made 10 hours ago but system shows created_at 2024-05-02."}
    assert dependency_values(args) == ["3RK2T9", "2024-05-02"]


def test_value_occurs_boundaries():
    assert value_occurs("2024-05-02", '"created_at": "2024-05-02T06:02:56"')
    assert not value_occurs("2024-05-0", "2024-05-02")
    assert not value_occurs("SEA", "SEARCH")
    assert value_occurs("SEA", "to SEA.")


def test_earliest_source_wins_and_later_sources_are_alternatives():
    sim = make_sim([("agent", "Hi"), ("user", "my id is ABC123"),
                    ("call", "get_reservation_details", {"reservation_id": "ABC123"}, {"reservation_id": "ABC123"}),
                    ("call", "cancel_reservation", {"reservation_id": "ABC123"}, {"status": "cancelled"})])
    g = build_step_graph(sim)
    assert deps(g) == {("u1", "s2", "ABC123"), ("u1", "s4", "ABC123")}
    assert next(e for e in g["edges"] if e["type"] == "data_dependency" and e["target"] == "s4")["alternative_sources"] == {"ABC123": ["s2"]}


def test_parallel_tool_calls_are_rejected():
    sim = make_sim([("agent", "Hi")])
    sim["messages"].append({"role": "assistant", "content": None,
                            "tool_calls": [{"id": "a", "name": "x", "arguments": {}},
                                           {"id": "b", "name": "y", "arguments": {}}]})
    with pytest.raises(ValueError):
        build_step_graph(sim)
