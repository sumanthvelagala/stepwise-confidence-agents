# C5 vs A / C0 / C3 / C4: generated tables (run_c5.py analyze)

C5 = two-stage constrained matching (OUR adaptation). Values are consensus fractions, not correctness.

Checks: {"F1_tool_steps_checked": 315, "pairs": 959, "F3_ctx_messages_after_tool": 661, "F4_6f12b024_s32_ctx_refs": 0, "F4_6f12b024_s32_node_refs": 0}

## Task 48

C5 cost: {'seconds': 0.7, 'nli_forward_passes_uncached': 0, 'nli_directional_pairs_requested': 5096, 'n_mcs_runs': 220}; stage-2 counters: {'candidates_message_edges': 419, 'dropped_tool_unmatched': 82, 'dropped_tool_conflict': 0}

Message coverage (indicator counts): {"C3": {"node": 419, "ctx": 419, "node_only": 0, "indicators": 867}, "C4": {"node": 423, "ctx": 423, "node_only": 0, "indicators": 867}, "C5": {"node": 337, "ctx": 337, "node_only": 0, "indicators": 867}}

C5 − C4 on message steps: {"node|same|unverified": 76, "ctx|same|unverified": 76, "node|down|valid": 10, "ctx|down|valid": 10, "node|down|unverified": 4, "ctx|down|unverified": 4}

| Variant | Target | Group | Runs | n | mean | median | bins 0 / (0,.25) / [.25,.5) / [.5,.75) / [.75,1) / 1 |
|---|---|---|---|---|---|---|---|
| A | ctx | incorrect:cancel_reservation | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| A | node | incorrect:cancel_reservation | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C0 | ctx | incorrect:cancel_reservation | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C0 | node | incorrect:cancel_reservation | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C3 | ctx | incorrect:cancel_reservation | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C3 | node | incorrect:cancel_reservation | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C4 | ctx | incorrect:cancel_reservation | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C4 | node | incorrect:cancel_reservation | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C5 | ctx | incorrect:cancel_reservation | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C5 | node | incorrect:cancel_reservation | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| A | ctx | incorrect | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| A | node | incorrect | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C0 | ctx | incorrect | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C0 | node | incorrect | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C3 | ctx | incorrect | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C3 | node | incorrect | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C4 | ctx | incorrect | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C4 | node | incorrect | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C5 | ctx | incorrect | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| C5 | node | incorrect | failed | 13 | 0.0 | 0.0 | 13 0 0 0 0 0 |
| A | ctx | message|pred=none | failed | 13 | 1.0 | 1.0 | 0 0 0 0 0 13 |
| A | node | message|pred=none | failed | 13 | 1.0 | 1.0 | 0 0 0 0 0 13 |
| C0 | ctx | message|pred=none | failed | 13 | 1.0 | 1.0 | 0 0 0 0 0 13 |
| C0 | node | message|pred=none | failed | 13 | 1.0 | 1.0 | 0 0 0 0 0 13 |
| C3 | ctx | message|pred=none | failed | 13 | 1.0 | 1.0 | 0 0 0 0 0 13 |
| C3 | node | message|pred=none | failed | 13 | 1.0 | 1.0 | 0 0 0 0 0 13 |
| C4 | ctx | message|pred=none | failed | 13 | 1.0 | 1.0 | 0 0 0 0 0 13 |
| C4 | node | message|pred=none | failed | 13 | 1.0 | 1.0 | 0 0 0 0 0 13 |
| C5 | ctx | message|pred=none | failed | 13 | 1.0 | 1.0 | 0 0 0 0 0 13 |
| C5 | node | message|pred=none | failed | 13 | 1.0 | 1.0 | 0 0 0 0 0 13 |
| A | ctx | message|pred=none | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| A | node | message|pred=none | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| C0 | ctx | message|pred=none | success | 10 | 0.4 | 0.556 | 1 3 0 6 0 0 |
| C0 | node | message|pred=none | success | 10 | 0.4 | 0.556 | 1 3 0 6 0 0 |
| C3 | ctx | message|pred=none | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| C3 | node | message|pred=none | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| C4 | ctx | message|pred=none | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| C4 | node | message|pred=none | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| C5 | ctx | message|pred=none | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| C5 | node | message|pred=none | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| A | ctx | message|pred=tool_call | failed | 25 | 0.108 | 0.0 | 20 2 0 1 0 2 |
| A | node | message|pred=tool_call | failed | 25 | 0.108 | 0.0 | 20 2 0 1 0 2 |
| C0 | ctx | message|pred=tool_call | failed | 25 | 0.02 | 0.0 | 24 0 0 1 0 0 |
| C0 | node | message|pred=tool_call | failed | 25 | 0.02 | 0.0 | 24 0 0 1 0 0 |
| C3 | ctx | message|pred=tool_call | failed | 25 | 0.02 | 0.0 | 24 0 0 1 0 0 |
| C3 | node | message|pred=tool_call | failed | 25 | 0.02 | 0.0 | 24 0 0 1 0 0 |
| C4 | ctx | message|pred=tool_call | failed | 25 | 0.028 | 0.0 | 22 2 0 1 0 0 |
| C4 | node | message|pred=tool_call | failed | 25 | 0.028 | 0.0 | 22 2 0 1 0 0 |
| C5 | ctx | message|pred=tool_call | failed | 25 | 0.02 | 0.0 | 24 0 0 1 0 0 |
| C5 | node | message|pred=tool_call | failed | 25 | 0.02 | 0.0 | 24 0 0 1 0 0 |
| A | ctx | message|pred=tool_call | success | 15 | 0.815 | 1.0 | 0 0 5 0 0 10 |
| A | node | message|pred=tool_call | success | 15 | 0.815 | 1.0 | 0 0 5 0 0 10 |
| C0 | ctx | message|pred=tool_call | success | 15 | 0.593 | 0.556 | 0 0 7 4 3 1 |
| C0 | node | message|pred=tool_call | success | 15 | 0.593 | 0.556 | 0 0 7 4 3 1 |
| C3 | ctx | message|pred=tool_call | success | 15 | 0.815 | 1.0 | 0 0 5 0 0 10 |
| C3 | node | message|pred=tool_call | success | 15 | 0.815 | 1.0 | 0 0 5 0 0 10 |
| C4 | ctx | message|pred=tool_call | success | 15 | 0.815 | 1.0 | 0 0 5 0 0 10 |
| C4 | node | message|pred=tool_call | success | 15 | 0.815 | 1.0 | 0 0 5 0 0 10 |
| C5 | ctx | message|pred=tool_call | success | 15 | 0.207 | 0.111 | 2 8 5 0 0 0 |
| C5 | node | message|pred=tool_call | success | 15 | 0.207 | 0.111 | 2 8 5 0 0 0 |
| A | ctx | message|pred=user_turn | failed | 19 | 0.284 | 0.0 | 10 0 0 9 0 0 |
| A | node | message|pred=user_turn | failed | 19 | 0.284 | 0.0 | 10 0 0 9 0 0 |
| C0 | ctx | message|pred=user_turn | failed | 19 | 0.284 | 0.0 | 10 0 0 9 0 0 |
| C0 | node | message|pred=user_turn | failed | 19 | 0.284 | 0.0 | 10 0 0 9 0 0 |
| C3 | ctx | message|pred=user_turn | failed | 19 | 0.284 | 0.0 | 10 0 0 9 0 0 |
| C3 | node | message|pred=user_turn | failed | 19 | 0.284 | 0.0 | 10 0 0 9 0 0 |
| C4 | ctx | message|pred=user_turn | failed | 19 | 0.284 | 0.0 | 10 0 0 9 0 0 |
| C4 | node | message|pred=user_turn | failed | 19 | 0.284 | 0.0 | 10 0 0 9 0 0 |
| C5 | ctx | message|pred=user_turn | failed | 19 | 0.284 | 0.0 | 10 0 0 9 0 0 |
| C5 | node | message|pred=user_turn | failed | 19 | 0.284 | 0.0 | 10 0 0 9 0 0 |
| A | ctx | message|pred=user_turn | success | 8 | 0.445 | 0.556 | 0 2 0 6 0 0 |
| A | node | message|pred=user_turn | success | 8 | 0.445 | 0.556 | 0 2 0 6 0 0 |
| C0 | ctx | message|pred=user_turn | success | 8 | 0.417 | 0.556 | 2 0 0 6 0 0 |
| C0 | node | message|pred=user_turn | success | 8 | 0.417 | 0.556 | 2 0 0 6 0 0 |
| C3 | ctx | message|pred=user_turn | success | 8 | 0.417 | 0.556 | 2 0 0 6 0 0 |
| C3 | node | message|pred=user_turn | success | 8 | 0.417 | 0.556 | 2 0 0 6 0 0 |
| C4 | ctx | message|pred=user_turn | success | 8 | 0.445 | 0.556 | 0 2 0 6 0 0 |
| C4 | node | message|pred=user_turn | success | 8 | 0.445 | 0.556 | 0 2 0 6 0 0 |
| C5 | ctx | message|pred=user_turn | success | 8 | 0.417 | 0.556 | 2 0 0 6 0 0 |
| C5 | node | message|pred=user_turn | success | 8 | 0.417 | 0.556 | 2 0 0 6 0 0 |
| A | ctx | unverified:get_flight_status | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | node | unverified:get_flight_status | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | ctx | unverified:get_flight_status | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | node | unverified:get_flight_status | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | ctx | unverified:get_flight_status | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | node | unverified:get_flight_status | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | ctx | unverified:get_flight_status | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | node | unverified:get_flight_status | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | ctx | unverified:get_flight_status | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | node | unverified:get_flight_status | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | ctx | unverified:get_user_details | failed | 1 | 0.1 | 0.1 | 0 1 0 0 0 0 |
| A | node | unverified:get_user_details | failed | 1 | 0.1 | 0.1 | 0 1 0 0 0 0 |
| C0 | ctx | unverified:get_user_details | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | node | unverified:get_user_details | failed | 1 | 0.1 | 0.1 | 0 1 0 0 0 0 |
| C3 | ctx | unverified:get_user_details | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | node | unverified:get_user_details | failed | 1 | 0.1 | 0.1 | 0 1 0 0 0 0 |
| C4 | ctx | unverified:get_user_details | failed | 1 | 0.1 | 0.1 | 0 1 0 0 0 0 |
| C4 | node | unverified:get_user_details | failed | 1 | 0.1 | 0.1 | 0 1 0 0 0 0 |
| C5 | ctx | unverified:get_user_details | failed | 1 | 0.1 | 0.1 | 0 1 0 0 0 0 |
| C5 | node | unverified:get_user_details | failed | 1 | 0.1 | 0.1 | 0 1 0 0 0 0 |
| A | ctx | unverified:get_user_details | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | node | unverified:get_user_details | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | ctx | unverified:get_user_details | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | node | unverified:get_user_details | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | ctx | unverified:get_user_details | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | node | unverified:get_user_details | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | ctx | unverified:get_user_details | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | node | unverified:get_user_details | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | ctx | unverified:get_user_details | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | node | unverified:get_user_details | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | ctx | unverified:message | failed | 57 | 0.37 | 0.0 | 30 2 0 10 0 15 |
| A | node | unverified:message | failed | 57 | 0.37 | 0.0 | 30 2 0 10 0 15 |
| C0 | ctx | unverified:message | failed | 57 | 0.332 | 0.0 | 34 0 0 10 0 13 |
| C0 | node | unverified:message | failed | 57 | 0.332 | 0.0 | 34 0 0 10 0 13 |
| C3 | ctx | unverified:message | failed | 57 | 0.332 | 0.0 | 34 0 0 10 0 13 |
| C3 | node | unverified:message | failed | 57 | 0.332 | 0.0 | 34 0 0 10 0 13 |
| C4 | ctx | unverified:message | failed | 57 | 0.335 | 0.0 | 32 2 0 10 0 13 |
| C4 | node | unverified:message | failed | 57 | 0.335 | 0.0 | 32 2 0 10 0 13 |
| C5 | ctx | unverified:message | failed | 57 | 0.332 | 0.0 | 34 0 0 10 0 13 |
| C5 | node | unverified:message | failed | 57 | 0.332 | 0.0 | 34 0 0 10 0 13 |
| A | ctx | unverified:message | success | 23 | 0.686 | 0.556 | 0 2 5 6 0 10 |
| A | node | unverified:message | success | 23 | 0.686 | 0.556 | 0 2 5 6 0 10 |
| C0 | ctx | unverified:message | success | 23 | 0.416 | 0.556 | 3 3 5 12 0 0 |
| C0 | node | unverified:message | success | 23 | 0.416 | 0.556 | 3 3 5 12 0 0 |
| C3 | ctx | unverified:message | success | 23 | 0.676 | 0.556 | 2 0 5 6 0 10 |
| C3 | node | unverified:message | success | 23 | 0.676 | 0.556 | 2 0 5 6 0 10 |
| C4 | ctx | unverified:message | success | 23 | 0.686 | 0.556 | 0 2 5 6 0 10 |
| C4 | node | unverified:message | success | 23 | 0.686 | 0.556 | 0 2 5 6 0 10 |
| C5 | ctx | unverified:message | success | 23 | 0.676 | 0.556 | 2 0 5 6 0 10 |
| C5 | node | unverified:message | success | 23 | 0.676 | 0.556 | 2 0 5 6 0 10 |
| A | ctx | unverified:transfer_to_human_agents | success | 10 | 0.078 | 0.111 | 3 7 0 0 0 0 |
| A | node | unverified:transfer_to_human_agents | success | 10 | 0.089 | 0.111 | 2 8 0 0 0 0 |
| C0 | ctx | unverified:transfer_to_human_agents | success | 10 | 0.044 | 0.0 | 6 4 0 0 0 0 |
| C0 | node | unverified:transfer_to_human_agents | success | 10 | 0.667 | 0.556 | 0 0 2 4 3 1 |
| C3 | ctx | unverified:transfer_to_human_agents | success | 10 | 0.044 | 0.0 | 6 4 0 0 0 0 |
| C3 | node | unverified:transfer_to_human_agents | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| C4 | ctx | unverified:transfer_to_human_agents | success | 10 | 0.078 | 0.111 | 3 7 0 0 0 0 |
| C4 | node | unverified:transfer_to_human_agents | success | 10 | 0.089 | 0.111 | 2 8 0 0 0 0 |
| C5 | ctx | unverified:transfer_to_human_agents | success | 10 | 0.078 | 0.111 | 3 7 0 0 0 0 |
| C5 | node | unverified:transfer_to_human_agents | success | 10 | 0.089 | 0.111 | 2 8 0 0 0 0 |
| A | ctx | unverified | failed | 59 | 0.359 | 0.0 | 31 3 0 10 0 15 |
| A | node | unverified | failed | 59 | 0.359 | 0.0 | 31 3 0 10 0 15 |
| C0 | ctx | unverified | failed | 59 | 0.32 | 0.0 | 36 0 0 10 0 13 |
| C0 | node | unverified | failed | 59 | 0.322 | 0.0 | 35 1 0 10 0 13 |
| C3 | ctx | unverified | failed | 59 | 0.32 | 0.0 | 36 0 0 10 0 13 |
| C3 | node | unverified | failed | 59 | 0.322 | 0.0 | 35 1 0 10 0 13 |
| C4 | ctx | unverified | failed | 59 | 0.325 | 0.0 | 33 3 0 10 0 13 |
| C4 | node | unverified | failed | 59 | 0.325 | 0.0 | 33 3 0 10 0 13 |
| C5 | ctx | unverified | failed | 59 | 0.322 | 0.0 | 35 1 0 10 0 13 |
| C5 | node | unverified | failed | 59 | 0.322 | 0.0 | 35 1 0 10 0 13 |
| A | ctx | unverified | success | 34 | 0.487 | 0.444 | 4 9 5 6 0 10 |
| A | node | unverified | success | 34 | 0.49 | 0.444 | 3 10 5 6 0 10 |
| C0 | ctx | unverified | success | 34 | 0.294 | 0.333 | 10 7 5 12 0 0 |
| C0 | node | unverified | success | 34 | 0.477 | 0.556 | 4 3 7 16 3 1 |
| C3 | ctx | unverified | success | 34 | 0.471 | 0.444 | 9 4 5 6 0 10 |
| C3 | node | unverified | success | 34 | 0.752 | 1.0 | 3 0 5 6 0 20 |
| C4 | ctx | unverified | success | 34 | 0.487 | 0.444 | 4 9 5 6 0 10 |
| C4 | node | unverified | success | 34 | 0.49 | 0.444 | 3 10 5 6 0 10 |
| C5 | ctx | unverified | success | 34 | 0.48 | 0.444 | 6 7 5 6 0 10 |
| C5 | node | unverified | success | 34 | 0.484 | 0.444 | 5 8 5 6 0 10 |
| A | ctx | valid:get_reservation_details | failed | 13 | 0.969 | 1.0 | 0 0 0 0 4 9 |
| A | node | valid:get_reservation_details | failed | 13 | 0.969 | 1.0 | 0 0 0 0 4 9 |
| C0 | ctx | valid:get_reservation_details | failed | 13 | 0.508 | 0.6 | 0 0 4 9 0 0 |
| C0 | node | valid:get_reservation_details | failed | 13 | 0.508 | 0.6 | 0 0 4 9 0 0 |
| C3 | ctx | valid:get_reservation_details | failed | 13 | 0.577 | 0.7 | 0 0 4 9 0 0 |
| C3 | node | valid:get_reservation_details | failed | 13 | 0.577 | 0.7 | 0 0 4 9 0 0 |
| C4 | ctx | valid:get_reservation_details | failed | 13 | 0.969 | 1.0 | 0 0 0 0 4 9 |
| C4 | node | valid:get_reservation_details | failed | 13 | 0.969 | 1.0 | 0 0 0 0 4 9 |
| C5 | ctx | valid:get_reservation_details | failed | 13 | 0.969 | 1.0 | 0 0 0 0 4 9 |
| C5 | node | valid:get_reservation_details | failed | 13 | 0.969 | 1.0 | 0 0 0 0 4 9 |
| A | ctx | valid:get_reservation_details | success | 10 | 0.933 | 1.0 | 0 0 0 1 3 6 |
| A | node | valid:get_reservation_details | success | 10 | 0.933 | 1.0 | 0 0 0 1 3 6 |
| C0 | ctx | valid:get_reservation_details | success | 10 | 0.422 | 0.556 | 1 2 1 6 0 0 |
| C0 | node | valid:get_reservation_details | success | 10 | 0.422 | 0.556 | 1 2 1 6 0 0 |
| C3 | ctx | valid:get_reservation_details | success | 10 | 0.556 | 0.667 | 0 2 1 6 1 0 |
| C3 | node | valid:get_reservation_details | success | 10 | 0.556 | 0.667 | 0 2 1 6 1 0 |
| C4 | ctx | valid:get_reservation_details | success | 10 | 0.933 | 1.0 | 0 0 0 1 3 6 |
| C4 | node | valid:get_reservation_details | success | 10 | 0.933 | 1.0 | 0 0 0 1 3 6 |
| C5 | ctx | valid:get_reservation_details | success | 10 | 0.933 | 1.0 | 0 0 0 1 3 6 |
| C5 | node | valid:get_reservation_details | success | 10 | 0.933 | 1.0 | 0 0 0 1 3 6 |
| A | ctx | valid:message | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| A | node | valid:message | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| C0 | ctx | valid:message | success | 10 | 0.667 | 0.556 | 0 0 2 4 3 1 |
| C0 | node | valid:message | success | 10 | 0.667 | 0.556 | 0 0 2 4 3 1 |
| C3 | ctx | valid:message | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| C3 | node | valid:message | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| C4 | ctx | valid:message | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| C4 | node | valid:message | success | 10 | 1.0 | 1.0 | 0 0 0 0 0 10 |
| C5 | ctx | valid:message | success | 10 | 0.089 | 0.111 | 2 8 0 0 0 0 |
| C5 | node | valid:message | success | 10 | 0.089 | 0.111 | 2 8 0 0 0 0 |
| A | ctx | valid | failed | 13 | 0.969 | 1.0 | 0 0 0 0 4 9 |
| A | node | valid | failed | 13 | 0.969 | 1.0 | 0 0 0 0 4 9 |
| C0 | ctx | valid | failed | 13 | 0.508 | 0.6 | 0 0 4 9 0 0 |
| C0 | node | valid | failed | 13 | 0.508 | 0.6 | 0 0 4 9 0 0 |
| C3 | ctx | valid | failed | 13 | 0.577 | 0.7 | 0 0 4 9 0 0 |
| C3 | node | valid | failed | 13 | 0.577 | 0.7 | 0 0 4 9 0 0 |
| C4 | ctx | valid | failed | 13 | 0.969 | 1.0 | 0 0 0 0 4 9 |
| C4 | node | valid | failed | 13 | 0.969 | 1.0 | 0 0 0 0 4 9 |
| C5 | ctx | valid | failed | 13 | 0.969 | 1.0 | 0 0 0 0 4 9 |
| C5 | node | valid | failed | 13 | 0.969 | 1.0 | 0 0 0 0 4 9 |
| A | ctx | valid | success | 20 | 0.967 | 1.0 | 0 0 0 1 3 16 |
| A | node | valid | success | 20 | 0.967 | 1.0 | 0 0 0 1 3 16 |
| C0 | ctx | valid | success | 20 | 0.545 | 0.556 | 1 2 3 10 3 1 |
| C0 | node | valid | success | 20 | 0.545 | 0.556 | 1 2 3 10 3 1 |
| C3 | ctx | valid | success | 20 | 0.778 | 0.889 | 0 2 1 6 1 10 |
| C3 | node | valid | success | 20 | 0.778 | 0.889 | 0 2 1 6 1 10 |
| C4 | ctx | valid | success | 20 | 0.967 | 1.0 | 0 0 0 1 3 16 |
| C4 | node | valid | success | 20 | 0.967 | 1.0 | 0 0 0 1 3 16 |
| C5 | ctx | valid | success | 20 | 0.511 | 0.389 | 2 8 0 1 3 6 |
| C5 | node | valid | success | 20 | 0.511 | 0.389 | 2 8 0 1 3 6 |

Unexpected (valid < 0.5 / incorrect ≥ 0.5): A node: 0, A ctx: 0, C0 node: 10, C0 ctx: 10, C3 node: 7, C3 ctx: 7, C4 node: 0, C4 ctx: 0, C5 node: 10, C5 ctx: 10

### Per-step masks (m_node / m_ctx)

| Run | Succ | Step | Pred | Label | Text | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|
| 07ec0bf6 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 07ec0bf6 | True | s2 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.22/0.22 | 0.89/0.89 | 0.89/0.89 |
| 07ec0bf6 | True | s4 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 1.00/0.11 | 0.11/0.11 | 0.11/0.11 |
| 07ec0bf6 | True | s6 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/1.00 | 1.00/1.00 | 0.11/0.11 |
| 59810305 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 59810305 | True | s2 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.33/0.33 | 0.89/0.89 | 0.89/0.89 |
| 59810305 | True | s4 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 1.00/0.00 | 0.11/0.11 | 0.11/0.11 |
| 59810305 | True | s6 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/1.00 | 1.00/1.00 | 0.11/0.11 |
| 5b5eaa71 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 5b5eaa71 | True | s2 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.67/0.67 | 0.67/0.67 | 0.67/0.67 |
| 5b5eaa71 | True | s4 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 1.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 5b5eaa71 | True | s6 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/1.00 | 1.00/1.00 | 0.00/0.00 |
| 655b2a43 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 655b2a43 | True | s2 | user_turn | unverified | Sure, I can help with that. To proceed, could you pleas | 0.56/0.56 | 0.56/0.56 | 0.56/0.56 |
| 655b2a43 | True | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.78/0.78 | 1.00/1.00 | 1.00/1.00 |
| 655b2a43 | True | s6 | tool_call | unverified | Call get_user_details with user_id = anya_garcia_5901. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 655b2a43 | True | s8 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 1.00/0.00 | 0.11/0.11 | 0.11/0.11 |
| 655b2a43 | True | s10 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/1.00 | 1.00/1.00 | 0.11/0.11 |
| 78c107ed | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 78c107ed | True | s2 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.22/0.22 | 0.89/0.89 | 0.89/0.89 |
| 78c107ed | True | s4 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 1.00/0.11 | 0.11/0.11 | 0.11/0.11 |
| 78c107ed | True | s6 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/1.00 | 1.00/1.00 | 0.11/0.11 |
| a41818c2 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| a41818c2 | True | s2 | user_turn | unverified | Sure, I can help with that. To proceed, could you pleas | 0.56/0.56 | 0.56/0.56 | 0.56/0.56 |
| a41818c2 | True | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.67/0.67 | 1.00/1.00 | 1.00/1.00 |
| a41818c2 | True | s6 | tool_call | unverified | I'm sorry, but I can't process a cancellation for that  | 0.44/0.44 | 0.44/0.44 | 0.44/0.44 |
| a41818c2 | True | s8 | user_turn | unverified | I'm sorry, but I can't process a cancellation for that  | 0.00/0.00 | 0.11/0.11 | 0.00/0.00 |
| a41818c2 | True | s10 | user_turn | unverified | Call transfer_to_human_agents with summary = User Anya  | 1.00/0.00 | 0.11/0.00 | 0.11/0.00 |
| a41818c2 | True | s12 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/1.00 | 1.00/1.00 | 0.11/0.11 |
| aa08e645 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| aa08e645 | True | s2 | user_turn | unverified | Sure, I can help with that. To proceed, could you pleas | 0.56/0.56 | 0.56/0.56 | 0.56/0.56 |
| aa08e645 | True | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.67/0.67 | 1.00/1.00 | 1.00/1.00 |
| aa08e645 | True | s6 | tool_call | unverified | I'm sorry, but I'm not able to cancel that reservation. | 0.44/0.44 | 0.44/0.44 | 0.44/0.44 |
| aa08e645 | True | s8 | user_turn | unverified | I've double-checked the reservation record for 3RK2T9.  | 0.00/0.00 | 0.11/0.11 | 0.00/0.00 |
| aa08e645 | True | s10 | user_turn | unverified | Call transfer_to_human_agents with summary = User claim | 1.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| aa08e645 | True | s12 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/1.00 | 1.00/1.00 | 0.00/0.00 |
| adcf197e | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| adcf197e | True | s2 | user_turn | unverified | Sure, I can help with that. To proceed, could you pleas | 0.56/0.56 | 0.56/0.56 | 0.56/0.56 |
| adcf197e | True | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.67/0.67 | 1.00/1.00 | 1.00/1.00 |
| adcf197e | True | s6 | tool_call | unverified | I'm sorry, but I can't process a cancellation for that  | 0.44/0.44 | 0.44/0.44 | 0.44/0.44 |
| adcf197e | True | s8 | user_turn | unverified | Call transfer_to_human_agents with summary = User claim | 1.00/0.00 | 0.11/0.11 | 0.11/0.11 |
| adcf197e | True | s10 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/1.00 | 1.00/1.00 | 0.11/0.11 |
| c890f90b | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| c890f90b | True | s2 | user_turn | unverified | Sure, I can help with that. To proceed, could you pleas | 0.56/0.56 | 0.56/0.56 | 0.56/0.56 |
| c890f90b | True | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.67/0.67 | 1.00/1.00 | 1.00/1.00 |
| c890f90b | True | s6 | tool_call | unverified | I'm sorry, but I can't process a cancellation for that  | 0.44/0.44 | 0.44/0.44 | 0.44/0.44 |
| c890f90b | True | s8 | user_turn | unverified | Call transfer_to_human_agents with summary = User claim | 1.00/0.11 | 0.11/0.11 | 0.11/0.11 |
| c890f90b | True | s10 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/1.00 | 1.00/1.00 | 0.11/0.11 |
| e6daf449 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| e6daf449 | True | s2 | user_turn | unverified | Sure, I can help with that. To proceed, could you pleas | 0.56/0.56 | 0.56/0.56 | 0.56/0.56 |
| e6daf449 | True | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.67/0.67 | 1.00/1.00 | 1.00/1.00 |
| e6daf449 | True | s6 | tool_call | unverified | I'm sorry, but I can't process a cancellation for that  | 0.44/0.44 | 0.44/0.44 | 0.44/0.44 |
| e6daf449 | True | s8 | user_turn | unverified | Call transfer_to_human_agents with summary = User claim | 1.00/0.11 | 0.11/0.11 | 0.11/0.11 |
| e6daf449 | True | s10 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/1.00 | 1.00/1.00 | 0.11/0.11 |
| 058388c8 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 058388c8 | False | s2 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.30/0.30 | 0.90/0.90 | 0.90/0.90 |
| 058388c8 | False | s4 | tool_call | unverified | Sure, I can help with that. To proceed with the cancell | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 058388c8 | False | s6 | user_turn | incorrect | Call cancel_reservation with reservation_id = 3RK2T9. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 058388c8 | False | s8 | tool_call | unverified | Your reservation 3RK2T9 has been cancelled. A full refu | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 24ec2605 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 24ec2605 | False | s2 | user_turn | unverified | Sure, I can help with that. To proceed, could you pleas | 0.60/0.60 | 0.60/0.60 | 0.60/0.60 |
| 24ec2605 | False | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.70/0.70 | 1.00/1.00 | 1.00/1.00 |
| 24ec2605 | False | s6 | tool_call | unverified | Your reservation 3RK2T9 was indeed booked just 10 hours | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 24ec2605 | False | s8 | user_turn | incorrect | Call cancel_reservation with reservation_id = 3RK2T9. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 24ec2605 | False | s10 | tool_call | unverified | Your reservation 3RK2T9 has been cancelled and a full r | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 4a280c26 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 4a280c26 | False | s2 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.30/0.30 | 0.90/0.90 | 0.90/0.90 |
| 4a280c26 | False | s4 | tool_call | unverified | Sure, I can help you cancel that reservation. Just to c | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 4a280c26 | False | s6 | user_turn | incorrect | Call cancel_reservation with reservation_id = 3RK2T9. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 4a280c26 | False | s8 | tool_call | unverified | Your reservation 3RK2T9 has been cancelled and a full r | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 73c78a0d | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 73c78a0d | False | s2 | user_turn | unverified | Sure, I can help with that. Could you please provide yo | 0.60/0.60 | 0.60/0.60 | 0.60/0.60 |
| 73c78a0d | False | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.70/0.70 | 1.00/1.00 | 1.00/1.00 |
| 73c78a0d | False | s6 | tool_call | unverified | I've pulled up the details for reservation 3RK2T9. It's | 0.50/0.50 | 0.50/0.50 | 0.50/0.50 |
| 73c78a0d | False | s8 | user_turn | unverified | Call get_user_details with user_id = anya_garcia_5901. | 0.10/0.00 | 0.10/0.10 | 0.10/0.10 |
| 73c78a0d | False | s10 | tool_call | unverified | I've double-checked the booking record. The reservation | 0.00/0.00 | 0.10/0.10 | 0.00/0.00 |
| 73c78a0d | False | s12 | user_turn | unverified | I'm sorry, but the policy does not allow a full refund  | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 73c78a0d | False | s14 | user_turn | unverified | I've checked the booking record for reservation 3RK2T9. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 73c78a0d | False | s16 | user_turn | unverified | I understand. To proceed, I'll need your explicit confi | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 73c78a0d | False | s18 | user_turn | incorrect | Call cancel_reservation with reservation_id = 3RK2T9. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 73c78a0d | False | s20 | tool_call | unverified | Your reservation 3RK2T9 has been cancelled. A refund wi | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 7f5cbcd7 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 7f5cbcd7 | False | s2 | user_turn | unverified | Sure, I can help with that. Could you please provide yo | 0.60/0.60 | 0.60/0.60 | 0.60/0.60 |
| 7f5cbcd7 | False | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.70/0.70 | 1.00/1.00 | 1.00/1.00 |
| 7f5cbcd7 | False | s6 | tool_call | incorrect | Call cancel_reservation with reservation_id = 3RK2T9. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 7f5cbcd7 | False | s8 | tool_call | unverified | Your reservation 3RK2T9 has been cancelled successfully | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 7f5cbcd7 | False | s10 | user_turn | unverified | Your refund will be credited back to the original payme | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 7f5cbcd7 | False | s12 | user_turn | unverified | You're very welcome! If anything comes up, just let me  | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| a6fb29f3 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| a6fb29f3 | False | s2 | user_turn | unverified | Sure, I can help with that. Could you please provide yo | 0.60/0.60 | 0.60/0.60 | 0.60/0.60 |
| a6fb29f3 | False | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.70/0.70 | 1.00/1.00 | 1.00/1.00 |
| a6fb29f3 | False | s6 | tool_call | incorrect | Call cancel_reservation with reservation_id = 3RK2T9. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| a6fb29f3 | False | s8 | tool_call | unverified | Your reservation 3RK2T9 has been cancelled successfully | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| a6fb29f3 | False | s10 | user_turn | unverified | Your refund will be credited back to the original payme | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| afce6c04 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| afce6c04 | False | s2 | user_turn | unverified | Sure, I can help with that. To proceed, could you pleas | 0.60/0.60 | 0.60/0.60 | 0.60/0.60 |
| afce6c04 | False | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.70/0.70 | 1.00/1.00 | 1.00/1.00 |
| afce6c04 | False | s6 | tool_call | unverified | Call get_flight_status with date = 2024-05-19; flight_n | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| afce6c04 | False | s8 | tool_call | unverified | Your reservation 3RK2T9 was booked less than 24 hours a | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| afce6c04 | False | s10 | user_turn | incorrect | Call cancel_reservation with reservation_id = 3RK2T9. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| afce6c04 | False | s12 | tool_call | unverified | Your reservation 3RK2T9 has been cancelled. A full refu | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| b081606a | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| b081606a | False | s2 | user_turn | unverified | Sure, I can help with that. To proceed, could you pleas | 0.60/0.60 | 0.60/0.60 | 0.60/0.60 |
| b081606a | False | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.70/0.70 | 1.00/1.00 | 1.00/1.00 |
| b081606a | False | s6 | tool_call | unverified | Your reservation 3RK2T9 was indeed booked just 10 hours | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| b081606a | False | s8 | user_turn | incorrect | Call cancel_reservation with reservation_id = 3RK2T9. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| b081606a | False | s10 | tool_call | unverified | Your reservation 3RK2T9 has been cancelled and a full r | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| be82d372 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| be82d372 | False | s2 | user_turn | unverified | Sure, I can help with that. To proceed, could you pleas | 0.60/0.60 | 0.60/0.60 | 0.60/0.60 |
| be82d372 | False | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.70/0.70 | 1.00/1.00 | 1.00/1.00 |
| be82d372 | False | s6 | tool_call | unverified | Your reservation 3RK2T9 was indeed booked just 10 hours | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| be82d372 | False | s8 | user_turn | incorrect | Call cancel_reservation with reservation_id = 3RK2T9. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| be82d372 | False | s10 | tool_call | unverified | Your reservation 3RK2T9 has been cancelled and a full r | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| c4902f46 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| c4902f46 | False | s2 | user_turn | unverified | Sure, I can help with that. To proceed, could you pleas | 0.60/0.60 | 0.60/0.60 | 0.60/0.60 |
| c4902f46 | False | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.70/0.70 | 1.00/1.00 | 1.00/1.00 |
| c4902f46 | False | s6 | tool_call | unverified | I'm looking at the reservation details for 3RK2T9. It s | 0.00/0.00 | 0.10/0.10 | 0.00/0.00 |
| c4902f46 | False | s8 | user_turn | unverified | I'm sorry, but the system records show that reservation | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| c4902f46 | False | s10 | user_turn | unverified | Sure, I can cancel reservation 3RK2T9 for you. The canc | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| c4902f46 | False | s12 | user_turn | incorrect | Call cancel_reservation with reservation_id = 3RK2T9. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| c4902f46 | False | s14 | tool_call | unverified | Your reservation 3RK2T9 has been cancelled. A refund wi | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| d5456653 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| d5456653 | False | s2 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.30/0.30 | 0.90/0.90 | 0.90/0.90 |
| d5456653 | False | s4 | tool_call | unverified | Sure, I can help you cancel that reservation. Just to c | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| d5456653 | False | s6 | user_turn | incorrect | Call cancel_reservation with reservation_id = 3RK2T9. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| d5456653 | False | s8 | tool_call | unverified | Your reservation 3RK2T9 has been cancelled. The refund  | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| d5456653 | False | s10 | user_turn | unverified | Yes, the full amount you paid will be refunded to the o | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| d5456653 | False | s12 | user_turn | unverified | You're welcome! I'm glad I could help. If you need anyt | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| fc2b9a57 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| fc2b9a57 | False | s2 | user_turn | unverified | Sure, I can help with that. To proceed, could you pleas | 0.60/0.60 | 0.60/0.60 | 0.60/0.60 |
| fc2b9a57 | False | s4 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.70/0.70 | 1.00/1.00 | 1.00/1.00 |
| fc2b9a57 | False | s6 | tool_call | unverified | I've pulled up your reservation (ID 3RK2T9). Since you  | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| fc2b9a57 | False | s8 | user_turn | incorrect | Call cancel_reservation with reservation_id = 3RK2T9. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| fc2b9a57 | False | s10 | tool_call | unverified | Your reservation 3RK2T9 has been cancelled and a full r | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| fcce7c71 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| fcce7c71 | False | s2 | user_turn | valid | Call get_reservation_details with reservation_id = 3RK2 | 0.30/0.30 | 0.90/0.90 | 0.90/0.90 |
| fcce7c71 | False | s4 | tool_call | unverified | I've pulled up your reservation 3RK2T9. It was booked 1 | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| fcce7c71 | False | s6 | user_turn | incorrect | Call cancel_reservation with reservation_id = 3RK2T9. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| fcce7c71 | False | s8 | tool_call | unverified | Your reservation 3RK2T9 has been cancelled. A full refu | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |

## Task 9

C5 cost: {'seconds': 1.9, 'nli_forward_passes_uncached': 0, 'nli_directional_pairs_requested': 11430, 'n_mcs_runs': 340}; stage-2 counters: {'candidates_message_edges': 693, 'dropped_tool_unmatched': 194, 'dropped_tool_conflict': 0}

Message coverage (indicator counts): {"C3": {"node": 722, "ctx": 693, "node_only": 29, "indicators": 1074}, "C4": {"node": 725, "ctx": 725, "node_only": 0, "indicators": 1074}, "C5": {"node": 499, "ctx": 499, "node_only": 0, "indicators": 1074}}

C5 − C4 on message steps: {"node|same|unverified": 43, "ctx|same|unverified": 43, "node|down|valid": 14, "ctx|down|valid": 14, "node|down|unverified": 9, "ctx|down|unverified": 9}

| Variant | Target | Group | Runs | n | mean | median | bins 0 / (0,.25) / [.25,.5) / [.5,.75) / [.75,1) / 1 |
|---|---|---|---|---|---|---|---|
| A | ctx | incorrect:cancel_reservation | failed | 6 | 0.0 | 0.0 | 6 0 0 0 0 0 |
| A | node | incorrect:cancel_reservation | failed | 6 | 0.0 | 0.0 | 6 0 0 0 0 0 |
| C0 | ctx | incorrect:cancel_reservation | failed | 6 | 0.0 | 0.0 | 6 0 0 0 0 0 |
| C0 | node | incorrect:cancel_reservation | failed | 6 | 0.0 | 0.0 | 6 0 0 0 0 0 |
| C3 | ctx | incorrect:cancel_reservation | failed | 6 | 0.0 | 0.0 | 6 0 0 0 0 0 |
| C3 | node | incorrect:cancel_reservation | failed | 6 | 0.0 | 0.0 | 6 0 0 0 0 0 |
| C4 | ctx | incorrect:cancel_reservation | failed | 6 | 0.0 | 0.0 | 6 0 0 0 0 0 |
| C4 | node | incorrect:cancel_reservation | failed | 6 | 0.0 | 0.0 | 6 0 0 0 0 0 |
| C5 | ctx | incorrect:cancel_reservation | failed | 6 | 0.0 | 0.0 | 6 0 0 0 0 0 |
| C5 | node | incorrect:cancel_reservation | failed | 6 | 0.0 | 0.0 | 6 0 0 0 0 0 |
| A | ctx | incorrect:update_reservation_flights | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| A | node | incorrect:update_reservation_flights | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C0 | ctx | incorrect:update_reservation_flights | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C0 | node | incorrect:update_reservation_flights | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C3 | ctx | incorrect:update_reservation_flights | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C3 | node | incorrect:update_reservation_flights | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C4 | ctx | incorrect:update_reservation_flights | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C4 | node | incorrect:update_reservation_flights | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C5 | ctx | incorrect:update_reservation_flights | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C5 | node | incorrect:update_reservation_flights | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| A | ctx | incorrect | failed | 8 | 0.0 | 0.0 | 8 0 0 0 0 0 |
| A | node | incorrect | failed | 8 | 0.0 | 0.0 | 8 0 0 0 0 0 |
| C0 | ctx | incorrect | failed | 8 | 0.0 | 0.0 | 8 0 0 0 0 0 |
| C0 | node | incorrect | failed | 8 | 0.0 | 0.0 | 8 0 0 0 0 0 |
| C3 | ctx | incorrect | failed | 8 | 0.0 | 0.0 | 8 0 0 0 0 0 |
| C3 | node | incorrect | failed | 8 | 0.0 | 0.0 | 8 0 0 0 0 0 |
| C4 | ctx | incorrect | failed | 8 | 0.0 | 0.0 | 8 0 0 0 0 0 |
| C4 | node | incorrect | failed | 8 | 0.0 | 0.0 | 8 0 0 0 0 0 |
| C5 | ctx | incorrect | failed | 8 | 0.0 | 0.0 | 8 0 0 0 0 0 |
| C5 | node | incorrect | failed | 8 | 0.0 | 0.0 | 8 0 0 0 0 0 |
| A | ctx | message|pred=none | failed | 4 | 1.0 | 1.0 | 0 0 0 0 0 4 |
| A | node | message|pred=none | failed | 4 | 1.0 | 1.0 | 0 0 0 0 0 4 |
| C0 | ctx | message|pred=none | failed | 4 | 0.985 | 1.0 | 0 0 0 0 1 3 |
| C0 | node | message|pred=none | failed | 4 | 0.985 | 1.0 | 0 0 0 0 1 3 |
| C3 | ctx | message|pred=none | failed | 4 | 1.0 | 1.0 | 0 0 0 0 0 4 |
| C3 | node | message|pred=none | failed | 4 | 1.0 | 1.0 | 0 0 0 0 0 4 |
| C4 | ctx | message|pred=none | failed | 4 | 1.0 | 1.0 | 0 0 0 0 0 4 |
| C4 | node | message|pred=none | failed | 4 | 1.0 | 1.0 | 0 0 0 0 0 4 |
| C5 | ctx | message|pred=none | failed | 4 | 1.0 | 1.0 | 0 0 0 0 0 4 |
| C5 | node | message|pred=none | failed | 4 | 1.0 | 1.0 | 0 0 0 0 0 4 |
| A | ctx | message|pred=none | success | 17 | 1.0 | 1.0 | 0 0 0 0 0 17 |
| A | node | message|pred=none | success | 17 | 1.0 | 1.0 | 0 0 0 0 0 17 |
| C0 | ctx | message|pred=none | success | 17 | 0.934 | 0.938 | 0 0 0 1 10 6 |
| C0 | node | message|pred=none | success | 17 | 0.934 | 0.938 | 0 0 0 1 10 6 |
| C3 | ctx | message|pred=none | success | 17 | 1.0 | 1.0 | 0 0 0 0 0 17 |
| C3 | node | message|pred=none | success | 17 | 1.0 | 1.0 | 0 0 0 0 0 17 |
| C4 | ctx | message|pred=none | success | 17 | 1.0 | 1.0 | 0 0 0 0 0 17 |
| C4 | node | message|pred=none | success | 17 | 1.0 | 1.0 | 0 0 0 0 0 17 |
| C5 | ctx | message|pred=none | success | 17 | 1.0 | 1.0 | 0 0 0 0 0 17 |
| C5 | node | message|pred=none | success | 17 | 1.0 | 1.0 | 0 0 0 0 0 17 |
| A | ctx | message|pred=tool_call | failed | 10 | 0.118 | 0.0 | 6 3 0 0 1 0 |
| A | node | message|pred=tool_call | failed | 10 | 0.118 | 0.0 | 6 3 0 0 1 0 |
| C0 | ctx | message|pred=tool_call | failed | 10 | 0.012 | 0.0 | 8 2 0 0 0 0 |
| C0 | node | message|pred=tool_call | failed | 10 | 0.012 | 0.0 | 8 2 0 0 0 0 |
| C3 | ctx | message|pred=tool_call | failed | 10 | 0.088 | 0.0 | 8 1 0 0 1 0 |
| C3 | node | message|pred=tool_call | failed | 10 | 0.094 | 0.0 | 7 2 0 0 1 0 |
| C4 | ctx | message|pred=tool_call | failed | 10 | 0.1 | 0.0 | 6 3 0 0 1 0 |
| C4 | node | message|pred=tool_call | failed | 10 | 0.1 | 0.0 | 6 3 0 0 1 0 |
| C5 | ctx | message|pred=tool_call | failed | 10 | 0.006 | 0.0 | 9 1 0 0 0 0 |
| C5 | node | message|pred=tool_call | failed | 10 | 0.006 | 0.0 | 9 1 0 0 0 0 |
| A | ctx | message|pred=tool_call | success | 19 | 0.891 | 1.0 | 0 2 0 0 3 14 |
| A | node | message|pred=tool_call | success | 19 | 0.891 | 1.0 | 0 2 0 0 3 14 |
| C0 | ctx | message|pred=tool_call | success | 19 | 0.237 | 0.25 | 2 7 7 3 0 0 |
| C0 | node | message|pred=tool_call | success | 19 | 0.25 | 0.25 | 2 7 7 3 0 0 |
| C3 | ctx | message|pred=tool_call | success | 19 | 0.79 | 0.938 | 1 2 0 0 16 0 |
| C3 | node | message|pred=tool_call | success | 19 | 0.882 | 1.0 | 1 1 0 0 4 13 |
| C4 | ctx | message|pred=tool_call | success | 19 | 0.882 | 1.0 | 0 2 0 0 4 13 |
| C4 | node | message|pred=tool_call | success | 19 | 0.882 | 1.0 | 0 2 0 0 4 13 |
| C5 | ctx | message|pred=tool_call | success | 19 | 0.197 | 0.125 | 4 6 7 2 0 0 |
| C5 | node | message|pred=tool_call | success | 19 | 0.197 | 0.125 | 4 6 7 2 0 0 |
| A | ctx | message|pred=user_turn | failed | 4 | 0.162 | 0.029 | 2 1 0 1 0 0 |
| A | node | message|pred=user_turn | failed | 4 | 0.162 | 0.029 | 2 1 0 1 0 0 |
| C0 | ctx | message|pred=user_turn | failed | 4 | 0.147 | 0.0 | 3 0 0 1 0 0 |
| C0 | node | message|pred=user_turn | failed | 4 | 0.147 | 0.0 | 3 0 0 1 0 0 |
| C3 | ctx | message|pred=user_turn | failed | 4 | 0.147 | 0.0 | 3 0 0 1 0 0 |
| C3 | node | message|pred=user_turn | failed | 4 | 0.147 | 0.0 | 3 0 0 1 0 0 |
| C4 | ctx | message|pred=user_turn | failed | 4 | 0.176 | 0.059 | 1 2 0 1 0 0 |
| C4 | node | message|pred=user_turn | failed | 4 | 0.176 | 0.059 | 1 2 0 1 0 0 |
| C5 | ctx | message|pred=user_turn | failed | 4 | 0.147 | 0.0 | 3 0 0 1 0 0 |
| C5 | node | message|pred=user_turn | failed | 4 | 0.147 | 0.0 | 3 0 0 1 0 0 |
| A | ctx | message|pred=user_turn | success | 12 | 0.536 | 0.562 | 0 1 0 10 1 0 |
| A | node | message|pred=user_turn | success | 12 | 0.536 | 0.562 | 0 1 0 10 1 0 |
| C0 | ctx | message|pred=user_turn | success | 12 | 0.458 | 0.562 | 2 0 0 10 0 0 |
| C0 | node | message|pred=user_turn | success | 12 | 0.458 | 0.562 | 2 0 0 10 0 0 |
| C3 | ctx | message|pred=user_turn | success | 12 | 0.458 | 0.562 | 2 0 0 10 0 0 |
| C3 | node | message|pred=user_turn | success | 12 | 0.458 | 0.562 | 2 0 0 10 0 0 |
| C4 | ctx | message|pred=user_turn | success | 12 | 0.458 | 0.562 | 2 0 0 10 0 0 |
| C4 | node | message|pred=user_turn | success | 12 | 0.458 | 0.562 | 2 0 0 10 0 0 |
| C5 | ctx | message|pred=user_turn | success | 12 | 0.458 | 0.562 | 2 0 0 10 0 0 |
| C5 | node | message|pred=user_turn | success | 12 | 0.458 | 0.562 | 2 0 0 10 0 0 |
| A | ctx | unverified:get_flight_status | failed | 1 | 0.176 | 0.176 | 0 1 0 0 0 0 |
| A | node | unverified:get_flight_status | failed | 1 | 0.176 | 0.176 | 0 1 0 0 0 0 |
| C0 | ctx | unverified:get_flight_status | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | node | unverified:get_flight_status | failed | 1 | 0.176 | 0.176 | 0 1 0 0 0 0 |
| C3 | ctx | unverified:get_flight_status | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | node | unverified:get_flight_status | failed | 1 | 0.176 | 0.176 | 0 1 0 0 0 0 |
| C4 | ctx | unverified:get_flight_status | failed | 1 | 0.176 | 0.176 | 0 1 0 0 0 0 |
| C4 | node | unverified:get_flight_status | failed | 1 | 0.176 | 0.176 | 0 1 0 0 0 0 |
| C5 | ctx | unverified:get_flight_status | failed | 1 | 0.176 | 0.176 | 0 1 0 0 0 0 |
| C5 | node | unverified:get_flight_status | failed | 1 | 0.176 | 0.176 | 0 1 0 0 0 0 |
| A | ctx | unverified:get_flight_status | success | 5 | 0.075 | 0.125 | 2 3 0 0 0 0 |
| A | node | unverified:get_flight_status | success | 5 | 0.075 | 0.125 | 2 3 0 0 0 0 |
| C0 | ctx | unverified:get_flight_status | success | 5 | 0.075 | 0.125 | 2 3 0 0 0 0 |
| C0 | node | unverified:get_flight_status | success | 5 | 0.075 | 0.125 | 2 3 0 0 0 0 |
| C3 | ctx | unverified:get_flight_status | success | 5 | 0.075 | 0.125 | 2 3 0 0 0 0 |
| C3 | node | unverified:get_flight_status | success | 5 | 0.075 | 0.125 | 2 3 0 0 0 0 |
| C4 | ctx | unverified:get_flight_status | success | 5 | 0.075 | 0.125 | 2 3 0 0 0 0 |
| C4 | node | unverified:get_flight_status | success | 5 | 0.075 | 0.125 | 2 3 0 0 0 0 |
| C5 | ctx | unverified:get_flight_status | success | 5 | 0.075 | 0.125 | 2 3 0 0 0 0 |
| C5 | node | unverified:get_flight_status | success | 5 | 0.075 | 0.125 | 2 3 0 0 0 0 |
| A | ctx | unverified:get_reservation_details | failed | 12 | 0.77 | 0.706 | 0 0 0 8 4 0 |
| A | node | unverified:get_reservation_details | failed | 12 | 0.77 | 0.706 | 0 0 0 8 4 0 |
| C0 | ctx | unverified:get_reservation_details | failed | 12 | 0.451 | 0.529 | 3 1 0 6 2 0 |
| C0 | node | unverified:get_reservation_details | failed | 12 | 0.77 | 0.706 | 0 0 0 8 4 0 |
| C3 | ctx | unverified:get_reservation_details | failed | 12 | 0.451 | 0.529 | 3 1 0 6 2 0 |
| C3 | node | unverified:get_reservation_details | failed | 12 | 0.774 | 0.706 | 0 0 0 8 4 0 |
| C4 | ctx | unverified:get_reservation_details | failed | 12 | 0.77 | 0.706 | 0 0 0 8 4 0 |
| C4 | node | unverified:get_reservation_details | failed | 12 | 0.774 | 0.706 | 0 0 0 8 4 0 |
| C5 | ctx | unverified:get_reservation_details | failed | 12 | 0.77 | 0.706 | 0 0 0 8 4 0 |
| C5 | node | unverified:get_reservation_details | failed | 12 | 0.774 | 0.706 | 0 0 0 8 4 0 |
| A | ctx | unverified:get_reservation_details | success | 40 | 0.769 | 0.688 | 0 0 0 25 15 0 |
| A | node | unverified:get_reservation_details | success | 40 | 0.769 | 0.688 | 0 0 0 25 15 0 |
| C0 | ctx | unverified:get_reservation_details | success | 40 | 0.428 | 0.5 | 2 12 3 17 6 0 |
| C0 | node | unverified:get_reservation_details | success | 40 | 0.779 | 0.688 | 0 0 0 24 16 0 |
| C3 | ctx | unverified:get_reservation_details | success | 40 | 0.428 | 0.5 | 2 12 3 17 6 0 |
| C3 | node | unverified:get_reservation_details | success | 40 | 0.779 | 0.688 | 0 0 0 24 16 0 |
| C4 | ctx | unverified:get_reservation_details | success | 40 | 0.769 | 0.688 | 0 0 0 25 15 0 |
| C4 | node | unverified:get_reservation_details | success | 40 | 0.769 | 0.688 | 0 0 0 25 15 0 |
| C5 | ctx | unverified:get_reservation_details | success | 40 | 0.769 | 0.688 | 0 0 0 25 15 0 |
| C5 | node | unverified:get_reservation_details | success | 40 | 0.769 | 0.688 | 0 0 0 25 15 0 |
| A | ctx | unverified:get_user_details | failed | 2 | 0.353 | 0.353 | 0 0 2 0 0 0 |
| A | node | unverified:get_user_details | failed | 2 | 0.353 | 0.353 | 0 0 2 0 0 0 |
| C0 | ctx | unverified:get_user_details | failed | 2 | 0.176 | 0.176 | 1 0 1 0 0 0 |
| C0 | node | unverified:get_user_details | failed | 2 | 0.353 | 0.353 | 0 0 2 0 0 0 |
| C3 | ctx | unverified:get_user_details | failed | 2 | 0.176 | 0.176 | 1 0 1 0 0 0 |
| C3 | node | unverified:get_user_details | failed | 2 | 0.353 | 0.353 | 0 0 2 0 0 0 |
| C4 | ctx | unverified:get_user_details | failed | 2 | 0.353 | 0.353 | 0 0 2 0 0 0 |
| C4 | node | unverified:get_user_details | failed | 2 | 0.353 | 0.353 | 0 0 2 0 0 0 |
| C5 | ctx | unverified:get_user_details | failed | 2 | 0.353 | 0.353 | 0 0 2 0 0 0 |
| C5 | node | unverified:get_user_details | failed | 2 | 0.353 | 0.353 | 0 0 2 0 0 0 |
| A | ctx | unverified:get_user_details | success | 6 | 0.291 | 0.312 | 0 0 6 0 0 0 |
| A | node | unverified:get_user_details | success | 6 | 0.291 | 0.312 | 0 0 6 0 0 0 |
| C0 | ctx | unverified:get_user_details | success | 6 | 0.125 | 0.125 | 0 5 1 0 0 0 |
| C0 | node | unverified:get_user_details | success | 6 | 0.312 | 0.312 | 0 0 6 0 0 0 |
| C3 | ctx | unverified:get_user_details | success | 6 | 0.125 | 0.125 | 0 5 1 0 0 0 |
| C3 | node | unverified:get_user_details | success | 6 | 0.312 | 0.312 | 0 0 6 0 0 0 |
| C4 | ctx | unverified:get_user_details | success | 6 | 0.291 | 0.312 | 0 0 6 0 0 0 |
| C4 | node | unverified:get_user_details | success | 6 | 0.291 | 0.312 | 0 0 6 0 0 0 |
| C5 | ctx | unverified:get_user_details | success | 6 | 0.291 | 0.312 | 0 0 6 0 0 0 |
| C5 | node | unverified:get_user_details | success | 6 | 0.291 | 0.312 | 0 0 6 0 0 0 |
| A | ctx | unverified:message | failed | 18 | 0.324 | 0.059 | 8 4 0 1 1 4 |
| A | node | unverified:message | failed | 18 | 0.324 | 0.059 | 8 4 0 1 1 4 |
| C0 | ctx | unverified:message | failed | 18 | 0.258 | 0.0 | 11 2 0 1 1 3 |
| C0 | node | unverified:message | failed | 18 | 0.258 | 0.0 | 11 2 0 1 1 3 |
| C3 | ctx | unverified:message | failed | 18 | 0.304 | 0.0 | 11 1 0 1 1 4 |
| C3 | node | unverified:message | failed | 18 | 0.307 | 0.0 | 10 2 0 1 1 4 |
| C4 | ctx | unverified:message | failed | 18 | 0.317 | 0.059 | 7 5 0 1 1 4 |
| C4 | node | unverified:message | failed | 18 | 0.317 | 0.059 | 7 5 0 1 1 4 |
| C5 | ctx | unverified:message | failed | 18 | 0.258 | 0.0 | 12 1 0 1 0 4 |
| C5 | node | unverified:message | failed | 18 | 0.258 | 0.0 | 12 1 0 1 0 4 |
| A | ctx | unverified:message | success | 34 | 0.777 | 1.0 | 0 3 0 10 3 18 |
| A | node | unverified:message | success | 34 | 0.777 | 1.0 | 0 3 0 10 3 18 |
| C0 | ctx | unverified:message | success | 34 | 0.643 | 0.594 | 3 3 1 11 10 6 |
| C0 | node | unverified:message | success | 34 | 0.649 | 0.594 | 3 3 1 11 10 6 |
| C3 | ctx | unverified:message | success | 34 | 0.717 | 0.938 | 3 2 0 10 2 17 |
| C3 | node | unverified:message | success | 34 | 0.744 | 0.969 | 3 1 0 10 3 17 |
| C4 | ctx | unverified:message | success | 34 | 0.744 | 0.969 | 2 2 0 10 3 17 |
| C4 | node | unverified:message | success | 34 | 0.744 | 0.969 | 2 2 0 10 3 17 |
| C5 | ctx | unverified:message | success | 34 | 0.676 | 0.781 | 3 3 1 10 0 17 |
| C5 | node | unverified:message | success | 34 | 0.676 | 0.781 | 3 3 1 10 0 17 |
| A | ctx | unverified:search_direct_flight | failed | 4 | 0.029 | 0.029 | 2 2 0 0 0 0 |
| A | node | unverified:search_direct_flight | failed | 4 | 0.029 | 0.029 | 2 2 0 0 0 0 |
| C0 | ctx | unverified:search_direct_flight | failed | 4 | 0.0 | 0.0 | 4 0 0 0 0 0 |
| C0 | node | unverified:search_direct_flight | failed | 4 | 0.029 | 0.029 | 2 2 0 0 0 0 |
| C3 | ctx | unverified:search_direct_flight | failed | 4 | 0.0 | 0.0 | 4 0 0 0 0 0 |
| C3 | node | unverified:search_direct_flight | failed | 4 | 0.029 | 0.029 | 2 2 0 0 0 0 |
| C4 | ctx | unverified:search_direct_flight | failed | 4 | 0.029 | 0.029 | 2 2 0 0 0 0 |
| C4 | node | unverified:search_direct_flight | failed | 4 | 0.029 | 0.029 | 2 2 0 0 0 0 |
| C5 | ctx | unverified:search_direct_flight | failed | 4 | 0.029 | 0.029 | 2 2 0 0 0 0 |
| C5 | node | unverified:search_direct_flight | failed | 4 | 0.029 | 0.029 | 2 2 0 0 0 0 |
| A | ctx | unverified:search_direct_flight | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| A | node | unverified:search_direct_flight | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C0 | ctx | unverified:search_direct_flight | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C0 | node | unverified:search_direct_flight | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C3 | ctx | unverified:search_direct_flight | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C3 | node | unverified:search_direct_flight | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C4 | ctx | unverified:search_direct_flight | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C4 | node | unverified:search_direct_flight | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C5 | ctx | unverified:search_direct_flight | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C5 | node | unverified:search_direct_flight | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| A | ctx | unverified:search_onestop_flight | failed | 3 | 0.0 | 0.0 | 3 0 0 0 0 0 |
| A | node | unverified:search_onestop_flight | failed | 3 | 0.0 | 0.0 | 3 0 0 0 0 0 |
| C0 | ctx | unverified:search_onestop_flight | failed | 3 | 0.0 | 0.0 | 3 0 0 0 0 0 |
| C0 | node | unverified:search_onestop_flight | failed | 3 | 0.0 | 0.0 | 3 0 0 0 0 0 |
| C3 | ctx | unverified:search_onestop_flight | failed | 3 | 0.0 | 0.0 | 3 0 0 0 0 0 |
| C3 | node | unverified:search_onestop_flight | failed | 3 | 0.0 | 0.0 | 3 0 0 0 0 0 |
| C4 | ctx | unverified:search_onestop_flight | failed | 3 | 0.0 | 0.0 | 3 0 0 0 0 0 |
| C4 | node | unverified:search_onestop_flight | failed | 3 | 0.0 | 0.0 | 3 0 0 0 0 0 |
| C5 | ctx | unverified:search_onestop_flight | failed | 3 | 0.0 | 0.0 | 3 0 0 0 0 0 |
| C5 | node | unverified:search_onestop_flight | failed | 3 | 0.0 | 0.0 | 3 0 0 0 0 0 |
| A | ctx | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | node | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | ctx | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | node | unverified:transfer_to_human_agents | failed | 1 | 0.059 | 0.059 | 0 1 0 0 0 0 |
| C3 | ctx | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | node | unverified:transfer_to_human_agents | failed | 1 | 0.824 | 0.824 | 0 0 0 0 1 0 |
| C4 | ctx | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | node | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | ctx | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | node | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | ctx | unverified:transfer_to_human_agents | success | 16 | 0.234 | 0.25 | 3 4 7 2 0 0 |
| A | node | unverified:transfer_to_human_agents | success | 16 | 0.234 | 0.25 | 3 4 7 2 0 0 |
| C0 | ctx | unverified:transfer_to_human_agents | success | 16 | 0.078 | 0.062 | 7 9 0 0 0 0 |
| C0 | node | unverified:transfer_to_human_agents | success | 16 | 0.281 | 0.281 | 1 5 7 3 0 0 |
| C3 | ctx | unverified:transfer_to_human_agents | success | 16 | 0.078 | 0.062 | 7 9 0 0 0 0 |
| C3 | node | unverified:transfer_to_human_agents | success | 16 | 0.938 | 0.938 | 0 0 0 0 16 0 |
| C4 | ctx | unverified:transfer_to_human_agents | success | 16 | 0.234 | 0.25 | 3 4 7 2 0 0 |
| C4 | node | unverified:transfer_to_human_agents | success | 16 | 0.234 | 0.25 | 3 4 7 2 0 0 |
| C5 | ctx | unverified:transfer_to_human_agents | success | 16 | 0.234 | 0.25 | 3 4 7 2 0 0 |
| C5 | node | unverified:transfer_to_human_agents | success | 16 | 0.234 | 0.25 | 3 4 7 2 0 0 |
| A | ctx | unverified | failed | 41 | 0.392 | 0.176 | 14 7 2 9 5 4 |
| A | node | unverified | failed | 41 | 0.392 | 0.176 | 14 7 2 9 5 4 |
| C0 | ctx | unverified | failed | 41 | 0.254 | 0.0 | 24 3 1 7 3 3 |
| C0 | node | unverified | failed | 41 | 0.364 | 0.059 | 16 6 2 9 5 3 |
| C3 | ctx | unverified | failed | 41 | 0.274 | 0.0 | 24 2 1 7 3 4 |
| C3 | node | unverified | failed | 41 | 0.406 | 0.353 | 15 5 2 9 6 4 |
| C4 | ctx | unverified | failed | 41 | 0.389 | 0.176 | 13 8 2 9 5 4 |
| C4 | node | unverified | failed | 41 | 0.39 | 0.176 | 13 8 2 9 5 4 |
| C5 | ctx | unverified | failed | 41 | 0.363 | 0.059 | 18 4 2 9 4 4 |
| C5 | node | unverified | failed | 41 | 0.364 | 0.059 | 18 4 2 9 4 4 |
| A | ctx | unverified | success | 103 | 0.612 | 0.688 | 7 10 13 37 18 18 |
| A | node | unverified | success | 103 | 0.612 | 0.688 | 7 10 13 37 18 18 |
| C0 | ctx | unverified | success | 103 | 0.402 | 0.438 | 16 32 5 28 16 6 |
| C0 | node | unverified | success | 103 | 0.582 | 0.688 | 8 11 14 38 26 6 |
| C3 | ctx | unverified | success | 103 | 0.426 | 0.5 | 16 31 4 27 8 17 |
| C3 | node | unverified | success | 103 | 0.716 | 0.75 | 7 4 6 34 35 17 |
| C4 | ctx | unverified | success | 103 | 0.601 | 0.688 | 9 9 13 37 18 17 |
| C4 | node | unverified | success | 103 | 0.601 | 0.688 | 9 9 13 37 18 17 |
| C5 | ctx | unverified | success | 103 | 0.579 | 0.688 | 10 10 14 37 15 17 |
| C5 | node | unverified | success | 103 | 0.579 | 0.688 | 10 10 14 37 15 17 |
| A | ctx | valid:message | success | 14 | 0.996 | 1.0 | 0 0 0 0 1 13 |
| A | node | valid:message | success | 14 | 0.996 | 1.0 | 0 0 0 0 1 13 |
| C0 | ctx | valid:message | success | 14 | 0.286 | 0.281 | 1 4 6 3 0 0 |
| C0 | node | valid:message | success | 14 | 0.29 | 0.281 | 1 4 6 3 0 0 |
| C3 | ctx | valid:message | success | 14 | 0.938 | 0.938 | 0 0 0 0 14 0 |
| C3 | node | valid:message | success | 14 | 0.996 | 1.0 | 0 0 0 0 1 13 |
| C4 | ctx | valid:message | success | 14 | 0.996 | 1.0 | 0 0 0 0 1 13 |
| C4 | node | valid:message | success | 14 | 0.996 | 1.0 | 0 0 0 0 1 13 |
| C5 | ctx | valid:message | success | 14 | 0.232 | 0.25 | 3 3 6 2 0 0 |
| C5 | node | valid:message | success | 14 | 0.232 | 0.25 | 3 3 6 2 0 0 |
| A | ctx | valid:search_direct_flight | failed | 4 | 0.514 | 0.529 | 0 0 1 3 0 0 |
| A | node | valid:search_direct_flight | failed | 4 | 0.514 | 0.529 | 0 0 1 3 0 0 |
| C0 | ctx | valid:search_direct_flight | failed | 4 | 0.397 | 0.529 | 1 0 0 3 0 0 |
| C0 | node | valid:search_direct_flight | failed | 4 | 0.514 | 0.529 | 0 0 1 3 0 0 |
| C3 | ctx | valid:search_direct_flight | failed | 4 | 0.397 | 0.529 | 1 0 0 3 0 0 |
| C3 | node | valid:search_direct_flight | failed | 4 | 0.529 | 0.529 | 0 0 0 4 0 0 |
| C4 | ctx | valid:search_direct_flight | failed | 4 | 0.529 | 0.529 | 0 0 0 4 0 0 |
| C4 | node | valid:search_direct_flight | failed | 4 | 0.529 | 0.529 | 0 0 0 4 0 0 |
| C5 | ctx | valid:search_direct_flight | failed | 4 | 0.529 | 0.529 | 0 0 0 4 0 0 |
| C5 | node | valid:search_direct_flight | failed | 4 | 0.529 | 0.529 | 0 0 0 4 0 0 |
| A | ctx | valid:search_direct_flight | success | 9 | 0.5 | 0.5 | 0 0 0 9 0 0 |
| A | node | valid:search_direct_flight | success | 9 | 0.5 | 0.5 | 0 0 0 9 0 0 |
| C0 | ctx | valid:search_direct_flight | success | 9 | 0.389 | 0.5 | 2 0 0 7 0 0 |
| C0 | node | valid:search_direct_flight | success | 9 | 0.5 | 0.5 | 0 0 0 9 0 0 |
| C3 | ctx | valid:search_direct_flight | success | 9 | 0.389 | 0.5 | 2 0 0 7 0 0 |
| C3 | node | valid:search_direct_flight | success | 9 | 0.5 | 0.5 | 0 0 0 9 0 0 |
| C4 | ctx | valid:search_direct_flight | success | 9 | 0.5 | 0.5 | 0 0 0 9 0 0 |
| C4 | node | valid:search_direct_flight | success | 9 | 0.5 | 0.5 | 0 0 0 9 0 0 |
| C5 | ctx | valid:search_direct_flight | success | 9 | 0.5 | 0.5 | 0 0 0 9 0 0 |
| C5 | node | valid:search_direct_flight | success | 9 | 0.5 | 0.5 | 0 0 0 9 0 0 |
| A | ctx | valid | failed | 4 | 0.514 | 0.529 | 0 0 1 3 0 0 |
| A | node | valid | failed | 4 | 0.514 | 0.529 | 0 0 1 3 0 0 |
| C0 | ctx | valid | failed | 4 | 0.397 | 0.529 | 1 0 0 3 0 0 |
| C0 | node | valid | failed | 4 | 0.514 | 0.529 | 0 0 1 3 0 0 |
| C3 | ctx | valid | failed | 4 | 0.397 | 0.529 | 1 0 0 3 0 0 |
| C3 | node | valid | failed | 4 | 0.529 | 0.529 | 0 0 0 4 0 0 |
| C4 | ctx | valid | failed | 4 | 0.529 | 0.529 | 0 0 0 4 0 0 |
| C4 | node | valid | failed | 4 | 0.529 | 0.529 | 0 0 0 4 0 0 |
| C5 | ctx | valid | failed | 4 | 0.529 | 0.529 | 0 0 0 4 0 0 |
| C5 | node | valid | failed | 4 | 0.529 | 0.529 | 0 0 0 4 0 0 |
| A | ctx | valid | success | 23 | 0.802 | 1.0 | 0 0 0 9 1 13 |
| A | node | valid | success | 23 | 0.802 | 1.0 | 0 0 0 9 1 13 |
| C0 | ctx | valid | success | 23 | 0.326 | 0.375 | 3 4 6 10 0 0 |
| C0 | node | valid | success | 23 | 0.372 | 0.5 | 1 4 6 12 0 0 |
| C3 | ctx | valid | success | 23 | 0.723 | 0.938 | 2 0 0 7 14 0 |
| C3 | node | valid | success | 23 | 0.802 | 1.0 | 0 0 0 9 1 13 |
| C4 | ctx | valid | success | 23 | 0.802 | 1.0 | 0 0 0 9 1 13 |
| C4 | node | valid | success | 23 | 0.802 | 1.0 | 0 0 0 9 1 13 |
| C5 | ctx | valid | success | 23 | 0.337 | 0.438 | 3 3 6 11 0 0 |
| C5 | node | valid | success | 23 | 0.337 | 0.438 | 3 3 6 11 0 0 |

Unexpected (valid < 0.5 / incorrect ≥ 0.5): A node: 1, A ctx: 1, C0 node: 12, C0 ctx: 14, C3 node: 0, C3 ctx: 3, C4 node: 0, C4 ctx: 0, C5 node: 12, C5 ctx: 12

### Per-step masks (m_node / m_ctx)

| Run | Succ | Step | Pred | Label | Text | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|
| 1868029f | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 1868029f | True | s2 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.94 | 0.94/0.94 | 0.94/0.94 |
| 1868029f | True | s4 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.69/0.56 | 0.69/0.69 | 0.69/0.69 |
| 1868029f | True | s6 | tool_call | unverified | Call get_user_details with user_id = aarav_ahmed_6699. | 0.31/0.12 | 0.31/0.31 | 0.31/0.31 |
| 1868029f | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.69/0.12 | 0.69/0.69 | 0.69/0.69 |
| 1868029f | True | s10 | tool_call | valid | Call search_direct_flight with date = 2024-05-22; desti | 0.50/0.50 | 0.50/0.50 | 0.50/0.50 |
| 1868029f | True | s12 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.19 | 0.50/0.50 | 0.50/0.50 |
| 1868029f | True | s14 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/0.94 | 1.00/1.00 | 0.50/0.50 |
| 1d04e6f3 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 1d04e6f3 | True | s2 | user_turn | unverified | Sure thing, Aarav! Before we proceed, I'll need a few q | 0.56/0.56 | 0.56/0.56 | 0.56/0.56 |
| 1d04e6f3 | True | s4 | user_turn | unverified | Call get_user_details with user_id = aarav_ahmed_6699. | 0.31/0.06 | 0.25/0.25 | 0.25/0.25 |
| 1d04e6f3 | True | s6 | tool_call | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.06 | 0.88/0.88 | 0.88/0.88 |
| 1d04e6f3 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.69/0.50 | 0.62/0.62 | 0.62/0.62 |
| 1d04e6f3 | True | s10 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.69/0.44 | 0.62/0.62 | 0.62/0.62 |
| 1d04e6f3 | True | s12 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.00 | 0.00/0.00 | 0.00/0.00 |
| 1d04e6f3 | True | s14 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/0.94 | 1.00/1.00 | 0.00/0.00 |
| 2f77c770 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 2f77c770 | True | s2 | user_turn | unverified | Sure thing, Aarav! Before we can cancel or change your  | 0.56/0.56 | 0.56/0.56 | 0.56/0.56 |
| 2f77c770 | True | s4 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.88/0.06 | 0.88/0.88 | 0.88/0.88 |
| 2f77c770 | True | s6 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.12 | 0.19/0.19 | 0.19/0.19 |
| 2f77c770 | True | s8 | tool_call | unverified | I'm sorry, but I'm unable to process those cancellation | 0.94/0.88 | 0.94/0.94 | 0.12/0.12 |
| 39937705 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 39937705 | True | s2 | user_turn | unverified | Sure thing, Aarav! Before we proceed, I'll need a few q | 0.56/0.56 | 0.56/0.56 | 0.56/0.56 |
| 39937705 | True | s4 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.88/0.19 | 0.88/0.88 | 0.88/0.88 |
| 39937705 | True | s6 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.12 | 0.38/0.38 | 0.38/0.38 |
| 39937705 | True | s8 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/0.94 | 1.00/1.00 | 0.38/0.38 |
| 3d7ed3f2 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 3d7ed3f2 | True | s2 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.94 | 0.94/0.94 | 0.94/0.94 |
| 3d7ed3f2 | True | s4 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.69/0.56 | 0.69/0.69 | 0.69/0.69 |
| 3d7ed3f2 | True | s6 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.69/0.50 | 0.69/0.69 | 0.69/0.69 |
| 3d7ed3f2 | True | s8 | tool_call | valid | Call search_direct_flight with date = 2024-05-22; desti | 0.50/0.50 | 0.50/0.50 | 0.50/0.50 |
| 3d7ed3f2 | True | s10 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.00 | 0.00/0.00 | 0.00/0.00 |
| 3d7ed3f2 | True | s12 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/0.94 | 1.00/1.00 | 0.00/0.00 |
| 49f89baf | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 49f89baf | True | s2 | user_turn | unverified | Sure thing, Aarav! Before I can process the cancellatio | 0.56/0.56 | 0.56/0.56 | 0.56/0.56 |
| 49f89baf | True | s4 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.00 | 0.94/0.94 | 0.94/0.94 |
| 49f89baf | True | s6 | tool_call | unverified | Call get_flight_status with date = 2024-05-28; flight_n | 0.12/0.12 | 0.12/0.12 | 0.12/0.12 |
| 49f89baf | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.69/0.06 | 0.69/0.69 | 0.69/0.69 |
| 49f89baf | True | s10 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.69/0.50 | 0.69/0.69 | 0.69/0.69 |
| 49f89baf | True | s12 | tool_call | unverified | Call get_flight_status with date = 2024-05-22; flight_n | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 49f89baf | True | s14 | tool_call | unverified | Call get_flight_status with date = 2024-05-30; flight_n | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 49f89baf | True | s16 | tool_call | valid | Call search_direct_flight with date = 2024-05-22; desti | 0.50/0.00 | 0.50/0.50 | 0.50/0.50 |
| 49f89baf | True | s18 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.19 | 0.25/0.25 | 0.25/0.25 |
| 49f89baf | True | s20 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/0.94 | 1.00/1.00 | 0.25/0.25 |
| 67030d75 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 67030d75 | True | s2 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.94 | 0.94/0.94 | 0.94/0.94 |
| 67030d75 | True | s4 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.69/0.56 | 0.69/0.69 | 0.69/0.69 |
| 67030d75 | True | s6 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.69/0.50 | 0.69/0.69 | 0.69/0.69 |
| 67030d75 | True | s8 | tool_call | valid | Call search_direct_flight with date = 2024-05-22; desti | 0.50/0.50 | 0.50/0.50 | 0.50/0.50 |
| 67030d75 | True | s10 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.06 | 0.06/0.06 | 0.06/0.06 |
| 67030d75 | True | s12 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/0.94 | 1.00/1.00 | 0.06/0.06 |
| 7cd3469e | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 7cd3469e | True | s2 | user_turn | unverified | Call get_user_details with user_id = aarav_ahmed_6699. | 0.31/0.25 | 0.25/0.25 | 0.25/0.25 |
| 7cd3469e | True | s4 | tool_call | unverified | Call get_reservation_details with reservation_id = IFOY | 0.75/0.06 | 0.69/0.69 | 0.69/0.69 |
| 7cd3469e | True | s6 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.69/0.50 | 0.62/0.62 | 0.62/0.62 |
| 7cd3469e | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.69/0.44 | 0.62/0.62 | 0.62/0.62 |
| 7cd3469e | True | s10 | tool_call | unverified | I've checked your reservations: / Reservation / Status  | 0.00/0.00 | 0.06/0.06 | 0.00/0.00 |
| 7cd3469e | True | s12 | user_turn | valid | Call search_direct_flight with date = 2024-05-22; desti | 0.50/0.00 | 0.50/0.50 | 0.50/0.50 |
| 7cd3469e | True | s14 | tool_call | unverified | I've searched for a nonstop flight from JFK to MCO on 2 | 0.94/0.06 | 0.88/0.88 | 0.06/0.06 |
| 882b4bd9 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 882b4bd9 | True | s2 | user_turn | unverified | Sure thing, Aarav! Before I can process the cancellatio | 0.50/0.50 | 0.50/0.50 | 0.50/0.50 |
| 882b4bd9 | True | s4 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.00 | 0.94/0.94 | 0.94/0.94 |
| 882b4bd9 | True | s6 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.69/0.56 | 0.69/0.69 | 0.69/0.69 |
| 882b4bd9 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.69/0.50 | 0.69/0.69 | 0.69/0.69 |
| 882b4bd9 | True | s10 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.00 | 0.31/0.31 | 0.31/0.31 |
| 882b4bd9 | True | s12 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/0.94 | 1.00/1.00 | 0.31/0.31 |
| 8a795aaf | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 8a795aaf | True | s2 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.94 | 0.94/0.94 | 0.94/0.94 |
| 8a795aaf | True | s4 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.69/0.56 | 0.69/0.69 | 0.69/0.69 |
| 8a795aaf | True | s6 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.69/0.50 | 0.69/0.69 | 0.69/0.69 |
| 8a795aaf | True | s8 | tool_call | valid | Call search_direct_flight with date = 2024-05-22; desti | 0.50/0.50 | 0.50/0.50 | 0.50/0.50 |
| 8a795aaf | True | s10 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.19 | 0.44/0.44 | 0.44/0.44 |
| 8a795aaf | True | s12 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/0.94 | 1.00/1.00 | 0.44/0.44 |
| a567caf8 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| a567caf8 | True | s2 | user_turn | unverified | Sure thing, Aarav! Before I can process the cancellatio | 0.56/0.56 | 0.56/0.56 | 0.56/0.56 |
| a567caf8 | True | s4 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.19 | 0.94/0.94 | 0.94/0.94 |
| a567caf8 | True | s6 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.69/0.56 | 0.69/0.69 | 0.69/0.69 |
| a567caf8 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.69/0.50 | 0.69/0.69 | 0.69/0.69 |
| a567caf8 | True | s10 | tool_call | unverified | Call search_direct_flight with date = 2025-06-15; desti | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| a567caf8 | True | s12 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.00 | 0.06/0.06 | 0.06/0.06 |
| a567caf8 | True | s14 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/0.94 | 1.00/1.00 | 0.06/0.06 |
| bb968e44 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| bb968e44 | True | s2 | user_turn | unverified | Sure thing, Aarav! Before I can process the cancellatio | 0.56/0.56 | 0.56/0.56 | 0.56/0.56 |
| bb968e44 | True | s4 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.19 | 0.94/0.94 | 0.94/0.94 |
| bb968e44 | True | s6 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.12 | 0.44/0.44 | 0.44/0.44 |
| bb968e44 | True | s8 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/0.94 | 1.00/1.00 | 0.44/0.44 |
| ce95f0bf | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| ce95f0bf | True | s2 | user_turn | unverified | Sure thing, Aarav! I'll need a few details to make sure | 0.56/0.56 | 0.56/0.56 | 0.56/0.56 |
| ce95f0bf | True | s4 | user_turn | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.00 | 0.00/0.00 | 0.00/0.00 |
| ce95f0bf | True | s6 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/0.94 | 1.00/1.00 | 0.00/0.00 |
| d33894dd | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| d33894dd | True | s2 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.94 | 0.94/0.94 | 0.94/0.94 |
| d33894dd | True | s4 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.69/0.56 | 0.69/0.69 | 0.69/0.69 |
| d33894dd | True | s6 | tool_call | unverified | Call get_user_details with user_id = aarav_ahmed_6699. | 0.31/0.12 | 0.31/0.31 | 0.31/0.31 |
| d33894dd | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.69/0.12 | 0.69/0.69 | 0.69/0.69 |
| d33894dd | True | s10 | tool_call | valid | Call search_direct_flight with date = 2024-05-22; desti | 0.50/0.50 | 0.50/0.50 | 0.50/0.50 |
| d33894dd | True | s12 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.19 | 0.50/0.50 | 0.50/0.50 |
| d33894dd | True | s14 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/0.94 | 1.00/1.00 | 0.50/0.50 |
| d5b7b555 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| d5b7b555 | True | s2 | user_turn | unverified | Sure thing! Before I make any changes, I'll need to dou | 0.50/0.50 | 0.50/0.50 | 0.50/0.50 |
| d5b7b555 | True | s4 | user_turn | unverified | Call get_user_details with user_id = aarav_ahmed_6699. | 0.31/0.06 | 0.31/0.31 | 0.31/0.31 |
| d5b7b555 | True | s6 | tool_call | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.12 | 0.94/0.94 | 0.94/0.94 |
| d5b7b555 | True | s8 | tool_call | unverified | Call get_flight_status with date = 2024-05-28; flight_n | 0.12/0.12 | 0.12/0.12 | 0.12/0.12 |
| d5b7b555 | True | s10 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.69/0.06 | 0.69/0.69 | 0.69/0.69 |
| d5b7b555 | True | s12 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.69/0.50 | 0.69/0.69 | 0.69/0.69 |
| d5b7b555 | True | s14 | tool_call | valid | Call search_direct_flight with date = 2024-05-22; desti | 0.50/0.50 | 0.50/0.50 | 0.50/0.50 |
| d5b7b555 | True | s16 | tool_call | unverified | I've checked the details for your reservations: / Reser | 0.06/0.06 | 0.06/0.06 | 0.06/0.06 |
| d5b7b555 | True | s18 | user_turn | unverified | Call search_direct_flight with date = 2024-05-23; desti | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| d5b7b555 | True | s20 | tool_call | unverified | Call transfer_to_human_agents with summary = User reque | 0.94/0.00 | 0.25/0.25 | 0.25/0.25 |
| d5b7b555 | True | s22 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 0.94/0.94 | 0.94/0.94 | 0.25/0.25 |
| ed3e4cc7 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| ed3e4cc7 | True | s2 | user_turn | unverified | Sure thing, Aarav! Before we proceed, I'll need a few q | 0.56/0.56 | 0.56/0.56 | 0.56/0.56 |
| ed3e4cc7 | True | s4 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.88/0.25 | 0.88/0.88 | 0.88/0.88 |
| ed3e4cc7 | True | s6 | tool_call | unverified | Call get_flight_status with date = 2024-05-28; flight_n | 0.12/0.12 | 0.12/0.12 | 0.12/0.12 |
| ed3e4cc7 | True | s8 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.00 | 0.31/0.31 | 0.31/0.31 |
| ed3e4cc7 | True | s10 | tool_call | unverified | I'm sorry, but I'm unable to process the cancellations  | 0.88/0.88 | 0.88/0.88 | 0.25/0.25 |
| ed3e4cc7 | True | s12 | user_turn | unverified | You're welcome! I've forwarded your request to a human  | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| ed3e4cc7 | True | s14 | user_turn | unverified | You're very welcome! If anything else comes up, just le | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| f2974012 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| f2974012 | True | s2 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.94 | 0.94/0.94 | 0.94/0.94 |
| f2974012 | True | s4 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.69/0.56 | 0.69/0.69 | 0.69/0.69 |
| f2974012 | True | s6 | tool_call | unverified | Call get_user_details with user_id = aarav_ahmed_6699. | 0.31/0.12 | 0.31/0.31 | 0.31/0.31 |
| f2974012 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.69/0.12 | 0.69/0.69 | 0.69/0.69 |
| f2974012 | True | s10 | tool_call | valid | Call search_direct_flight with date = 2024-05-22; desti | 0.50/0.50 | 0.50/0.50 | 0.50/0.50 |
| f2974012 | True | s12 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.94/0.06 | 0.06/0.06 | 0.06/0.06 |
| f2974012 | True | s14 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 1.00/0.94 | 1.00/1.00 | 0.06/0.06 |
| 68290327 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 68290327 | False | s2 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.94 | 0.94/0.94 | 0.94/0.94 |
| 68290327 | False | s4 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.71/0.59 | 0.71/0.71 | 0.71/0.71 |
| 68290327 | False | s6 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.71/0.53 | 0.71/0.71 | 0.71/0.71 |
| 68290327 | False | s8 | tool_call | valid | Call search_direct_flight with date = 2024-05-22; desti | 0.53/0.53 | 0.53/0.53 | 0.53/0.53 |
| 68290327 | False | s10 | tool_call | unverified | I can cancel your reservation NQNU5R for you. I'm not a | 0.06/0.06 | 0.06/0.06 | 0.06/0.06 |
| 68290327 | False | s12 | user_turn | incorrect | Call cancel_reservation with reservation_id = NQNU5R. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 68290327 | False | s14 | tool_call | unverified | Your reservation NQNU5R has been successfully cancelled | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 71270d8b | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 71270d8b | False | s2 | user_turn | unverified | Sure thing, Aarav! Before we proceed, I'll need a few q | 0.59/0.59 | 0.59/0.59 | 0.59/0.59 |
| 71270d8b | False | s4 | user_turn | unverified | I've pulled up the details for the three reservations y | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 71270d8b | False | s6 | user_turn | unverified | Call get_reservation_details with reservation_id = M20I | 0.71/0.00 | 0.71/0.65 | 0.71/0.65 |
| 71270d8b | False | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = IFOY | 0.88/0.00 | 0.88/0.88 | 0.88/0.88 |
| 71270d8b | False | s10 | tool_call | valid | Call search_direct_flight with date = 2024-05-22; desti | 0.53/0.00 | 0.53/0.53 | 0.53/0.53 |
| 71270d8b | False | s12 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.65/0.00 | 0.65/0.65 | 0.65/0.65 |
| 71270d8b | False | s14 | tool_call | incorrect | Call cancel_reservation with reservation_id = IFOYYZ. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 71270d8b | False | s16 | tool_call | incorrect | Call cancel_reservation with reservation_id = NQNU5R. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 71270d8b | False | s18 | tool_call | unverified | I've completed the cancellations for IFOYYZ and NQNU5R  | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 71270d8b | False | s20 | user_turn | unverified | Call search_direct_flight with date = 2024-05-23; desti | 0.06/0.00 | 0.06/0.06 | 0.06/0.06 |
| 71270d8b | False | s22 | tool_call | unverified | Call search_direct_flight with date = 2024-05-24; desti | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 71270d8b | False | s24 | tool_call | unverified | Call search_onestop_flight with date = 2024-05-23; dest | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 71270d8b | False | s26 | tool_call | unverified | Call search_onestop_flight with date = 2024-05-24; dest | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 71270d8b | False | s28 | tool_call | unverified | Here's what I found for a nonstop or short-layover flig | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 71270d8b | False | s30 | user_turn | incorrect | Call update_reservation_flights with cabin = economy; f | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 71270d8b | False | s32 | tool_call | unverified | All set! Your reservation M20IZO has been updated to th | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 71270d8b | False | s34 | user_turn | unverified | You're very welcome, Aarav! I'm glad everything's sorte | 0.00/0.00 | 0.06/0.06 | 0.00/0.00 |
| 7a9248ed | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 7a9248ed | False | s2 | user_turn | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.94 | 0.94/0.94 | 0.94/0.94 |
| 7a9248ed | False | s4 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.71/0.59 | 0.71/0.71 | 0.71/0.71 |
| 7a9248ed | False | s6 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.71/0.53 | 0.71/0.71 | 0.71/0.71 |
| 7a9248ed | False | s8 | tool_call | valid | Call search_direct_flight with date = 2024-05-22; desti | 0.53/0.53 | 0.53/0.53 | 0.53/0.53 |
| 7a9248ed | False | s10 | tool_call | unverified | Call get_user_details with user_id = aarav_ahmed_6699. | 0.35/0.00 | 0.35/0.35 | 0.35/0.35 |
| 7a9248ed | False | s12 | tool_call | incorrect | Call cancel_reservation with reservation_id = NQNU5R. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 7a9248ed | False | s14 | tool_call | incorrect | Call cancel_reservation with reservation_id = IFOYYZ. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 7a9248ed | False | s16 | tool_call | unverified | I've processed the cancellations for reservations IFOYY | 0.00/0.00 | 0.06/0.06 | 0.00/0.00 |
| 7a9248ed | False | s18 | user_turn | unverified | Call search_direct_flight with date = 2024-05-23; desti | 0.06/0.00 | 0.06/0.06 | 0.06/0.06 |
| 7a9248ed | False | s20 | tool_call | unverified | Call search_direct_flight with date = 2024-05-24; desti | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 7a9248ed | False | s22 | tool_call | unverified | Call search_onestop_flight with date = 2024-05-23; dest | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 7a9248ed | False | s24 | tool_call | unverified | I've checked the flight options for 2024-05-23 and 2024 | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 7a9248ed | False | s26 | user_turn | incorrect | Call update_reservation_flights with cabin = business;  | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 7a9248ed | False | s28 | tool_call | unverified | ✅ Your reservation M20IZO has been updated to the 2½-ho | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 7a9248ed | False | s30 | user_turn | unverified | You're very welcome! I'm glad everything's sorted out.  | 0.00/0.00 | 0.06/0.06 | 0.00/0.00 |
| 7e3e8b73 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 7e3e8b73 | False | s2 | user_turn | unverified | Call get_user_details with user_id = aarav_ahmed_6699. | 0.35/0.35 | 0.35/0.35 | 0.35/0.35 |
| 7e3e8b73 | False | s4 | tool_call | unverified | Call get_reservation_details with reservation_id = IFOY | 0.94/0.18 | 0.94/0.94 | 0.94/0.94 |
| 7e3e8b73 | False | s6 | tool_call | unverified | Call get_reservation_details with reservation_id = NQNU | 0.71/0.59 | 0.71/0.71 | 0.71/0.71 |
| 7e3e8b73 | False | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = M20I | 0.71/0.53 | 0.71/0.71 | 0.71/0.71 |
| 7e3e8b73 | False | s10 | tool_call | valid | Call search_direct_flight with date = 2024-05-22; desti | 0.53/0.53 | 0.53/0.53 | 0.53/0.53 |
| 7e3e8b73 | False | s12 | tool_call | unverified | Call get_flight_status with date = 2024-05-28; flight_n | 0.18/0.00 | 0.18/0.18 | 0.18/0.18 |
| 7e3e8b73 | False | s14 | tool_call | unverified | Next Steps 1. Cancel Reservation IFOYYZ - I can proceed | 0.06/0.00 | 0.06/0.06 | 0.00/0.00 |
| 7e3e8b73 | False | s16 | user_turn | incorrect | Call cancel_reservation with reservation_id = IFOYYZ. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 7e3e8b73 | False | s18 | tool_call | unverified | Call transfer_to_human_agents with summary = User wants | 0.82/0.00 | 0.00/0.00 | 0.00/0.00 |
| 7e3e8b73 | False | s20 | tool_call | unverified | Your reservation IFOYYZ has been cancelled. I'm transfe | 0.82/0.82 | 0.82/0.82 | 0.00/0.00 |

## Task 25

C5 cost: {'seconds': 9.3, 'nli_forward_passes_uncached': 0, 'nli_directional_pairs_requested': 58506, 'n_mcs_runs': 399}; stage-2 counters: {'candidates_message_edges': 971, 'dropped_tool_unmatched': 1, 'dropped_tool_conflict': 1}

Message coverage (indicator counts): {"C3": {"node": 1149, "ctx": 969, "node_only": 180, "indicators": 2256}, "C4": {"node": 1220, "ctx": 1220, "node_only": 0, "indicators": 2256}, "C5": {"node": 969, "ctx": 969, "node_only": 0, "indicators": 2256}}

C5 − C4 on message steps: {"node|same|unverified": 63, "ctx|same|unverified": 63, "node|down|unverified": 59, "ctx|down|unverified": 59, "node|up|unverified": 1, "ctx|up|unverified": 1, "node|same|valid": 1, "ctx|same|valid": 1}

| Variant | Target | Group | Runs | n | mean | median | bins 0 / (0,.25) / [.25,.5) / [.5,.75) / [.75,1) / 1 |
|---|---|---|---|---|---|---|---|
| A | ctx | incorrect:book_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | node | incorrect:book_reservation | failed | 1 | 0.947 | 0.947 | 0 0 0 0 1 0 |
| C0 | ctx | incorrect:book_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | node | incorrect:book_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | ctx | incorrect:book_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | node | incorrect:book_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | ctx | incorrect:book_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | node | incorrect:book_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | ctx | incorrect:book_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | node | incorrect:book_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | ctx | incorrect:cancel_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | node | incorrect:cancel_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | ctx | incorrect:cancel_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | node | incorrect:cancel_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | ctx | incorrect:cancel_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | node | incorrect:cancel_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | ctx | incorrect:cancel_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | node | incorrect:cancel_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | ctx | incorrect:cancel_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | node | incorrect:cancel_reservation | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | ctx | incorrect | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| A | node | incorrect | failed | 2 | 0.473 | 0.473 | 1 0 0 0 1 0 |
| C0 | ctx | incorrect | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C0 | node | incorrect | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C3 | ctx | incorrect | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C3 | node | incorrect | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C4 | ctx | incorrect | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C4 | node | incorrect | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C5 | ctx | incorrect | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C5 | node | incorrect | failed | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| A | ctx | message|pred=none | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| A | node | message|pred=none | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| C0 | ctx | message|pred=none | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| C0 | node | message|pred=none | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| C3 | ctx | message|pred=none | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| C3 | node | message|pred=none | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| C4 | ctx | message|pred=none | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| C4 | node | message|pred=none | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| C5 | ctx | message|pred=none | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| C5 | node | message|pred=none | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| A | ctx | message|pred=none | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| A | node | message|pred=none | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C0 | ctx | message|pred=none | success | 19 | 0.86 | 0.833 | 0 0 0 3 8 8 |
| C0 | node | message|pred=none | success | 19 | 0.86 | 0.833 | 0 0 0 3 8 8 |
| C3 | ctx | message|pred=none | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C3 | node | message|pred=none | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C4 | ctx | message|pred=none | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C4 | node | message|pred=none | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C5 | ctx | message|pred=none | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C5 | node | message|pred=none | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| A | ctx | message|pred=tool_call | failed | 14 | 0.327 | 0.21 | 5 2 3 1 3 0 |
| A | node | message|pred=tool_call | failed | 14 | 0.327 | 0.21 | 5 2 3 1 3 0 |
| C0 | ctx | message|pred=tool_call | failed | 14 | 0.173 | 0.0 | 9 1 2 2 0 0 |
| C0 | node | message|pred=tool_call | failed | 14 | 0.196 | 0.0 | 9 1 2 0 2 0 |
| C3 | ctx | message|pred=tool_call | failed | 14 | 0.169 | 0.0 | 9 1 2 2 0 0 |
| C3 | node | message|pred=tool_call | failed | 14 | 0.244 | 0.132 | 6 2 4 0 2 0 |
| C4 | ctx | message|pred=tool_call | failed | 14 | 0.304 | 0.184 | 5 2 3 1 3 0 |
| C4 | node | message|pred=tool_call | failed | 14 | 0.304 | 0.184 | 5 2 3 1 3 0 |
| C5 | ctx | message|pred=tool_call | failed | 14 | 0.169 | 0.0 | 9 1 2 2 0 0 |
| C5 | node | message|pred=tool_call | failed | 14 | 0.169 | 0.0 | 9 1 2 2 0 0 |
| A | ctx | message|pred=tool_call | success | 66 | 0.599 | 0.667 | 1 9 7 21 26 2 |
| A | node | message|pred=tool_call | success | 66 | 0.599 | 0.667 | 1 9 7 21 26 2 |
| C0 | ctx | message|pred=tool_call | success | 66 | 0.44 | 0.556 | 15 5 7 28 11 0 |
| C0 | node | message|pred=tool_call | success | 66 | 0.52 | 0.556 | 9 6 9 18 24 0 |
| C3 | ctx | message|pred=tool_call | success | 66 | 0.44 | 0.556 | 15 5 7 28 11 0 |
| C3 | node | message|pred=tool_call | success | 66 | 0.546 | 0.611 | 5 7 11 19 24 0 |
| C4 | ctx | message|pred=tool_call | success | 66 | 0.57 | 0.611 | 2 9 8 22 24 1 |
| C4 | node | message|pred=tool_call | success | 66 | 0.57 | 0.611 | 2 9 8 22 24 1 |
| C5 | ctx | message|pred=tool_call | success | 66 | 0.44 | 0.556 | 15 5 7 28 11 0 |
| C5 | node | message|pred=tool_call | success | 66 | 0.44 | 0.556 | 15 5 7 28 11 0 |
| A | ctx | message|pred=user_turn | failed | 7 | 0.038 | 0.0 | 6 0 1 0 0 0 |
| A | node | message|pred=user_turn | failed | 7 | 0.038 | 0.0 | 6 0 1 0 0 0 |
| C0 | ctx | message|pred=user_turn | failed | 7 | 0.008 | 0.0 | 6 1 0 0 0 0 |
| C0 | node | message|pred=user_turn | failed | 7 | 0.008 | 0.0 | 6 1 0 0 0 0 |
| C3 | ctx | message|pred=user_turn | failed | 7 | 0.008 | 0.0 | 6 1 0 0 0 0 |
| C3 | node | message|pred=user_turn | failed | 7 | 0.008 | 0.0 | 6 1 0 0 0 0 |
| C4 | ctx | message|pred=user_turn | failed | 7 | 0.008 | 0.0 | 6 1 0 0 0 0 |
| C4 | node | message|pred=user_turn | failed | 7 | 0.008 | 0.0 | 6 1 0 0 0 0 |
| C5 | ctx | message|pred=user_turn | failed | 7 | 0.008 | 0.0 | 6 1 0 0 0 0 |
| C5 | node | message|pred=user_turn | failed | 7 | 0.008 | 0.0 | 6 1 0 0 0 0 |
| A | ctx | message|pred=user_turn | success | 15 | 0.237 | 0.111 | 5 6 0 3 1 0 |
| A | node | message|pred=user_turn | success | 15 | 0.237 | 0.111 | 5 6 0 3 1 0 |
| C0 | ctx | message|pred=user_turn | success | 15 | 0.007 | 0.0 | 13 2 0 0 0 0 |
| C0 | node | message|pred=user_turn | success | 15 | 0.082 | 0.0 | 9 5 0 0 1 0 |
| C3 | ctx | message|pred=user_turn | success | 15 | 0.007 | 0.0 | 13 2 0 0 0 0 |
| C3 | node | message|pred=user_turn | success | 15 | 0.13 | 0.056 | 7 6 1 0 1 0 |
| C4 | ctx | message|pred=user_turn | success | 15 | 0.23 | 0.056 | 6 5 0 3 1 0 |
| C4 | node | message|pred=user_turn | success | 15 | 0.23 | 0.056 | 6 5 0 3 1 0 |
| C5 | ctx | message|pred=user_turn | success | 15 | 0.007 | 0.0 | 13 2 0 0 0 0 |
| C5 | node | message|pred=user_turn | success | 15 | 0.007 | 0.0 | 13 2 0 0 0 0 |
| A | ctx | unverified:book_reservation | failed | 8 | 0.579 | 0.526 | 0 1 2 2 3 0 |
| A | node | unverified:book_reservation | failed | 8 | 0.579 | 0.526 | 0 1 2 2 3 0 |
| C0 | ctx | unverified:book_reservation | failed | 8 | 0.165 | 0.132 | 1 4 3 0 0 0 |
| C0 | node | unverified:book_reservation | failed | 8 | 0.5 | 0.342 | 0 2 3 0 3 0 |
| C3 | ctx | unverified:book_reservation | failed | 8 | 0.165 | 0.132 | 1 4 3 0 0 0 |
| C3 | node | unverified:book_reservation | failed | 8 | 0.5 | 0.342 | 0 2 3 0 3 0 |
| C4 | ctx | unverified:book_reservation | failed | 8 | 0.5 | 0.342 | 0 2 3 0 3 0 |
| C4 | node | unverified:book_reservation | failed | 8 | 0.5 | 0.342 | 0 2 3 0 3 0 |
| C5 | ctx | unverified:book_reservation | failed | 8 | 0.5 | 0.342 | 0 2 3 0 3 0 |
| C5 | node | unverified:book_reservation | failed | 8 | 0.5 | 0.342 | 0 2 3 0 3 0 |
| A | ctx | unverified:book_reservation | success | 39 | 0.499 | 0.5 | 5 5 9 5 15 0 |
| A | node | unverified:book_reservation | success | 39 | 0.61 | 0.5 | 3 2 6 10 18 0 |
| C0 | ctx | unverified:book_reservation | success | 39 | 0.151 | 0.167 | 8 22 9 0 0 0 |
| C0 | node | unverified:book_reservation | success | 39 | 0.544 | 0.333 | 4 4 13 0 18 0 |
| C3 | ctx | unverified:book_reservation | success | 39 | 0.15 | 0.167 | 9 21 9 0 0 0 |
| C3 | node | unverified:book_reservation | success | 39 | 0.544 | 0.333 | 4 4 13 0 18 0 |
| C4 | ctx | unverified:book_reservation | success | 39 | 0.45 | 0.333 | 6 8 7 3 15 0 |
| C4 | node | unverified:book_reservation | success | 39 | 0.544 | 0.333 | 4 4 13 0 18 0 |
| C5 | ctx | unverified:book_reservation | success | 39 | 0.45 | 0.333 | 6 8 7 3 15 0 |
| C5 | node | unverified:book_reservation | success | 39 | 0.544 | 0.333 | 4 4 13 0 18 0 |
| A | ctx | unverified:get_flight_status | failed | 4 | 0.026 | 0.026 | 2 2 0 0 0 0 |
| A | node | unverified:get_flight_status | failed | 4 | 0.026 | 0.026 | 2 2 0 0 0 0 |
| C0 | ctx | unverified:get_flight_status | failed | 4 | 0.013 | 0.0 | 3 1 0 0 0 0 |
| C0 | node | unverified:get_flight_status | failed | 4 | 0.026 | 0.026 | 2 2 0 0 0 0 |
| C3 | ctx | unverified:get_flight_status | failed | 4 | 0.013 | 0.0 | 3 1 0 0 0 0 |
| C3 | node | unverified:get_flight_status | failed | 4 | 0.026 | 0.026 | 2 2 0 0 0 0 |
| C4 | ctx | unverified:get_flight_status | failed | 4 | 0.026 | 0.026 | 2 2 0 0 0 0 |
| C4 | node | unverified:get_flight_status | failed | 4 | 0.026 | 0.026 | 2 2 0 0 0 0 |
| C5 | ctx | unverified:get_flight_status | failed | 4 | 0.026 | 0.026 | 2 2 0 0 0 0 |
| C5 | node | unverified:get_flight_status | failed | 4 | 0.026 | 0.026 | 2 2 0 0 0 0 |
| A | ctx | unverified:get_flight_status | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| A | node | unverified:get_flight_status | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C0 | ctx | unverified:get_flight_status | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C0 | node | unverified:get_flight_status | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C3 | ctx | unverified:get_flight_status | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C3 | node | unverified:get_flight_status | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C4 | ctx | unverified:get_flight_status | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C4 | node | unverified:get_flight_status | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C5 | ctx | unverified:get_flight_status | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| C5 | node | unverified:get_flight_status | success | 2 | 0.0 | 0.0 | 2 0 0 0 0 0 |
| A | ctx | unverified:get_reservation_details | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| A | node | unverified:get_reservation_details | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| C0 | ctx | unverified:get_reservation_details | failed | 3 | 0.982 | 1.0 | 0 0 0 0 1 2 |
| C0 | node | unverified:get_reservation_details | failed | 3 | 0.982 | 1.0 | 0 0 0 0 1 2 |
| C3 | ctx | unverified:get_reservation_details | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| C3 | node | unverified:get_reservation_details | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| C4 | ctx | unverified:get_reservation_details | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| C4 | node | unverified:get_reservation_details | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| C5 | ctx | unverified:get_reservation_details | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| C5 | node | unverified:get_reservation_details | failed | 3 | 1.0 | 1.0 | 0 0 0 0 0 3 |
| A | ctx | unverified:get_reservation_details | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| A | node | unverified:get_reservation_details | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C0 | ctx | unverified:get_reservation_details | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C0 | node | unverified:get_reservation_details | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C3 | ctx | unverified:get_reservation_details | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C3 | node | unverified:get_reservation_details | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C4 | ctx | unverified:get_reservation_details | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C4 | node | unverified:get_reservation_details | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C5 | ctx | unverified:get_reservation_details | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C5 | node | unverified:get_reservation_details | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| A | ctx | unverified:get_user_details | failed | 5 | 0.874 | 1.0 | 0 0 0 2 0 3 |
| A | node | unverified:get_user_details | failed | 5 | 0.874 | 1.0 | 0 0 0 2 0 3 |
| C0 | ctx | unverified:get_user_details | failed | 5 | 0.863 | 0.947 | 0 0 0 2 1 2 |
| C0 | node | unverified:get_user_details | failed | 5 | 0.863 | 0.947 | 0 0 0 2 1 2 |
| C3 | ctx | unverified:get_user_details | failed | 5 | 0.874 | 1.0 | 0 0 0 2 0 3 |
| C3 | node | unverified:get_user_details | failed | 5 | 0.874 | 1.0 | 0 0 0 2 0 3 |
| C4 | ctx | unverified:get_user_details | failed | 5 | 0.874 | 1.0 | 0 0 0 2 0 3 |
| C4 | node | unverified:get_user_details | failed | 5 | 0.874 | 1.0 | 0 0 0 2 0 3 |
| C5 | ctx | unverified:get_user_details | failed | 5 | 0.874 | 1.0 | 0 0 0 2 0 3 |
| C5 | node | unverified:get_user_details | failed | 5 | 0.874 | 1.0 | 0 0 0 2 0 3 |
| A | ctx | unverified:get_user_details | success | 38 | 0.734 | 0.805 | 0 6 0 13 2 17 |
| A | node | unverified:get_user_details | success | 38 | 0.737 | 0.834 | 0 6 0 13 0 19 |
| C0 | ctx | unverified:get_user_details | success | 38 | 0.643 | 0.667 | 3 4 3 10 2 16 |
| C0 | node | unverified:get_user_details | success | 38 | 0.737 | 0.834 | 0 6 0 13 0 19 |
| C3 | ctx | unverified:get_user_details | success | 38 | 0.643 | 0.667 | 3 4 3 10 2 16 |
| C3 | node | unverified:get_user_details | success | 38 | 0.737 | 0.834 | 0 6 0 13 0 19 |
| C4 | ctx | unverified:get_user_details | success | 38 | 0.734 | 0.805 | 0 6 0 13 2 17 |
| C4 | node | unverified:get_user_details | success | 38 | 0.737 | 0.834 | 0 6 0 13 0 19 |
| C5 | ctx | unverified:get_user_details | success | 38 | 0.734 | 0.805 | 0 6 0 13 2 17 |
| C5 | node | unverified:get_user_details | success | 38 | 0.737 | 0.834 | 0 6 0 13 0 19 |
| A | ctx | unverified:message | failed | 23 | 0.341 | 0.053 | 10 2 4 1 3 3 |
| A | node | unverified:message | failed | 23 | 0.341 | 0.053 | 10 2 4 1 3 3 |
| C0 | ctx | unverified:message | failed | 23 | 0.238 | 0.0 | 14 2 2 2 0 3 |
| C0 | node | unverified:message | failed | 23 | 0.252 | 0.0 | 14 2 2 0 2 3 |
| C3 | ctx | unverified:message | failed | 23 | 0.236 | 0.0 | 14 2 2 2 0 3 |
| C3 | node | unverified:message | failed | 23 | 0.282 | 0.053 | 11 3 4 0 2 3 |
| C4 | ctx | unverified:message | failed | 23 | 0.318 | 0.053 | 10 3 3 1 3 3 |
| C4 | node | unverified:message | failed | 23 | 0.318 | 0.053 | 10 3 3 1 3 3 |
| C5 | ctx | unverified:message | failed | 23 | 0.236 | 0.0 | 14 2 2 2 0 3 |
| C5 | node | unverified:message | failed | 23 | 0.236 | 0.0 | 14 2 2 2 0 3 |
| A | ctx | unverified:message | success | 100 | 0.621 | 0.667 | 6 15 7 24 27 21 |
| A | node | unverified:message | success | 100 | 0.621 | 0.667 | 6 15 7 24 27 21 |
| C0 | ctx | unverified:message | success | 100 | 0.455 | 0.556 | 28 7 7 31 19 8 |
| C0 | node | unverified:message | success | 100 | 0.519 | 0.556 | 18 11 9 21 33 8 |
| C3 | ctx | unverified:message | success | 100 | 0.481 | 0.556 | 28 7 7 28 11 19 |
| C3 | node | unverified:message | success | 100 | 0.57 | 0.611 | 12 13 12 19 25 19 |
| C4 | ctx | unverified:message | success | 100 | 0.601 | 0.639 | 8 14 8 25 25 20 |
| C4 | node | unverified:message | success | 100 | 0.601 | 0.639 | 8 14 8 25 25 20 |
| C5 | ctx | unverified:message | success | 100 | 0.481 | 0.556 | 28 7 7 28 11 19 |
| C5 | node | unverified:message | success | 100 | 0.481 | 0.556 | 28 7 7 28 11 19 |
| A | ctx | unverified:search_direct_flight | failed | 4 | 0.04 | 0.0 | 3 1 0 0 0 0 |
| A | node | unverified:search_direct_flight | failed | 4 | 0.04 | 0.0 | 3 1 0 0 0 0 |
| C0 | ctx | unverified:search_direct_flight | failed | 4 | 0.013 | 0.0 | 3 1 0 0 0 0 |
| C0 | node | unverified:search_direct_flight | failed | 4 | 0.04 | 0.0 | 3 1 0 0 0 0 |
| C3 | ctx | unverified:search_direct_flight | failed | 4 | 0.053 | 0.026 | 2 2 0 0 0 0 |
| C3 | node | unverified:search_direct_flight | failed | 4 | 0.079 | 0.079 | 2 2 0 0 0 0 |
| C4 | ctx | unverified:search_direct_flight | failed | 4 | 0.079 | 0.079 | 2 2 0 0 0 0 |
| C4 | node | unverified:search_direct_flight | failed | 4 | 0.079 | 0.079 | 2 2 0 0 0 0 |
| C5 | ctx | unverified:search_direct_flight | failed | 4 | 0.079 | 0.079 | 2 2 0 0 0 0 |
| C5 | node | unverified:search_direct_flight | failed | 4 | 0.079 | 0.079 | 2 2 0 0 0 0 |
| A | ctx | unverified:search_direct_flight | success | 8 | 0.056 | 0.056 | 3 5 0 0 0 0 |
| A | node | unverified:search_direct_flight | success | 8 | 0.056 | 0.056 | 3 5 0 0 0 0 |
| C0 | ctx | unverified:search_direct_flight | success | 8 | 0.028 | 0.028 | 4 4 0 0 0 0 |
| C0 | node | unverified:search_direct_flight | success | 8 | 0.056 | 0.056 | 3 5 0 0 0 0 |
| C3 | ctx | unverified:search_direct_flight | success | 8 | 0.07 | 0.056 | 1 7 0 0 0 0 |
| C3 | node | unverified:search_direct_flight | success | 8 | 0.097 | 0.111 | 0 8 0 0 0 0 |
| C4 | ctx | unverified:search_direct_flight | success | 8 | 0.097 | 0.111 | 0 8 0 0 0 0 |
| C4 | node | unverified:search_direct_flight | success | 8 | 0.097 | 0.111 | 0 8 0 0 0 0 |
| C5 | ctx | unverified:search_direct_flight | success | 8 | 0.097 | 0.111 | 0 8 0 0 0 0 |
| C5 | node | unverified:search_direct_flight | success | 8 | 0.097 | 0.111 | 0 8 0 0 0 0 |
| A | ctx | unverified:search_onestop_flight | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | node | unverified:search_onestop_flight | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | ctx | unverified:search_onestop_flight | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | node | unverified:search_onestop_flight | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | ctx | unverified:search_onestop_flight | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | node | unverified:search_onestop_flight | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | ctx | unverified:search_onestop_flight | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | node | unverified:search_onestop_flight | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | ctx | unverified:search_onestop_flight | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | node | unverified:search_onestop_flight | success | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | ctx | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | node | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | ctx | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | node | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | ctx | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | node | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | ctx | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | node | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | ctx | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | node | unverified:transfer_to_human_agents | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | ctx | unverified | failed | 48 | 0.419 | 0.316 | 16 6 6 5 6 9 |
| A | node | unverified | failed | 48 | 0.419 | 0.316 | 16 6 6 5 6 9 |
| C0 | ctx | unverified | failed | 48 | 0.295 | 0.053 | 22 8 5 4 2 7 |
| C0 | node | unverified | failed | 48 | 0.361 | 0.105 | 20 7 5 2 7 7 |
| C3 | ctx | unverified | failed | 48 | 0.299 | 0.053 | 21 9 5 4 0 9 |
| C3 | node | unverified | failed | 48 | 0.381 | 0.184 | 16 9 7 2 5 9 |
| C4 | ctx | unverified | failed | 48 | 0.398 | 0.237 | 15 9 6 3 6 9 |
| C4 | node | unverified | failed | 48 | 0.398 | 0.237 | 15 9 6 3 6 9 |
| C5 | ctx | unverified | failed | 48 | 0.359 | 0.132 | 19 8 5 4 3 9 |
| C5 | node | unverified | failed | 48 | 0.359 | 0.132 | 19 8 5 4 3 9 |
| A | ctx | unverified | success | 207 | 0.623 | 0.667 | 17 31 16 42 44 57 |
| A | node | unverified | success | 207 | 0.644 | 0.778 | 15 28 13 47 45 59 |
| C0 | ctx | unverified | success | 207 | 0.459 | 0.5 | 46 37 19 41 21 43 |
| C0 | node | unverified | success | 207 | 0.582 | 0.667 | 28 26 22 34 51 46 |
| C3 | ctx | unverified | success | 207 | 0.473 | 0.5 | 44 39 19 38 13 54 |
| C3 | node | unverified | success | 207 | 0.609 | 0.667 | 19 31 25 32 43 57 |
| C4 | ctx | unverified | success | 207 | 0.605 | 0.667 | 17 36 15 41 42 56 |
| C4 | node | unverified | success | 207 | 0.623 | 0.667 | 15 32 21 38 43 58 |
| C5 | ctx | unverified | success | 207 | 0.548 | 0.611 | 37 29 14 44 28 55 |
| C5 | node | unverified | success | 207 | 0.566 | 0.667 | 35 25 20 41 29 57 |
| A | ctx | valid:book_reservation | success | 19 | 0.854 | 0.833 | 0 0 0 3 10 6 |
| A | node | valid:book_reservation | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C0 | ctx | valid:book_reservation | success | 19 | 0.269 | 0.278 | 3 6 7 3 0 0 |
| C0 | node | valid:book_reservation | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C3 | ctx | valid:book_reservation | success | 19 | 0.269 | 0.278 | 3 6 7 3 0 0 |
| C3 | node | valid:book_reservation | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C4 | ctx | valid:book_reservation | success | 19 | 0.854 | 0.833 | 0 0 0 3 10 6 |
| C4 | node | valid:book_reservation | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C5 | ctx | valid:book_reservation | success | 19 | 0.854 | 0.833 | 0 0 0 3 10 6 |
| C5 | node | valid:book_reservation | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| A | ctx | valid:message | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | node | valid:message | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | ctx | valid:message | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | node | valid:message | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | ctx | valid:message | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | node | valid:message | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | ctx | valid:message | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | node | valid:message | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | ctx | valid:message | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | node | valid:message | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | ctx | valid | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | node | valid | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | ctx | valid | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C0 | node | valid | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | ctx | valid | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C3 | node | valid | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | ctx | valid | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C4 | node | valid | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | ctx | valid | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| C5 | node | valid | failed | 1 | 0.0 | 0.0 | 1 0 0 0 0 0 |
| A | ctx | valid | success | 19 | 0.854 | 0.833 | 0 0 0 3 10 6 |
| A | node | valid | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C0 | ctx | valid | success | 19 | 0.269 | 0.278 | 3 6 7 3 0 0 |
| C0 | node | valid | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C3 | ctx | valid | success | 19 | 0.269 | 0.278 | 3 6 7 3 0 0 |
| C3 | node | valid | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C4 | ctx | valid | success | 19 | 0.854 | 0.833 | 0 0 0 3 10 6 |
| C4 | node | valid | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |
| C5 | ctx | valid | success | 19 | 0.854 | 0.833 | 0 0 0 3 10 6 |
| C5 | node | valid | success | 19 | 1.0 | 1.0 | 0 0 0 0 0 19 |

Unexpected (valid < 0.5 / incorrect ≥ 0.5): A node: 2, A ctx: 1, C0 node: 1, C0 ctx: 17, C3 node: 1, C3 ctx: 17, C4 node: 1, C4 ctx: 1, C5 node: 1, C5 ctx: 1

### Per-step masks (m_node / m_ctx)

| Run | Succ | Step | Pred | Label | Text | C3 | C4 | C5 |
|---|---|---|---|---|---|---|---|---|
| 0f0f7358 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 0f0f7358 | True | s2 | user_turn | unverified | Call get_user_details with user_id = user123. | 0.06/0.06 | 0.06/0.06 | 0.06/0.06 |
| 0f0f7358 | True | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.61/0.00 | 0.61/0.61 | 0.00/0.00 |
| 0f0f7358 | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 0f0f7358 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 0f0f7358 | True | s10 | tool_call | unverified | Here's what I'd do to book the flight for Ivan Smith: / | 0.44/0.28 | 0.50/0.50 | 0.28/0.28 |
| 0f0f7358 | True | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.33/0.28 | 0.33/0.33 | 0.33/0.33 |
| 0f0f7358 | True | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.33 | 0.94/0.94 | 0.94/0.94 |
| 0f0f7358 | True | s16 | tool_call | valid | Call book_reservation with cabin = economy; destination | 1.00/0.50 | 1.00/1.00 | 1.00/1.00 |
| 0f0f7358 | True | s18 | tool_call | unverified | Your reservation has been created successfully! Here ar | 0.94/0.94 | 0.94/0.94 | 0.94/0.94 |
| 0f0f7358 | True | s20 | user_turn | unverified | You're all set! Just make sure to: 1. Check the flight  | 0.06/0.06 | 0.17/0.17 | 0.06/0.06 |
| 142fde74 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 142fde74 | True | s2 | user_turn | unverified | Call get_user_details with user_id = user123. | 0.06/0.06 | 0.06/0.06 | 0.06/0.06 |
| 142fde74 | True | s4 | tool_call | unverified | Sure! To get started, could you please provide your use | 0.17/0.00 | 0.28/0.28 | 0.00/0.00 |
| 142fde74 | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 142fde74 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 142fde74 | True | s10 | tool_call | unverified | Your certificate balance is $500.00. I've pulled the de | 0.50/0.50 | 0.50/0.50 | 0.50/0.50 |
| 142fde74 | True | s12 | user_turn | unverified | Call get_flight_status with date = 2024-05-17; flight_n | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 142fde74 | True | s14 | tool_call | unverified | Call get_flight_status with date = 2024-05-17; flight_n | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 142fde74 | True | s16 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.33/0.00 | 0.33/0.28 | 0.33/0.28 |
| 142fde74 | True | s18 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.28 | 0.94/0.78 | 0.94/0.78 |
| 142fde74 | True | s20 | tool_call | valid | Call book_reservation with cabin = economy; destination | 1.00/0.44 | 1.00/0.83 | 1.00/0.83 |
| 142fde74 | True | s22 | tool_call | unverified | Your reservation has been created successfully! Reserva | 0.67/0.67 | 0.67/0.67 | 0.67/0.67 |
| 142fde74 | True | s24 | user_turn | unverified | You're welcome! I'm glad everything looks good. If you  | 0.11/0.00 | 0.17/0.17 | 0.00/0.00 |
| 16aac895 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 16aac895 | True | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.67/0.28 | 0.67/0.67 | 0.67/0.67 |
| 16aac895 | True | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.83/0.67 | 0.83/0.83 | 0.67/0.67 |
| 16aac895 | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 16aac895 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 16aac895 | True | s10 | tool_call | unverified | Here's what I've gathered: / Item / Details / /------/- | 0.61/0.56 | 0.61/0.61 | 0.56/0.56 |
| 16aac895 | True | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 16aac895 | True | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.00 | 0.94/0.50 | 0.94/0.50 |
| 16aac895 | True | s16 | tool_call | unverified | I'm ready to book the reservation for Ivan Smith. Befor | 0.28/0.00 | 0.22/0.22 | 0.00/0.00 |
| 16aac895 | True | s18 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.06/0.00 | 0.06/0.00 | 0.06/0.00 |
| 16aac895 | True | s20 | tool_call | unverified | I'm ready to book the reservation, but the system requi | 0.00/0.00 | 0.06/0.06 | 0.00/0.00 |
| 16aac895 | True | s22 | user_turn | unverified | I'm ready to finalize the booking, but I need to confir | 0.06/0.00 | 0.06/0.06 | 0.00/0.00 |
| 16aac895 | True | s24 | user_turn | valid | Call book_reservation with cabin = economy; destination | 1.00/0.11 | 1.00/0.56 | 1.00/0.56 |
| 16aac895 | True | s26 | tool_call | unverified | ✅ Your reservation has been confirmed! Reservation ID:  | 0.50/0.50 | 0.50/0.50 | 0.50/0.50 |
| 1e01a088 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 1e01a088 | True | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.67/0.67 | 0.67/0.67 | 0.67/0.67 |
| 1e01a088 | True | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.39/0.22 | 0.44/0.44 | 0.22/0.22 |
| 1e01a088 | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 1e01a088 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 1e01a088 | True | s10 | tool_call | unverified | Sure! I'll need a few details before I can create the n | 0.83/0.83 | 0.89/0.89 | 0.83/0.83 |
| 1e01a088 | True | s12 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 0.06/0.00 | 0.06/0.06 | 0.06/0.06 |
| 1e01a088 | True | s14 | tool_call | unverified | Here's the plan for the new reservation: - Trip type: o | 0.17/0.00 | 0.17/0.17 | 0.00/0.00 |
| 1e01a088 | True | s16 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 1e01a088 | True | s18 | tool_call | valid | Call book_reservation with cabin = economy; destination | 1.00/0.00 | 1.00/1.00 | 1.00/1.00 |
| 1e01a088 | True | s20 | tool_call | unverified | Your reservation has been successfully created! Reserva | 0.22/0.22 | 0.22/0.22 | 0.22/0.22 |
| 291cfe67 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 291cfe67 | True | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.67/0.50 | 0.67/0.67 | 0.67/0.67 |
| 291cfe67 | True | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.78/0.56 | 0.78/0.78 | 0.56/0.56 |
| 291cfe67 | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 291cfe67 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 291cfe67 | True | s10 | tool_call | unverified | Here's what I've pulled together for the new reservatio | 0.44/0.39 | 0.50/0.50 | 0.39/0.39 |
| 291cfe67 | True | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.28/0.22 | 0.28/0.22 | 0.28/0.22 |
| 291cfe67 | True | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.22 | 0.94/0.78 | 0.94/0.78 |
| 291cfe67 | True | s16 | tool_call | valid | Call book_reservation with cabin = economy; destination | 1.00/0.44 | 1.00/0.83 | 1.00/0.83 |
| 291cfe67 | True | s18 | tool_call | unverified | ✅ Your reservation has been confirmed! Reservation ID:  | 0.89/0.89 | 0.89/0.89 | 0.89/0.89 |
| 2aca18ff | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 2aca18ff | True | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.67/0.50 | 0.67/0.67 | 0.67/0.67 |
| 2aca18ff | True | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.78/0.56 | 0.78/0.78 | 0.56/0.56 |
| 2aca18ff | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 2aca18ff | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 2aca18ff | True | s10 | tool_call | unverified | Here's what I've pulled together for the new reservatio | 0.50/0.39 | 0.50/0.50 | 0.39/0.39 |
| 2aca18ff | True | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.06/0.06 | 0.06/0.06 | 0.06/0.06 |
| 2aca18ff | True | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.06 | 0.94/0.78 | 0.94/0.78 |
| 2aca18ff | True | s16 | tool_call | unverified | Call search_direct_flight with date = 2024-05-17; desti | 0.11/0.06 | 0.11/0.11 | 0.11/0.11 |
| 2aca18ff | True | s18 | tool_call | unverified | Call search_direct_flight with date = 2024-05-17; desti | 0.11/0.11 | 0.11/0.11 | 0.11/0.11 |
| 2aca18ff | True | s20 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 2aca18ff | True | s22 | tool_call | valid | Call book_reservation with cabin = economy; destination | 1.00/0.00 | 1.00/0.83 | 1.00/0.83 |
| 2aca18ff | True | s24 | tool_call | unverified | ✅ Your reservation has been confirmed! Reservation ID:  | 0.83/0.83 | 0.83/0.83 | 0.83/0.83 |
| 2aca18ff | True | s26 | user_turn | unverified | Your certificate balance is still $500.00. | 0.00/0.00 | 0.56/0.56 | 0.00/0.00 |
| 2e0c25a6 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 2e0c25a6 | True | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.67/0.50 | 0.67/0.67 | 0.67/0.67 |
| 2e0c25a6 | True | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.78/0.56 | 0.78/0.78 | 0.56/0.56 |
| 2e0c25a6 | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 2e0c25a6 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 2e0c25a6 | True | s10 | tool_call | unverified | Here's what I've pulled together for the new reservatio | 0.44/0.39 | 0.50/0.50 | 0.39/0.39 |
| 2e0c25a6 | True | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.33/0.17 | 0.33/0.28 | 0.33/0.28 |
| 2e0c25a6 | True | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.28 | 0.94/0.78 | 0.94/0.78 |
| 2e0c25a6 | True | s16 | tool_call | unverified | I'm sorry for the hiccup. It looks like the payment amo | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 2e0c25a6 | True | s18 | user_turn | unverified | I don't have the exact fare breakdown (including taxes  | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 2e0c25a6 | True | s20 | user_turn | unverified | Call search_direct_flight with date = 2024-05-17; desti | 0.11/0.00 | 0.11/0.11 | 0.11/0.11 |
| 2e0c25a6 | True | s22 | tool_call | unverified | Call search_direct_flight with date = 2024-05-17; desti | 0.11/0.11 | 0.11/0.11 | 0.11/0.11 |
| 2e0c25a6 | True | s24 | tool_call | unverified | Here are the current fare totals that the system shows  | 0.11/0.00 | 0.22/0.22 | 0.00/0.00 |
| 2e0c25a6 | True | s26 | user_turn | valid | Call book_reservation with cabin = economy; destination | 1.00/0.11 | 1.00/0.83 | 1.00/0.83 |
| 2e0c25a6 | True | s28 | tool_call | unverified | ✅ Your reservation has been confirmed! Reservation ID:  | 0.67/0.56 | 0.61/0.61 | 0.56/0.56 |
| 8c8332b6 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 8c8332b6 | True | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.67/0.50 | 0.67/0.67 | 0.67/0.67 |
| 8c8332b6 | True | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.78/0.56 | 0.78/0.78 | 0.56/0.56 |
| 8c8332b6 | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 8c8332b6 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 8c8332b6 | True | s10 | tool_call | unverified | Here's what I've gathered for the new booking: / Item / | 0.56/0.56 | 0.78/0.78 | 0.56/0.56 |
| 8c8332b6 | True | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.28/0.17 | 0.28/0.22 | 0.28/0.22 |
| 8c8332b6 | True | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.22 | 0.94/0.78 | 0.94/0.78 |
| 8c8332b6 | True | s16 | tool_call | valid | Call book_reservation with cabin = economy; destination | 1.00/0.44 | 1.00/0.83 | 1.00/0.83 |
| 8c8332b6 | True | s18 | tool_call | unverified | ✅ Your reservation has been created successfully! - Res | 0.61/0.61 | 0.61/0.61 | 0.61/0.61 |
| a92c9234 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| a92c9234 | True | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.67/0.50 | 0.67/0.67 | 0.67/0.67 |
| a92c9234 | True | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.78/0.56 | 0.78/0.78 | 0.56/0.56 |
| a92c9234 | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| a92c9234 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| a92c9234 | True | s10 | tool_call | unverified | Here's what I'm planning to do for you: / Item / Detail | 0.94/0.89 | 1.00/1.00 | 0.89/0.89 |
| a92c9234 | True | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.28/0.22 | 0.28/0.22 | 0.28/0.22 |
| a92c9234 | True | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.22 | 0.94/0.78 | 0.94/0.78 |
| a92c9234 | True | s16 | tool_call | unverified | Call search_direct_flight with date = 2024-05-17; desti | 0.06/0.06 | 0.06/0.06 | 0.06/0.06 |
| a92c9234 | True | s18 | tool_call | unverified | I'm ready to book the reservation, but I need to confir | 0.00/0.00 | 0.06/0.06 | 0.00/0.00 |
| a92c9234 | True | s20 | user_turn | valid | Call book_reservation with cabin = economy; destination | 1.00/0.06 | 1.00/0.83 | 1.00/0.83 |
| a92c9234 | True | s22 | tool_call | unverified | ✅ Your reservation has been confirmed! Reservation ID:  | 0.89/0.89 | 0.89/0.89 | 0.89/0.89 |
| ab3d173b | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| ab3d173b | True | s2 | user_turn | unverified | Sure! To make sure I book the exact same itinerary for  | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| ab3d173b | True | s4 | user_turn | unverified | Could you let me know the reservation ID of the itinera | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| ab3d173b | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/0.00 | 1.00/1.00 | 1.00/1.00 |
| ab3d173b | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| ab3d173b | True | s10 | tool_call | unverified | Your certificate balance is $500.00. The itinerary you' | 0.28/0.22 | 0.33/0.33 | 0.22/0.22 |
| ab3d173b | True | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.33/0.17 | 0.33/0.33 | 0.33/0.33 |
| ab3d173b | True | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.33 | 0.94/0.94 | 0.94/0.94 |
| ab3d173b | True | s16 | tool_call | valid | Call book_reservation with cabin = economy; destination | 1.00/0.50 | 1.00/1.00 | 1.00/1.00 |
| ab3d173b | True | s18 | tool_call | unverified | Your reservation has been created! Reservation ID: HATH | 0.67/0.67 | 0.67/0.67 | 0.67/0.67 |
| b03440a4 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| b03440a4 | True | s2 | user_turn | unverified | Call get_user_details with user_id = sara_doe_496. | 0.06/0.06 | 0.06/0.06 | 0.06/0.06 |
| b03440a4 | True | s4 | tool_call | unverified | Sure thing! To make sure I get everything right, could  | 0.89/0.00 | 0.89/0.89 | 0.00/0.00 |
| b03440a4 | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/0.94 | 1.00/0.94 | 1.00/0.94 |
| b03440a4 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| b03440a4 | True | s10 | tool_call | unverified | Sure! I've pulled up the details of your current reserv | 0.33/0.33 | 0.33/0.33 | 0.33/0.33 |
| b03440a4 | True | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.33/0.28 | 0.33/0.33 | 0.33/0.33 |
| b03440a4 | True | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.33 | 0.94/0.89 | 0.94/0.89 |
| b03440a4 | True | s16 | tool_call | valid | Call book_reservation with cabin = economy; destination | 1.00/0.44 | 1.00/0.94 | 1.00/0.94 |
| b03440a4 | True | s18 | tool_call | unverified | Your reservation has been created successfully! Reserva | 0.78/0.78 | 0.83/0.83 | 0.78/0.78 |
| b91137fb | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| b91137fb | True | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.67/0.50 | 0.67/0.67 | 0.67/0.67 |
| b91137fb | True | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.78/0.56 | 0.78/0.78 | 0.56/0.56 |
| b91137fb | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| b91137fb | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| b91137fb | True | s10 | tool_call | unverified | Here's what I've pulled together for the new reservatio | 0.56/0.56 | 0.61/0.61 | 0.56/0.56 |
| b91137fb | True | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.33/0.17 | 0.33/0.28 | 0.33/0.28 |
| b91137fb | True | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.28 | 0.94/0.78 | 0.94/0.78 |
| b91137fb | True | s16 | tool_call | valid | Call book_reservation with cabin = economy; destination | 1.00/0.44 | 1.00/0.83 | 1.00/0.83 |
| b91137fb | True | s18 | tool_call | unverified | Your reservation has been confirmed! 🎉 Reservation ID:  | 0.78/0.78 | 0.78/0.78 | 0.78/0.78 |
| b91137fb | True | s20 | user_turn | unverified | I'm sorry, but I don't have the ability to generate or  | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| b91137fb | True | s22 | user_turn | unverified | You're welcome! If there's anything else you need-wheth | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| bb73aded | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| bb73aded | True | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.67/0.67 | 0.67/0.67 | 0.67/0.67 |
| bb73aded | True | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.39/0.22 | 0.44/0.44 | 0.22/0.22 |
| bb73aded | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| bb73aded | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| bb73aded | True | s10 | tool_call | unverified | Sure thing! I'll set up a new reservation that mirrors  | 0.56/0.56 | 0.50/0.50 | 0.56/0.56 |
| bb73aded | True | s12 | user_turn | unverified | Here's what I'm planning to do: / Item / Details / /--- | 0.17/0.00 | 0.61/0.61 | 0.00/0.00 |
| bb73aded | True | s14 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.06 | 0.94/0.94 | 0.94/0.94 |
| bb73aded | True | s16 | tool_call | unverified | I'm ready to book the reservation, but I need to make s | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| bb73aded | True | s18 | user_turn | valid | Call book_reservation with cabin = economy; destination | 1.00/0.17 | 1.00/1.00 | 1.00/1.00 |
| bb73aded | True | s20 | tool_call | unverified | ✅ Your new reservation has been created! - Reservation  | 0.33/0.33 | 0.33/0.33 | 0.33/0.33 |
| c801d833 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| c801d833 | True | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.67/0.50 | 0.67/0.67 | 0.67/0.67 |
| c801d833 | True | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.78/0.56 | 0.78/0.78 | 0.56/0.56 |
| c801d833 | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| c801d833 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| c801d833 | True | s10 | tool_call | unverified | Here's what I've pulled together for the new reservatio | 0.61/0.56 | 0.61/0.61 | 0.56/0.56 |
| c801d833 | True | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.28/0.22 | 0.28/0.22 | 0.28/0.22 |
| c801d833 | True | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.22 | 0.94/0.78 | 0.94/0.78 |
| c801d833 | True | s16 | tool_call | unverified | Call search_direct_flight with date = 2024-05-17; desti | 0.06/0.06 | 0.06/0.06 | 0.06/0.06 |
| c801d833 | True | s18 | tool_call | unverified | Here's the reservation I'm ready to create: / Item / De | 0.11/0.00 | 0.28/0.28 | 0.00/0.00 |
| c801d833 | True | s20 | user_turn | unverified | Call search_onestop_flight with date = 2024-05-17; dest | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| c801d833 | True | s22 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.06/0.00 | 0.06/0.00 | 0.06/0.00 |
| c801d833 | True | s24 | tool_call | unverified | I'm ready to book the reservation, but the system shows | 0.00/0.00 | 0.11/0.11 | 0.00/0.00 |
| c801d833 | True | s26 | user_turn | valid | Call book_reservation with cabin = economy; destination | 1.00/0.06 | 1.00/0.83 | 1.00/0.83 |
| c801d833 | True | s28 | tool_call | unverified | ✅ Your reservation has been confirmed! Reservation ID:  | 0.67/0.67 | 0.67/0.67 | 0.67/0.67 |
| cc2b26ea | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| cc2b26ea | True | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.67/0.28 | 0.67/0.67 | 0.67/0.67 |
| cc2b26ea | True | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.83/0.67 | 0.83/0.83 | 0.67/0.67 |
| cc2b26ea | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| cc2b26ea | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| cc2b26ea | True | s10 | tool_call | unverified | Here's what I've gathered: / Item / Details / /------/- | 0.56/0.56 | 0.61/0.61 | 0.56/0.56 |
| cc2b26ea | True | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.33/0.17 | 0.33/0.17 | 0.33/0.17 |
| cc2b26ea | True | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.17 | 0.94/0.50 | 0.94/0.50 |
| cc2b26ea | True | s16 | tool_call | valid | Call book_reservation with cabin = economy; destination | 1.00/0.28 | 1.00/0.56 | 1.00/0.56 |
| cc2b26ea | True | s18 | tool_call | unverified | Your reservation has been successfully created! 🎉 Reser | 0.72/0.72 | 0.72/0.72 | 0.72/0.72 |
| cd5be315 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| cd5be315 | True | s2 | user_turn | unverified | Sure thing! To get started, could you please provide yo | 0.94/0.00 | 0.94/0.94 | 0.00/0.00 |
| cd5be315 | True | s4 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| cd5be315 | True | s6 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| cd5be315 | True | s8 | tool_call | unverified | Your travel certificate balance is $500.00. To create t | 0.44/0.44 | 0.56/0.56 | 0.44/0.44 |
| cd5be315 | True | s10 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 0.06/0.00 | 0.06/0.06 | 0.06/0.06 |
| cd5be315 | True | s12 | tool_call | unverified | Here's the plan for the new reservation: / Item / Detai | 0.39/0.00 | 0.44/0.44 | 0.00/0.00 |
| cd5be315 | True | s14 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| cd5be315 | True | s16 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.00 | 0.94/0.94 | 0.94/0.94 |
| cd5be315 | True | s18 | tool_call | valid | Call book_reservation with cabin = economy; destination | 1.00/0.50 | 1.00/1.00 | 1.00/1.00 |
| cd5be315 | True | s20 | tool_call | unverified | Your reservation has been created successfully! Reserva | 0.50/0.50 | 0.50/0.50 | 0.50/0.50 |
| cd5be315 | True | s22 | user_turn | unverified | Your e-ticket and boarding pass will be emailed to the  | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| cd5be315 | True | s24 | user_turn | unverified | You're welcome! If you need anything else, feel free to | 0.11/0.00 | 0.22/0.22 | 0.00/0.00 |
| d2135fe7 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| d2135fe7 | True | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.67/0.67 | 0.67/0.67 | 0.67/0.67 |
| d2135fe7 | True | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.78/0.56 | 0.78/0.78 | 0.56/0.56 |
| d2135fe7 | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| d2135fe7 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| d2135fe7 | True | s10 | tool_call | unverified | Here's what I've gathered: / Item / Details / /------/- | 0.50/0.50 | 0.61/0.61 | 0.50/0.50 |
| d2135fe7 | True | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.28/0.22 | 0.28/0.28 | 0.28/0.28 |
| d2135fe7 | True | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.28 | 0.94/0.94 | 0.94/0.94 |
| d2135fe7 | True | s16 | tool_call | unverified | I'm ready to book the reservation, but the system is te | 0.06/0.00 | 0.06/0.06 | 0.00/0.00 |
| d2135fe7 | True | s18 | user_turn | valid | Call book_reservation with cabin = economy; destination | 1.00/0.17 | 1.00/1.00 | 1.00/1.00 |
| d2135fe7 | True | s20 | tool_call | unverified | ✅ Your reservation has been confirmed! Reservation ID:  | 0.78/0.78 | 0.78/0.78 | 0.78/0.78 |
| d3366062 | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| d3366062 | True | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.67/0.28 | 0.67/0.67 | 0.67/0.67 |
| d3366062 | True | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.83/0.67 | 0.83/0.83 | 0.67/0.67 |
| d3366062 | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| d3366062 | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| d3366062 | True | s10 | tool_call | unverified | Here's what I've gathered: / Item / Details / /------/- | 0.61/0.56 | 0.61/0.61 | 0.56/0.56 |
| d3366062 | True | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.28/0.06 | 0.28/0.06 | 0.28/0.06 |
| d3366062 | True | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.06 | 0.94/0.50 | 0.94/0.50 |
| d3366062 | True | s16 | tool_call | unverified | Call search_direct_flight with date = 2024-05-17; desti | 0.11/0.06 | 0.11/0.11 | 0.11/0.11 |
| d3366062 | True | s18 | tool_call | unverified | Call search_direct_flight with date = 2024-05-17; desti | 0.11/0.11 | 0.11/0.11 | 0.11/0.11 |
| d3366062 | True | s20 | tool_call | valid | Call book_reservation with cabin = economy; destination | 1.00/0.00 | 1.00/0.56 | 1.00/0.56 |
| d3366062 | True | s22 | tool_call | unverified | ✅ Your reservation has been created! Reservation ID: `H | 0.83/0.83 | 0.83/0.83 | 0.83/0.83 |
| f81eaa6a | True | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| f81eaa6a | True | s2 | user_turn | unverified | Call get_user_details with user_id = sara_doe_496. | 0.06/0.06 | 0.06/0.06 | 0.06/0.06 |
| f81eaa6a | True | s4 | tool_call | unverified | Sure thing! To make sure I get everything right, could  | 0.89/0.00 | 0.89/0.89 | 0.00/0.00 |
| f81eaa6a | True | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/0.94 | 1.00/0.94 | 1.00/0.94 |
| f81eaa6a | True | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| f81eaa6a | True | s10 | tool_call | unverified | Sure, I can help you duplicate that flight. Just to mak | 0.06/0.06 | 0.06/0.06 | 0.06/0.06 |
| f81eaa6a | True | s12 | user_turn | unverified | Here's the plan for the new reservation: / Item / Detai | 0.44/0.00 | 0.67/0.67 | 0.00/0.00 |
| f81eaa6a | True | s14 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.06/0.06 | 0.06/0.06 | 0.06/0.06 |
| f81eaa6a | True | s16 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.94/0.06 | 0.94/0.89 | 0.94/0.89 |
| f81eaa6a | True | s18 | tool_call | valid | Call book_reservation with cabin = economy; destination | 1.00/0.44 | 1.00/0.94 | 1.00/0.94 |
| f81eaa6a | True | s20 | tool_call | unverified | ✅ Your reservation has been created! Reservation ID: `H | 0.83/0.83 | 0.83/0.83 | 0.83/0.83 |
| f81eaa6a | True | s22 | user_turn | unverified | You're welcome! Have a safe flight and a great day! | 0.06/0.06 | 0.06/0.06 | 0.06/0.06 |
| 51d355a9 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 51d355a9 | False | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.68/0.68 | 0.68/0.68 | 0.68/0.68 |
| 51d355a9 | False | s4 | tool_call | unverified | Sure thing! To get started, could you please share your | 0.84/0.68 | 0.84/0.84 | 0.68/0.68 |
| 51d355a9 | False | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 51d355a9 | False | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 51d355a9 | False | s10 | tool_call | unverified | Here's what I've pulled from your account: / Item / Det | 0.32/0.32 | 0.32/0.32 | 0.32/0.32 |
| 51d355a9 | False | s12 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.32/0.21 | 0.32/0.32 | 0.32/0.32 |
| 51d355a9 | False | s14 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.05/0.00 | 0.05/0.05 | 0.05/0.05 |
| 51d355a9 | False | s16 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.95/0.05 | 0.95/0.95 | 0.95/0.95 |
| 51d355a9 | False | s18 | tool_call | unverified | I'm ready to book the reservation, but the fare for the | 0.00/0.00 | 0.05/0.05 | 0.00/0.00 |
| 51d355a9 | False | s20 | user_turn | unverified | Call transfer_to_human_agents with summary = User wants | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 51d355a9 | False | s22 | tool_call | valid | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 6f12b024 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 6f12b024 | False | s2 | user_turn | unverified | Sure! To make sure I book the exact same itinerary for  | 0.05/0.05 | 0.05/0.05 | 0.05/0.05 |
| 6f12b024 | False | s4 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 6f12b024 | False | s6 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| 6f12b024 | False | s8 | tool_call | unverified | Your travel certificate currently has $500.00 remaining | 0.47/0.47 | 0.53/0.53 | 0.47/0.47 |
| 6f12b024 | False | s10 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.32/0.26 | 0.32/0.32 | 0.32/0.32 |
| 6f12b024 | False | s12 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.95/0.32 | 0.95/0.95 | 0.95/0.95 |
| 6f12b024 | False | s14 | tool_call | unverified | I'm running into a small issue: the total fare for the  | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 6f12b024 | False | s16 | user_turn | unverified | I'm sorry, but the total fare ($375) exceeds the combin | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 6f12b024 | False | s18 | user_turn | unverified | I understand. Let's cancel the booking request first. W | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 6f12b024 | False | s20 | user_turn | unverified | I've confirmed that no reservation was created, so ther | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 6f12b024 | False | s22 | user_turn | unverified | Sure! I can help you find a flight that works with your | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 6f12b024 | False | s24 | user_turn | unverified | Call search_direct_flight with date = 2024-05-21; desti | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 6f12b024 | False | s26 | tool_call | unverified | Call search_direct_flight with date = 2024-05-21; desti | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 6f12b024 | False | s28 | tool_call | unverified | Here are the economy-class flight options for DTW → PHX | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 6f12b024 | False | s30 | user_turn | incorrect | Call book_reservation with cabin = economy; destination | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| 6f12b024 | False | s32 | tool_call | unverified | ✅ Booking confirmed! - Reservation ID: `HATHAT` - Passe | 0.37/0.00 | 0.79/0.79 | 0.00/0.00 |
| d7a124a4 | False | s0 | none | unverified | Hi! How can I help you today? | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| d7a124a4 | False | s2 | user_turn | unverified | Call get_user_details with user_id = ?. | 0.68/0.68 | 0.68/0.68 | 0.68/0.68 |
| d7a124a4 | False | s4 | tool_call | unverified | Sure! To get started, could you please share your user  | 0.84/0.68 | 0.84/0.84 | 0.68/0.68 |
| d7a124a4 | False | s6 | user_turn | unverified | Call get_user_details with user_id = ivan_muller_7015. | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| d7a124a4 | False | s8 | tool_call | unverified | Call get_reservation_details with reservation_id = G72N | 1.00/1.00 | 1.00/1.00 | 1.00/1.00 |
| d7a124a4 | False | s10 | tool_call | unverified | Your certificate balance is $500.00. The total fare for | 0.21/0.21 | 0.37/0.37 | 0.21/0.21 |
| d7a124a4 | False | s12 | user_turn | unverified | Call get_flight_status with date = 2024-05-17; flight_n | 0.05/0.05 | 0.05/0.05 | 0.05/0.05 |
| d7a124a4 | False | s14 | tool_call | unverified | Great! Before I submit the booking, could you please co | 0.32/0.00 | 0.47/0.47 | 0.00/0.00 |
| d7a124a4 | False | s16 | user_turn | unverified | Call get_flight_status with date = 2024-05-17; flight_n | 0.05/0.00 | 0.05/0.05 | 0.05/0.05 |
| d7a124a4 | False | s18 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.37/0.05 | 0.37/0.37 | 0.37/0.37 |
| d7a124a4 | False | s20 | tool_call | unverified | Call book_reservation with cabin = economy; destination | 0.90/0.37 | 0.95/0.95 | 0.95/0.95 |
| d7a124a4 | False | s22 | tool_call | unverified | I'm encountering a small issue: the total fare for the  | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| d7a124a4 | False | s24 | user_turn | unverified | I've re-checked the flight prices: / Flight / Price / / | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| d7a124a4 | False | s26 | user_turn | unverified | Call book_reservation with cabin = economy; destination | 0.16/0.05 | 0.10/0.10 | 0.10/0.10 |
| d7a124a4 | False | s28 | tool_call | unverified | Call search_direct_flight with date = 2024-05-17; desti | 0.16/0.05 | 0.16/0.16 | 0.16/0.16 |
| d7a124a4 | False | s30 | tool_call | unverified | Call search_direct_flight with date = 2024-05-17; desti | 0.16/0.16 | 0.16/0.16 | 0.16/0.16 |
| d7a124a4 | False | s32 | tool_call | unverified | I'm sorry for the confusion. The current prices for the | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| d7a124a4 | False | s34 | user_turn | unverified | I'm sorry to hear you'd like to cancel. To proceed, cou | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| d7a124a4 | False | s36 | user_turn | unverified | Call get_flight_status with date = 2024-05-17; flight_n | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| d7a124a4 | False | s38 | tool_call | unverified | Call get_flight_status with date = 2024-05-17; flight_n | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| d7a124a4 | False | s40 | tool_call | incorrect | Call cancel_reservation with reservation_id = G72NSF. | 0.00/0.00 | 0.00/0.00 | 0.00/0.00 |
| d7a124a4 | False | s42 | tool_call | unverified | Your reservation G72NSF has been cancelled as requested | 0.05/0.00 | 0.05/0.05 | 0.00/0.00 |

