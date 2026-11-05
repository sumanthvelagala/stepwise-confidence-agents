# GIBS: one complete worked example

This is a teaching example. Names, match decisions and prediction values below are illustrative, not a recorded trajectory or a new experiment. The trajectory explorer shows actual saved executions and scores.

## 1. Start with the task and a recorded execution

Suppose the task is: book Maya on the same flight as the user's existing reservation. Maya's details are in the user's profile.

One simplified training execution contains three tool steps:

| Step | Operation | Observed result |
| --- | --- | --- |
| 1 | Read the user's profile | Profile contains Alex and friend Maya |
| 2 | Read the existing reservation | Flight AB123, requested date and cabin |
| 3 | Make a booking | Booking is created for Alex, although the task asks for Maya |

The third action is the intended error here. A tool can execute successfully while the overall task is wrong: the database accepted a booking, but it contains the wrong passenger.

Your collection contains 20 runs per task and 50 tasks. Real runs also contain user turns, assistant messages and additional tool calls. A failed run can contain correct steps before its mistake.

## 2. Split fitting, validation and test task groups

Before this model learns, reserve a task group for testing. This example task must belong to the fitting portion of this particular model.

Training queries update weights. Validation queries choose when to stop and which weights to save. Test queries measure performance afterward. The test task group does not enter fitting, reference construction for fitting targets, or early stopping.

We repeat this over four task-group folds and three seeds for each of two methods: 24 separately trained GCN checkpoints, not 24 new datasets or language models.

## 3. Build one graph per execution

Nodes represent observed results. Operations label edges into their results; edges reflect inferred dependencies. The graph is not hidden chain-of-thought.

A conceptual dependency pattern is:

```text
User/request context
        |
        | get_user_details(...)
        v
     Profile result -----------------------+
        |                                  |
        | get_reservation_details(...)     | book_reservation(...)
        v                                  |
  Reservation result                       |
        |                                  |
        | book_reservation(...)            |
        +-------------> Booking result <---+
```

The booking uses profile and itinerary information, so it can have multiple incoming edges. The same operation can label more than one dependency edge.

Our actual paper_literal projection infers dependencies from observed values and connects dependency-free events to ROOT. User/context nodes are represented, but agent events receive scores. It does not automatically connect every previous turn. The conceptual drawing is not a promise that the heuristic parser reconstructs these exact links.

## 4. Choose successful training references

Call the query graph Gq. Choose five other successful runs of this same task, with graphs R1 through R5. Each is an actual generated execution with a benchmark pass, not a paper figure or a manually designed ideal graph.

Our rule selects 3–5 references from the training partition. It excludes the query's entire exact-content class. Validation queries also use training-only references. The minimum of three and cap of five are project choices, not paper requirements.

Benchmark success is a selection proxy. It does not prove that every action in a reference is correct or necessary.

## 5. Compare Gq with one reference graph

Start with Gq versus R1. Frozen DeBERTa-large-MNLI estimates semantic entailment between operation texts and result texts in both directions. The matching similarity is the maximum of the directional probabilities, following the released implementation.

For illustration, an operation pair might score 0.83 in one direction and 0.76 in the other. Its similarity is 0.83. Required endpoint-node checks must pass too. Node and edge thresholds are 0.7.

These NLI values are not the final step targets. This maximum over directions is also different from NIBS Max's maximum over steps within a reference.

The graph heuristic tries high-scoring seeds and expands compatible matches. The node mapping preserves corresponding edge endpoints and prevents different query nodes mapping to the same reference node. The search is approximate, not a guarantee of the globally largest common subgraph.

## 6. Save one MCS result for each reference

Each pair produces a node map, an edge map and step-support indicators. A query step can align with a different position in the reference; step 3 need not match reference step 3.

Repeat Gq versus R2, R3, R4 and R5. This gives five pair results for this one query.

For paper GIBS, a step's indicator is 1 if its result node belongs to the MCS node map, and 0 otherwise. Membership does not require all incoming edges to match. A node can enter the structure through a matched relationship.

## 7. Average the indicators into soft targets

Suppose those pair matches produce:

| Query step | R1 | R2 | R3 | R4 | R5 | Target |
| --- | --- | --- | --- | --- | --- | --- |
| Read profile | 1 | 1 | 1 | 1 | 1 | 1.0 |
| Read reservation | 1 | 1 | 0 | 1 | 1 | 0.8 |
| Book passenger | 0 | 0 | 1 | 0 | 0 | 0.2 |

The vector is [1.0, 0.8, 0.2]: one target per analysed agent step, not one target for the whole run.

The wrong booking can receive support through semantic overmatching, an imperfect heuristic alignment or an imperfect benchmark-passing reference. Conversely, a valid step can receive less than 1 because it is missing or unmatched in another valid solution. Structural support is not verified correctness.

C4 changes this teacher: same-kind matching, listed critical-field checks, symmetric truncation, multiple compatible components, and support only when every incoming dependency edge matches. A wrong-passenger candidate can be rejected by its field checks. Those checks are not hard rules enforced by the learned GCN later.

## 8. Turn graph text into frozen BERT features

BERT tokenizes result and operation text and creates 768-dimensional CLS features, with a 256-token maximum per text. An adjacency representation describes the graph's connections. Prediction indices identify which nodes correspond to analysed agent events.

These numerical features and graph connections are the model input. The forward pass does not receive rewards, gold actions, correctness labels, reference graphs or MCS masks. BERT remains frozen.

## 9. Predict scores with the GCN

Two GCN layers mix result features across graph connections, with 128 hidden dimensions. Prediction layers combine each agent node's local representation, its operation representation and pooled graph context. A sigmoid turns each output logit into a score in [0,1].

Before learning, the illustrative query might receive [0.55, 0.60, 0.65]. These invented values explain training; they are not predictions from a checkpoint.

The predictor pools information across the recorded graph. Current evaluation is retrospective diagnosis, not a demonstrated prefix-only online guardrail.

## 10. Compute the loss and update weights

Compare predictions [0.55, 0.60, 0.65] with targets [1.0, 0.8, 0.2]. The implemented paper Equation 6 is:

```text
Loss = mean mask entropy + lambda * mean soft binary cross-entropy
lambda = 1

BCE(p, m) = -m * log(p) - (1-m) * log(1-p)
Entropy(p) = -p * log(p) - (1-p) * log(1-p)
```

Cross-entropy encourages agreement with the target. Entropy encourages decisive masks. Their combined objective does not simply force every score to equal the target fraction, and does not establish calibrated correctness probabilities.

Backpropagation computes how weights affect the loss. Adam updates the GCN, operation encoder and prediction layers. Qwen, BERT and DeBERTa are not fine-tuned.

## 11. Repeat through batches and epochs

A batch contains eight query graphs. Each retains its own adjacency and target vector. The code averages their losses and updates weights; graphs do not acquire edges to each other.

One epoch is one shuffled pass through that model's eligible training queries. The first actual fold/model used 511 training graphs: 63 batches of eight and one last batch of seven.

The cap is 150 epochs with validation-based early stopping. Actual paper-GIBS fits ran 51–102 epochs; C4 fits ran 59–91. Repeated epochs reuse the same data, not new generated runs.

## 12. Select and save the checkpoint

After each epoch, calculate teacher-based validation loss without updating weights. Retain the best weights and stop after the configured period without sufficient improvement.

The actual fold0/paper-GIBS/seed7 fit ran 74 epochs; its best validation checkpoint was epoch 54. The saved file contains those weights, architecture settings, fold identities, seed and history. Test accuracy does not select the checkpoint.

We saved 12 paper-GIBS and 12 C4 checkpoints. They use the same architecture with different target methods, held-out groups and random seeds.

## 13. Score a held-out trajectory without MCS

Take an execution from this model's held-out task group. Build its graph, compute frozen BERT features, and run the saved GCN. The forward pass needs no successful references or MCS calculation.

A hypothetical prediction [0.97, 0.81, 0.09] ranks the last step as most suspicious. These values are illustrative, not a claim that the trained model always catches the wrong booking. Inspect actual successes and misses in the explorer.

## 14. Evaluate independently of the teacher

Compare held-out scores with separate correctness judgements. AUROC ranks errors below correct steps. First-error Top-1 checks whether the lowest-confidence candidate identifies the first labelled error in an eligible failed run.

Our primary comparison uses automatic verifier labels on 911 reference-eligible trajectories. Learned models scored all 1,000. Most steps are unverified and human review is pending.

Actual primary tool results: paper GIBS AUROC 0.700 / Top-1 34.1%; C4 AUROC 0.719 / Top-1 52.2%; NIBS Mean AUROC 0.724 / Top-1 71.7%. Learned results are means over three seeds. The illustration must not be presented as guaranteed detection.

## 15. Why only 860 target queries?

Seven tasks lack three successful training references. Seven times 20 is 140, leaving 1,000 minus 140 = 860 eligible training/validation target queries. Each fold uses its own subset; it does not fit all 860 together.

The remaining 140 stay in the dataset. They do not supervise fitting, but models trained on other task groups still generate their held-out predictions.

MCS supplies a reference-derived teacher when individual training-step correctness labels are unavailable. It is not proof of reasoning correctness or the cause of failure.

Sources: supplied research PDF 2605.19228v2 and the current experiment, graph, consensus, model and training-loop code. Toy task, matches and predictions are illustrative; completed counts and metrics come from saved artifacts.
