"""BERT-feature / two-layer GCN soft-mask predictor (paper sections 4.3–4.4).

BERT features are frozen and supplied by the caller. Forward accepts graph inputs
only: no references, masks, outcome labels, gold actions or correctness labels.
"""
from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F


def normalized_adjacency(n_nodes, edges):
    """Directed source->target GCN normalization, with exactly one self-loop/node."""
    a = torch.eye(n_nodes, dtype=torch.float32)
    for source, target in edges:
        a[target, source] = 1
    inv = a.sum(dim=1).clamp_min(1).rsqrt()
    return inv[:, None] * a * inv[None, :]


class GIBSPredictor(nn.Module):
    def __init__(self, embedding_dim=768, hidden_dim=128, dropout=.1):
        super().__init__()
        self.config = dict(embedding_dim=embedding_dim, hidden_dim=hidden_dim, dropout=dropout)
        self.gcn1 = nn.Linear(embedding_dim, hidden_dim)
        self.gcn2 = nn.Linear(hidden_dim, hidden_dim)
        self.operation_encoder = nn.Linear(embedding_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        self.predictor = nn.Sequential(nn.Linear(hidden_dim * 3, hidden_dim), nn.ReLU(),
                                       nn.Dropout(dropout), nn.Linear(hidden_dim, hidden_dim // 2),
                                       nn.ReLU(), nn.Linear(hidden_dim // 2, 1))

    def forward(self, graph):
        # Pool within this graph only; minibatches never share adjacency/context.
        a = graph["adjacency"]
        h = self.dropout(F.relu(self.gcn1(a @ graph["results"])))
        h = self.gcn2(a @ h)
        idx = graph["agent_indices"]
        local = h[idx]
        operation = F.relu(self.operation_encoder(graph["operations"][idx]))
        context = h.mean(dim=0, keepdim=True).expand(len(idx), -1)
        return self.predictor(torch.cat([local, operation, context], dim=-1)).squeeze(-1)


def gib_loss(logits, target, relevance_weight=1.0):
    """Eq. 6: mean Bernoulli entropy + lambda * CE to fractional consensus.

    Implements the final entropy objective, NOT the distinct sparse-prior KL in
    Eq. 5. BCE-with-logits preserves stability for nearly binary predictions.
    """
    probability = torch.sigmoid(logits)
    entropy = (F.softplus(logits) - probability * logits).mean()
    cross_entropy = F.binary_cross_entropy_with_logits(logits, target)
    return entropy + relevance_weight * cross_entropy, entropy, cross_entropy
