# Generated tables (run_validation.py)

pairs.json sha256 `c075979c6f45f90d00426fe52da910a9d7794ec1a070bae48a06dfb08426d738`; model `microsoft/deberta-large-mnli` @ `7296194b9009373def4f7c5dad292651e4b5cf4e` on mps

## Per pair and configuration

| Pair | Task | Cfg | Mapped edges | Unmatched agent steps (node-level) | Unmatched (context step-level) | First unmatched (node) | Expected | Demonstrably incorrect step(s) unmatched (node/ctx) | Field rejections | Truncated comparisons (flips) | NLI pairs required / uncached | Seconds |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V1 | 48 | A | 5/12 | s6, s8, s10, s12 | s6, s8, s10, s12 | s6 | s6 ✓ | s6: 1/1 | 0 | 1 (0) | 242 / 0 | 0.03 |
| V1 | 48 | B | 5/13 | s6, s8, s10, s12 | s6, s8, s10, s12 | s6 | s6 ✓ | s6: 1/1 | 0 | 1 (0) | 242 / 0 | 0.02 |
| V1 | 48 | C | 5/13 | s6, s8, s10, s12 | s6, s8, s10, s12 | s6 | s6 ✓ | s6: 1/1 | 0 | 1 (0) | 242 / 0 | 0.02 |
| V2 | 48 | A | 7/10 | s6, s8 | s6, s8 | s6 | s6 ✓ | n/a | 0 | 1 (0) | 184 / 2 | 0.52 |
| V2 | 48 | B | 5/11 | s6, s8, s10 | s6, s8, s10 | s6 | s6 ✓ | n/a | 0 | 1 (0) | 184 / 0 | 0.02 |
| V2 | 48 | C | 5/11 | s6, s8, s10 | s6, s8, s10 | s6 | s6 ✓ | n/a | 0 | 1 (0) | 184 / 0 | 0.02 |
| V3 | 40 | A | 9/14 | s6, s10 | s6, s10 | s6 | s6 ✓ | s10: 1/1 | 0 | 1 (0) | 242 / 194 | 10.83 |
| V3 | 40 | B | 7/15 | s6, s10, s12 | s6, s8, s10, s12 | s6 | s6 ✓ | s10: 1/1 | 0 | 5 (0) | 244 / 0 | 0.02 |
| V3 | 40 | C | 7/15 | s6, s10, s12 | s6, s8, s10, s12 | s6 | s6 ✓ | s10: 1/1 | 1 | 5 (0) | 244 / 0 | 0.02 |
| V4 | 25 | A | 16/40 | s2, s4, s10, s12, s14, s16, s22, s24, s26, s28, s30, s32, s34, s36, s38, s40, s42 | s2, s4, s10, s12, s14, s16, s22, s24, s26, s28, s30, s32, s34, s36, s38, s40, s42 | s2 | s2 ✓ | s40: 1/1 | 0 | 103 (0) | 886 / 817 | 193.8 |
| V4 | 25 | B | 13/50 | s2, s4, s10, s12, s14, s16, s22, s24, s26, s28, s30, s32, s34, s36, s38, s40, s42 | s2, s4, s10, s12, s14, s16, s18, s22, s24, s26, s28, s30, s32, s34, s36, s38, s40, s42 | s2 | s2 ✓ | s40: 1/1 | 0 | 140 (0) | 880 / 16 | 8.3 |
| V4 | 25 | C | 13/50 | s2, s4, s10, s12, s14, s16, s22, s24, s26, s28, s30, s32, s34, s36, s38, s40, s42 | s2, s4, s10, s12, s14, s16, s18, s22, s24, s26, s28, s30, s32, s34, s36, s38, s40, s42 | s2 | s2 ✓ | s40: 1/1 | 0 | 140 (0) | 880 / 0 | 0.11 |
| V5 | 34 | A | 2/11 | s2, s4, s6, s8, s10, s12, s14 | s2, s4, s6, s8, s10, s12, s14 | s2 | s2 ✓ | s12: 1/1 | 0 | 3 (0) | 312 / 288 | 84.9 |
| V5 | 34 | B | 1/15 | s2, s4, s6, s8, s10, s12, s14 | s2, s4, s6, s8, s10, s12, s14 | s2 | s2 ✓ | s12: 1/1 | 0 | 9 (0) | 318 / 6 | 3.85 |
| V5 | 34 | C | 1/15 | s2, s4, s6, s8, s10, s12, s14 | s2, s4, s6, s8, s10, s12, s14 | s2 | s2 ✓ | s12: 1/1 | 0 | 9 (0) | 318 / 0 | 0.04 |
| V6 | 9 | A | 7/12 | s10, s12, s14 | s10, s12, s14 | s10 | s10 ✓ | s10: 1/1, s12: 1/1 | 0 | 7 (0) | 210 / 157 | 17.55 |
| V6 | 9 | B | 9/15 | s10, s12, s14 | s10, s12, s14 | s10 | s10 ✓ | s10: 1/1, s12: 1/1 | 0 | 15 (0) | 210 / 0 | 0.02 |
| V6 | 9 | C | 9/15 | s10, s12, s14 | s10, s12, s14 | s10 | s10 ✓ | s10: 1/1, s12: 1/1 | 0 | 15 (0) | 210 / 0 | 0.02 |
| V7 | 4 | A | 3/32 | s0, s2, s12, s14, s16, s18, s20, s22, s24, s26, s28, s30, s32, s34, s36, s38, s40, s42, s44, s46, s48, s50 | s0, s2, s4, s12, s14, s16, s18, s20, s22, s24, s26, s28, s30, s32, s34, s36, s38, s40, s42, s44, s46, s48, s50 | s0 | s12 ✗ | s12: 1/1, s20: 1/1 | 0 | 14 (0) | 626 / 594 | 75.68 |
| V7 | 4 | B | 5/43 | s0, s2, s12, s14, s16, s18, s20, s22, s24, s26, s28, s30, s32, s34, s36, s38, s40, s42, s44, s46, s48, s50 | s0, s2, s4, s12, s14, s16, s18, s20, s22, s24, s26, s28, s30, s32, s34, s36, s38, s40, s42, s44, s46, s48, s50 | s0 | s12 ✗ | s12: 1/1, s20: 1/1 | 0 | 39 (0) | 642 / 12 | 7.7 |
| V7 | 4 | C | 5/43 | s0, s2, s12, s14, s16, s18, s20, s22, s24, s26, s28, s30, s32, s34, s36, s38, s40, s42, s44, s46, s48, s50 | s0, s2, s4, s12, s14, s16, s18, s20, s22, s24, s26, s28, s30, s32, s34, s36, s38, s40, s42, s44, s46, s48, s50 | s0 | s12 ✗ | s12: 1/1, s20: 1/1 | 1 | 39 (0) | 642 / 0 | 0.07 |
| V8 | 4 | A | 3/14 | s2, s4, s6, s8, s10, s12, s14, s16 | s2, s4, s6, s8, s10, s12, s14, s16 | s2 | no prediction | n/a | 0 | 1 (0) | 450 / 353 | 69.22 |
| V8 | 4 | B | 2/17 | s0, s2, s4, s6, s8, s10, s12, s14 | s0, s2, s4, s6, s8, s10, s12, s14, s16 | s0 | no prediction | n/a | 0 | 2 (0) | 452 / 0 | 0.05 |
| V8 | 4 | C | 2/17 | s0, s2, s4, s6, s8, s10, s12, s14 | s0, s2, s4, s6, s8, s10, s12, s14, s16 | s0 | no prediction | n/a | 0 | 2 (0) | 452 / 0 | 0.06 |
| V9 | 38 | A | 5/17 | s6, s8, s10, s12, s14, s16, s18 | s6, s8, s10, s12, s14, s16, s18 | s6 | no prediction | n/a | 0 | 4 (2) | 618 / 568 | 86.74 |
| V9 | 38 | B | 3/18 | s4, s6, s8, s10, s12, s14, s16, s18 | s4, s6, s8, s10, s12, s14, s16, s18 | s4 | no prediction | n/a | 0 | 5 (2) | 620 / 2 | 1.08 |
| V9 | 38 | C | 3/18 | s4, s6, s8, s10, s12, s14, s16, s18 | s4, s6, s8, s10, s12, s14, s16, s18 | s4 | no prediction | n/a | 0 | 5 (2) | 620 / 0 | 0.07 |

## Per-step detail

### V1 (task 48): query 7f5cbcd7 vs reference c890f90b

| Step | Kind | Operation | A node/ctx | B node/ctx | C node/ctx | Best ref edge (s_edge) | Why unmatched (C) | Field check vs best partner |
|---|---|---|---|---|---|---|---|---|
| s0 | agent_message | Hi! How can I help you today? | 1/1 | 1/1 | 1/1 | ROOT->N:s0 (0.991) | mapped | — |
| s2 | agent_message | Sure, I can help with that. Could you please provide your user ID and the reservation ID for the flight you'd… | 1/1 | 1/1 | 1/1 | N:u1->N:s2 (0.995) | mapped | — |
| s4 | tool_result | Call get_reservation_details with reservation_id = 3RK2T9. | 1/1 | 1/1 | 1/1 | N:u3->N:s4 (0.984) | mapped | compatible |
| s6 | tool_result | Call cancel_reservation with reservation_id = 3RK2T9. | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.095) | no_reference_edge_above_tau_e | — |
| s8 | agent_message | Your reservation 3RK2T9 has been cancelled successfully. Because the booking was made within the last 24 hour… | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.089) | no_reference_edge_above_tau_e | — |
| s10 | agent_message | Your refund will be credited back to the original payment method (gift card 2550356) within 5-7 business days… | 0/0 | 0/0 | 0/0 | N:s10->N:u11 (0.243) | no_reference_edge_above_tau_e | — |
| s12 | agent_message | You're very welcome! If anything comes up, just let me know. Have a wonderful day! | 0/0 | 0/0 | 0/0 | N:s10->N:u11 (0.339) | no_reference_edge_above_tau_e | — |

### V2 (task 48): query c890f90b vs reference 655b2a43

| Step | Kind | Operation | A node/ctx | B node/ctx | C node/ctx | Best ref edge (s_edge) | Why unmatched (C) | Field check vs best partner |
|---|---|---|---|---|---|---|---|---|
| s0 | agent_message | Hi! How can I help you today? | 1/1 | 1/1 | 1/1 | ROOT->N:s0 (0.991) | mapped | — |
| s2 | agent_message | Sure, I can help with that. To proceed, could you please provide: 1. Your user ID (the ID you use to log in t… | 1/1 | 1/1 | 1/1 | N:u1->N:s2 (0.994) | mapped | — |
| s4 | tool_result | Call get_reservation_details with reservation_id = 3RK2T9. | 1/1 | 1/1 | 1/1 | N:u3->N:s4 (0.984) | mapped | compatible |
| s6 | agent_message | I'm sorry, but I can't process a cancellation for that reservation. According to our records, the booking was… | 0/0 | 0/0 | 0/0 | N:s6->N:s8 (0.307) | no_reference_edge_above_tau_e | — |
| s8 | tool_result | Call transfer_to_human_agents with summary = User claims booking was made 10 hours ago but system shows creat… | 0/0 | 0/0 | 0/0 | N:s10->N:u11 (0.945) | endpoint_below_tau_v | — |
| s10 | agent_message | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON. | 1/1 | 0/0 | 0/0 | N:s10->N:u11 (0.995) | candidate_but_disconnected_from_mcs | — |

### V3 (task 40): query b4901df6 vs reference f6000fbe

| Step | Kind | Operation | A node/ctx | B node/ctx | C node/ctx | Best ref edge (s_edge) | Why unmatched (C) | Field check vs best partner |
|---|---|---|---|---|---|---|---|---|
| s0 | agent_message | Hi! How can I help you today? | 1/1 | 1/1 | 1/1 | ROOT->N:s0 (0.991) | mapped | — |
| s2 | agent_message | Sure, I can help with that. Could you please provide your user ID? | 1/1 | 1/1 | 1/1 | N:u1->N:s2 (0.993) | mapped | — |
| s4 | agent_message | Here's what I'll do: I'll update the passenger list for reservation 3RK2T9 to replace "Mei Lee" with "Mei Gar… | 1/1 | 1/1 | 1/1 | N:u3->N:s4 (0.978) | mapped | — |
| s6 | agent_message | I'll need the date of birth for the passenger to update the record. Could you please provide Mei Garcia's dat… | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.188) | no_reference_edge_above_tau_e | — |
| s8 | tool_result | Call get_reservation_details with reservation_id = 3RK2T9. | 1/1 | 1/0 | 1/0 | N:u5->N:s6 (0.984) | candidate_but_mapping_conflict_or_bfs_order | compatible |
| s10 | tool_result | Call update_reservation_passengers with passengers[0].dob = 1992-11-12; passengers[0].first_name = Anya; pass… | 0/0 | 0/0 | 0/0 | N:s6->N:s8 (0.457) | no_reference_edge_above_tau_e | HARD: args.passengers: (('anya', 'garcia', '1992-11-12'), ('mei', 'garcia', '1992-07-15')) != (('anya', 'garcia', '1992-11-12'), ('mei', 'garcia', '1989-12-13')); res |
| s12 | agent_message | Your reservation 3RK2T9 has been updated. The passenger name is now Mei Garcia (DOB: 1992-07-15). Let me know… | 1/1 | 0/0 | 0/0 | N:s8->N:s10 (0.994) | rejected_by_structured_field_check | — |

### V4 (task 25): query d7a124a4 vs reference ab3d173b

| Step | Kind | Operation | A node/ctx | B node/ctx | C node/ctx | Best ref edge (s_edge) | Why unmatched (C) | Field check vs best partner |
|---|---|---|---|---|---|---|---|---|
| s0 | agent_message | Hi! How can I help you today? | 1/1 | 1/1 | 1/1 | ROOT->N:s0 (0.991) | mapped | — |
| s2 | tool_result | Call get_user_details with user_id = ?. | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.073) | no_reference_edge_above_tau_e | — |
| s4 | agent_message | Sure! To get started, could you please share your user ID? This will help me pull up your current reservation… | 0/0 | 0/0 | 0/0 | N:s10->N:u11 (0.556) | no_reference_edge_above_tau_e | — |
| s6 | tool_result | Call get_user_details with user_id = ivan_muller_7015. | 1/1 | 1/1 | 1/1 | N:u5->N:s6 (0.966) | mapped | compatible |
| s8 | tool_result | Call get_reservation_details with reservation_id = G72NSF. | 1/1 | 1/1 | 1/1 | N:s6->N:s8 (0.983) | mapped | compatible |
| s10 | agent_message | Your certificate balance is $500.00. The total fare for the itinerary (DTW → PHX → SEA on 2024-05-17) is $299… | 0/0 | 0/0 | 0/0 | N:u3->N:s4 (0.611) | no_reference_edge_above_tau_e | — |
| s12 | tool_result | Call get_flight_status with date = 2024-05-17; flight_number = HAT097. | 0/0 | 0/0 | 0/0 | N:s14->N:s16 (0.240) | no_reference_edge_above_tau_e | HARD: tool_name: 'get_flight_status' != 'book_reservation' |
| s14 | agent_message | Great! Before I submit the booking, could you please confirm that you'd like to proceed with the reservation … | 0/0 | 0/0 | 0/0 | N:s10->N:u11 (0.310) | no_reference_edge_above_tau_e | — |
| s16 | tool_result | Call get_flight_status with date = 2024-05-17; flight_number = HAT251. | 0/0 | 0/0 | 0/0 | N:s12->N:s14 (0.211) | no_reference_edge_above_tau_e | HARD: tool_name: 'get_flight_status' != 'book_reservation' |
| s18 | tool_result | Call book_reservation with cabin = economy; destination = SEA; flight_type = one_way; flights[0].date = 2024-… | 1/1 | 1/0 | 1/0 | N:u11->N:s12 (0.983) | endpoint_below_tau_v | compatible |
| s20 | tool_result | Call book_reservation with cabin = economy; destination = SEA; flight_type = one_way; flights[0].date = 2024-… | 1/1 | 1/1 | 1/1 | N:s12->N:s14 (0.979) | mapped | compatible |
| s22 | agent_message | I'm encountering a small issue: the total fare for the itinerary is $375.00, but the combined amount of your … | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.225) | no_reference_edge_above_tau_e | — |
| s24 | agent_message | I've re-checked the flight prices: / Flight / Price / /--------/-------/ / HAT097 (DTW → PHX) / $158.00 / / H… | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.161) | no_reference_edge_above_tau_e | — |
| s26 | tool_result | Call book_reservation with cabin = economy; destination = SEA; flight_type = one_way; flights[0].date = 2024-… | 0/0 | 0/0 | 0/0 | N:s12->N:s14 (0.979) | candidate_but_mapping_conflict_or_bfs_order, endpoint_below_tau_v | compatible |
| s28 | tool_result | Call search_direct_flight with date = 2024-05-17; destination = PHX; origin = DTW. | 0/0 | 0/0 | 0/0 | N:s14->N:s16 (0.161) | no_reference_edge_above_tau_e | HARD: tool_name: 'search_direct_flight' != 'book_reservation' |
| s30 | tool_result | Call search_direct_flight with date = 2024-05-17; destination = SEA; origin = PHX. | 0/0 | 0/0 | 0/0 | N:s12->N:s14 (0.148) | no_reference_edge_above_tau_e | HARD: tool_name: 'search_direct_flight' != 'book_reservation' |
| s32 | agent_message | I'm sorry for the confusion. The current prices for the flights you'd like to book are: / Flight / Price (eco… | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.237) | no_reference_edge_above_tau_e | — |
| s34 | agent_message | I'm sorry to hear you'd like to cancel. To proceed, could you let me know the reason for the cancellation? (O… | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.218) | no_reference_edge_above_tau_e | — |
| s36 | tool_result | Call get_flight_status with date = 2024-05-17; flight_number = HAT097. | 0/0 | 0/0 | 0/0 | N:s14->N:s16 (0.240) | no_reference_edge_above_tau_e | HARD: tool_name: 'get_flight_status' != 'book_reservation' |
| s38 | tool_result | Call get_flight_status with date = 2024-05-17; flight_number = HAT251. | 0/0 | 0/0 | 0/0 | N:s12->N:s14 (0.211) | no_reference_edge_above_tau_e | HARD: tool_name: 'get_flight_status' != 'book_reservation' |
| s40 | tool_result | Call cancel_reservation with reservation_id = G72NSF. | 0/0 | 0/0 | 0/0 | N:s18->N:u19 (0.349) | no_reference_edge_above_tau_e | — |
| s42 | agent_message | Your reservation G72NSF has been cancelled as requested. A refund will be processed to your original payment … | 0/0 | 0/0 | 0/0 | N:s18->N:u19 (0.123) | no_reference_edge_above_tau_e | — |

### V5 (task 34): query 2a9a7a9b vs reference b47dbb44

| Step | Kind | Operation | A node/ctx | B node/ctx | C node/ctx | Best ref edge (s_edge) | Why unmatched (C) | Field check vs best partner |
|---|---|---|---|---|---|---|---|---|
| s0 | agent_message | Hi! How can I help you today? | 1/1 | 1/1 | 1/1 | ROOT->N:s0 (0.991) | mapped | — |
| s2 | tool_result | Call get_reservation_details with reservation_id = HXDUBJ. | 0/0 | 0/0 | 0/0 | N:u3->N:s4 (0.971) | endpoint_below_tau_v | compatible |
| s4 | tool_result | Call get_user_details with user_id = yara_garcia_1905. | 0/0 | 0/0 | 0/0 | N:s12->N:s14 (0.101) | no_reference_edge_above_tau_e | — |
| s6 | tool_result | Call search_direct_flight with date = 2024-05-19; destination = SFO; origin = IAH. | 0/0 | 0/0 | 0/0 | N:s0->N:u1 (0.088) | no_reference_edge_above_tau_e | — |
| s8 | tool_result | Call search_direct_flight with date = 2024-05-23; destination = IAH; origin = SFO. | 0/0 | 0/0 | 0/0 | N:s8->N:s10 (0.973) | candidate_but_disconnected_from_mcs, endpoint_below_tau_v | compatible |
| s10 | agent_message | I've pulled up your reservation (HXDUBJ). Here's what the requested changes would look like: / Segment / Curr… | 0/0 | 0/0 | 0/0 | N:s12->N:s14 (0.584) | no_reference_edge_above_tau_e | — |
| s12 | tool_result | Call cancel_reservation with reservation_id = HXDUBJ. | 0/0 | 0/0 | 0/0 | N:s16->N:u17 (0.299) | no_reference_edge_above_tau_e | — |
| s14 | agent_message | Your reservation HXDUBJ has been cancelled. The original booking remains unchanged, and the full amount you p… | 0/0 | 0/0 | 0/0 | N:u15->N:s16 (0.275) | no_reference_edge_above_tau_e | — |

### V6 (task 9): query 68290327 vs reference 67030d75

| Step | Kind | Operation | A node/ctx | B node/ctx | C node/ctx | Best ref edge (s_edge) | Why unmatched (C) | Field check vs best partner |
|---|---|---|---|---|---|---|---|---|
| s0 | agent_message | Hi! How can I help you today? | 1/1 | 1/1 | 1/1 | ROOT->N:s0 (0.991) | mapped | — |
| s2 | tool_result | Call get_reservation_details with reservation_id = IFOYYZ. | 1/1 | 1/1 | 1/1 | N:u1->N:s2 (0.981) | mapped | compatible |
| s4 | tool_result | Call get_reservation_details with reservation_id = NQNU5R. | 1/1 | 1/1 | 1/1 | N:s2->N:s4 (0.978) | mapped | compatible |
| s6 | tool_result | Call get_reservation_details with reservation_id = M20IZO. | 1/1 | 1/1 | 1/1 | N:s4->N:s6 (0.986) | mapped | compatible |
| s8 | tool_result | Call search_direct_flight with date = 2024-05-22; destination = MCO; origin = JFK. | 1/1 | 1/1 | 1/1 | N:s6->N:s8 (0.969) | mapped | compatible |
| s10 | agent_message | I can cancel your reservation NQNU5R for you. I'm not able to cancel IFOYYZ (it doesn't meet the cancellation… | 0/0 | 0/0 | 0/0 | N:s12->N:u13 (0.279) | no_reference_edge_above_tau_e | — |
| s12 | tool_result | Call cancel_reservation with reservation_id = NQNU5R. | 0/0 | 0/0 | 0/0 | N:s8->N:s10 (0.249) | no_reference_edge_above_tau_e | HARD: tool_name: 'cancel_reservation' != 'transfer_to_human_agents' |
| s14 | agent_message | Your reservation NQNU5R has been successfully cancelled. The full amount will be refunded to the credit card … | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.074) | no_reference_edge_above_tau_e | — |

### V7 (task 4): query 259d9890 vs reference ce8b1b6b

| Step | Kind | Operation | A node/ctx | B node/ctx | C node/ctx | Best ref edge (s_edge) | Why unmatched (C) | Field check vs best partner |
|---|---|---|---|---|---|---|---|---|
| s0 | agent_message | Hi! How can I help you today? | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.991) | candidate_but_disconnected_from_mcs | — |
| s2 | agent_message | Sure-let's find the reservation that was affected. Could you please provide the reservation ID for the busine… | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.175) | no_reference_edge_above_tau_e | — |
| s4 | tool_result | Call get_user_details with user_id = sophia_silva_7557. | 1/0 | 1/0 | 1/0 | N:u1->N:s2 (0.986) | endpoint_below_tau_v | compatible |
| s6 | tool_result | Call get_reservation_details with reservation_id = NM1VX1. | 1/1 | 1/1 | 1/1 | N:s6->N:s8 (0.980) | mapped | compatible |
| s8 | tool_result | Call get_reservation_details with reservation_id = KC18K6. | 1/1 | 1/1 | 1/1 | N:s8->N:s10 (0.979) | mapped | compatible |
| s10 | tool_result | Call get_reservation_details with reservation_id = S61CZX. | 1/1 | 1/1 | 1/1 | N:s10->N:s12 (0.989) | mapped | compatible |
| s12 | tool_result | Call send_certificate with no arguments. | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.112) | no_reference_edge_above_tau_e | — |
| s14 | tool_result | Call send_certificate with no arguments. | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.112) | no_reference_edge_above_tau_e | — |
| s16 | tool_result | Call get_reservation_details with reservation_id = NM1VX1. | 0/0 | 0/0 | 0/0 | N:s6->N:s8 (0.980) | candidate_but_mapping_conflict_or_bfs_order, endpoint_below_tau_v | compatible |
| s18 | agent_message | Hello! How can I help you today with your flight reservation? | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.966) | endpoint_below_tau_v | — |
| s20 | tool_result | Call send_certificate with user_id = sophia_silva_7557; amount = 100. | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.147) | no_reference_edge_above_tau_e | — |
| s22 | agent_message | I'm sorry you're still having trouble locating the reservation and that a flight was canceled. First, let's p… | 0/0 | 0/0 | 0/0 | N:s12->N:s14 (0.351) | no_reference_edge_above_tau_e | — |
| s24 | tool_result | Call get_user_details with user_id = sophia_silva_7557. | 0/0 | 0/0 | 0/0 | N:u1->N:s2 (0.986) | endpoint_below_tau_v | HARD: result.payment_methods: (('certificate_3221322', 100.0), ('certificate_3887113', 150.0), ('certificate_8045380', 500.0), ('credit_card_419677... != (('certifica |
| s26 | tool_result | Call get_reservation_details with reservation_id = NM1VX1. | 0/0 | 0/0 | 0/0 | N:s6->N:s8 (0.980) | candidate_but_mapping_conflict_or_bfs_order, rejected_by_structured_field_check | compatible |
| s28 | tool_result | Call get_reservation_details with reservation_id = KC18K6. | 0/0 | 0/0 | 0/0 | N:s8->N:s10 (0.979) | candidate_but_disconnected_from_mcs, candidate_but_mapping_conflict_or_bfs_order | compatible |
| s30 | tool_result | Call transfer with no arguments. | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.103) | no_reference_edge_above_tau_e | — |
| s32 | tool_result | Call get_user_details with user_id = sophia_silva_7557. | 0/0 | 0/0 | 0/0 | N:u1->N:s2 (0.986) | endpoint_below_tau_v | HARD: result.payment_methods: (('certificate_3221322', 100.0), ('certificate_3887113', 150.0), ('certificate_8045380', 500.0), ('credit_card_419677... != (('certifica |
| s34 | tool_result | Call transfer with no arguments. | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.103) | no_reference_edge_above_tau_e | — |
| s36 | tool_result | Call transfer with no arguments. | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.103) | no_reference_edge_above_tau_e | — |
| s38 | tool_result | Call transfer with no arguments. | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.103) | no_reference_edge_above_tau_e | — |
| s40 | tool_result | Call get_user_details with no arguments. | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.083) | no_reference_edge_above_tau_e | — |
| s42 | tool_result | Call get_user_details with user_id = sophia_silva_7557. | 0/0 | 0/0 | 0/0 | N:u1->N:s2 (0.986) | endpoint_below_tau_v | HARD: result.payment_methods: (('certificate_3221322', 100.0), ('certificate_3887113', 150.0), ('certificate_8045380', 500.0), ('credit_card_419677... != (('certifica |
| s44 | agent_message | Hello! I've retrieved your profile details for reference. How can I assist you today? | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.991) | endpoint_below_tau_v | — |
| s46 | agent_message | I'm sorry to hear about the impact the flight cancellation had on your meeting and schedule. Per our policy, … | 0/0 | 0/0 | 0/0 | N:s12->N:s14 (0.603) | no_reference_edge_above_tau_e | — |
| s48 | tool_result | Call send_certificate with amount = 100; user_id = sophia_silva_7557. | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.139) | no_reference_edge_above_tau_e | — |
| s50 | agent_message | ✅ Your request has been processed. We have issued a travel-certificate worth $100 to your account (certificat… | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.148) | no_reference_edge_above_tau_e | — |

### V8 (task 4): query ce8b1b6b vs reference 54ecc816

| Step | Kind | Operation | A node/ctx | B node/ctx | C node/ctx | Best ref edge (s_edge) | Why unmatched (C) | Field check vs best partner |
|---|---|---|---|---|---|---|---|---|
| s0 | agent_message | Hi! How can I help you today? | 1/1 | 0/0 | 0/0 | ROOT->N:s0 (0.991) | candidate_but_disconnected_from_mcs | — |
| s2 | tool_result | Call get_user_details with user_id = sophia_silva_7557. | 0/0 | 0/0 | 0/0 | N:u5->N:s6 (0.986) | endpoint_below_tau_v | compatible |
| s4 | agent_message | I'm sorry to hear about the inconvenience. In order to help you proceed, could you please tell me the reserva… | 0/0 | 0/0 | 0/0 | N:u1->N:s2 (0.429) | no_reference_edge_above_tau_e | — |
| s6 | tool_result | Call get_reservation_details with reservation_id = AB1234. | 0/0 | 0/0 | 0/0 | N:s14->N:s16 (0.115) | no_reference_edge_above_tau_e | — |
| s8 | tool_result | Call get_reservation_details with reservation_id = NM1VX1. | 0/0 | 0/0 | 0/0 | N:s14->N:s16 (0.139) | no_reference_edge_above_tau_e | — |
| s10 | tool_result | Call get_reservation_details with reservation_id = KC18K6. | 0/0 | 0/0 | 0/0 | N:s14->N:s16 (0.123) | no_reference_edge_above_tau_e | — |
| s12 | tool_result | Call get_reservation_details with reservation_id = S61CZX. | 0/0 | 0/0 | 0/0 | N:s14->N:s16 (0.123) | no_reference_edge_above_tau_e | — |
| s14 | agent_message | I'm afraid I couldn't locate any record for a reservation numbered AB1234 in our system. Because I'm unable t… | 0/0 | 0/0 | 0/0 | N:u1->N:s2 (0.610) | no_reference_edge_above_tau_e | — |
| s16 | tool_result | Call transfer_to_human_agents with summary = User requesting higher compensation for a cancelled business fli… | 0/0 | 1/0 | 1/0 | N:s16->N:u17 (0.172) | no_reference_edge_above_tau_e | — |
| s18 | agent_message | YOU ARE BEING TRANSFERRED TO A HUMAN AGENT. PLEASE HOLD ON. | 1/1 | 1/1 | 1/1 | N:s14->N:s16 (0.970) | mapped | — |

### V9 (task 38): query c59e7ab6 vs reference 2a47da10

| Step | Kind | Operation | A node/ctx | B node/ctx | C node/ctx | Best ref edge (s_edge) | Why unmatched (C) | Field check vs best partner |
|---|---|---|---|---|---|---|---|---|
| s0 | agent_message | Hi! How can I help you today? | 1/1 | 1/1 | 1/1 | ROOT->N:s0 (0.991) | mapped | — |
| s2 | agent_message | Sure thing! Could you share your reservation ID or any other details (like the flight date, origin, or destin… | 1/1 | 1/1 | 1/1 | N:u1->N:s2 (0.990) | mapped | — |
| s4 | agent_message | I can help locate it for you. Could you please provide your user ID (the one you use to log in to our system)? | 1/1 | 0/0 | 0/0 | N:u3->N:s4 (0.986) | endpoint_below_tau_v | — |
| s6 | tool_result | Call get_user_details with user_id = noah_muller_9847. | 0/0 | 0/0 | 0/0 | N:u5->N:s6 (0.980) | endpoint_below_tau_v | compatible |
| s8 | tool_result | Call get_reservation_details with reservation_id = SDZQKO. | 0/0 | 0/0 | 0/0 | N:s6->N:s8 (0.982) | endpoint_below_tau_v | compatible |
| s10 | agent_message | I've pulled up your most recent booking (reservation SDZQKO). The itinerary is: / Segment / Flight / Date / F… | 0/0 | 0/0 | 0/0 | N:s14->N:s16 (0.356) | no_reference_edge_above_tau_e | — |
| s12 | tool_result | Call get_flight_status with date = 2024-05-27; flight_number = HAT228. | 0/0 | 0/0 | 0/0 | N:s10->N:s12 (0.986) | candidate_but_disconnected_from_mcs, endpoint_below_tau_v | compatible |
| s14 | agent_message | I'm happy to help clarify the situation. 1. Flight status The first leg (HAT228 on 2024-05-27) is currently l… | 0/0 | 0/0 | 0/0 | ROOT->N:s0 (0.452) | no_reference_edge_above_tau_e | — |
| s16 | agent_message | I've double-checked the reservation record (SDZQKO) and it currently lists two passengers: 1. Noah Muller (DO… | 0/0 | 0/0 | 0/0 | N:s14->N:s16 (0.445) | no_reference_edge_above_tau_e | — |
| s18 | agent_message | Got it-your reservation will remain as it is with the two passengers listed. If anything changes or you need … | 0/0 | 0/0 | 0/0 | N:s22->N:u23 (0.450) | no_reference_edge_above_tau_e | — |

