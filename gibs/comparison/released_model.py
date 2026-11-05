"""Independent reimplementation of the release's active forward/loss equations.

Only active parameters are included. No unused MCS GCN or similarity head.
This is a code-equation control, not the release's whole training experiment.
"""
import torch
from torch import nn


class ReleasedPredictor(nn.Module):
    def __init__(self, embedding_dim=768, hidden_dim=128, dropout=.1):
        super().__init__()
        self.config = dict(embedding_dim=embedding_dim, hidden_dim=hidden_dim, dropout=dropout)
        self.node_encoder = nn.Sequential(nn.Linear(embedding_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout))
        self.edge_encoder = nn.Sequential(nn.Linear(embedding_dim, hidden_dim), nn.ReLU(), nn.Dropout(dropout))
        self.graph_encoder = nn.Sequential(nn.Linear(hidden_dim * 2, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, hidden_dim))
        self.mask_predictor = nn.Sequential(nn.Linear(hidden_dim * 2, hidden_dim), nn.ReLU(), nn.Dropout(dropout),
                                           nn.Linear(hidden_dim, hidden_dim // 2), nn.ReLU(), nn.Linear(hidden_dim // 2, 1))

    def forward_edges(self, graph):
        nodes = self.node_encoder(graph["results"])
        edges = self.edge_encoder(graph["edge_operations"])
        context = self.graph_encoder(torch.cat([nodes.mean(dim=0), edges.mean(dim=0)]))
        return self.mask_predictor(torch.cat([edges, context.expand(len(edges), -1)], dim=1)).squeeze(-1)

    def forward(self, graph):
        logits = self.forward_edges(graph)
        # Incoming edges carry the same operation text, hence identical edge masks.
        return torch.stack([logits[indices].mean() for indices in graph["agent_edge_indices"]])


def released_loss(edge_logits, reference_masks):
    p = edge_logits.sigmoid().clamp(1e-6, 1 - 1e-6)
    entropy = -(p * p.log() + (1 - p) * (1 - p).log()).mean()
    terms = []
    for mask in reference_masks:
        selected = mask.bool()
        if not selected.any():
            continue  # exact active release behavior: empty MCS sets are skipped
        term = -(p[selected] + 1e-8).log().mean()
        if (~selected).any():
            term = term - (1 - p[~selected] + 1e-8).log().mean()
        terms.append(term)
    consistency = torch.stack(terms).mean() if terms else p.sum() * 0
    return entropy + consistency
