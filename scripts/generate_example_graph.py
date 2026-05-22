from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.schemas.rule import Rule, RuleDetails
from app.services.graph.graph_builder import GraphBuilder


EXAMPLE_RULES = [
    Rule(
        source="MIN_INPUT_VOLTS",
        target="MAX_INPUT_VOLTS",
        rule_details=RuleDetails(
            constraint="MAX_INPUT_VOLTS >= MIN_INPUT_VOLTS",
            message="Maximum input voltage must be greater than or equal to minimum input voltage.",
        ),
    ),
    Rule(
        source="MIN_OUTPUT_VOLTS",
        target="MAX_OUTPUT_VOLTS",
        rule_details=RuleDetails(
            constraint="MAX_OUTPUT_VOLTS >= MIN_OUTPUT_VOLTS",
            message="Maximum output voltage must be greater than or equal to minimum output voltage.",
        ),
    )
]

def generate_graph_image(rules: list[Rule]):
    builder = GraphBuilder()
    graph_obj = builder.build_graph(rules, genome_type="power_supply")
    graph = graph_obj.graph

    repo_root = Path(__file__).resolve().parent.parent
    output_path = repo_root / "app" / "resources" / "example_rule_graph.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Nodes: {list(graph.nodes())}")
    print(f"Edges: {list(graph.edges())}")

    fig, ax = plt.subplots(figsize=(10, 8), dpi=100) # adjust size as needed
    ax.set_title("Example Validation Rule Graph", fontsize=16, pad=16)
    ax.axis("off")

    pos = nx.spring_layout(graph, seed=42, k=5, iterations=100)

    nx.draw_networkx_nodes(
        graph,
        pos,
        node_size=2000,
        node_color="#E8F0FE",
        edgecolors="#1A73E8",
        linewidths=2,
        ax=ax,
    )

    nx.draw_networkx_labels(
        graph,
        pos,
        font_size=8,
        font_weight="bold",
        ax=ax,
    )

    import matplotlib.patches as mpatches
    
    for source, target in graph.edges():
        x1, y1 = pos[source]
        x2, y2 = pos[target]
        
        dx = x2 - x1
        dy = y2 - y1
        distance = np.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            dx_norm = dx / distance
            dy_norm = dy / distance
            
            shrink = 0.08  # Adjust this value based on node size relative to spacing
            
            start_x = x1 + dx_norm * shrink
            start_y = y1 + dy_norm * shrink
            end_x = x2 - dx_norm * shrink
            end_y = y2 - dy_norm * shrink
            
            arrow = mpatches.FancyArrowPatch(
                (start_x, start_y),
                (end_x, end_y),
                connectionstyle="arc3,rad=0.1",
                arrowstyle="->",
                mutation_scale=40,
                linewidth=3,
                color="#5F6368",
                zorder=10,
            )
            ax.add_patch(arrow)

    edge_labels = {}
    for source, target, data in graph.edges(data=True):
        rule_def = data.get("rule_details")
        if rule_def:
            constraint = rule_def.get("constraint")
            if rule_def.get("condition"):
                label = f"{rule_def.get('condition')}\n{constraint}"
            else:
                label = constraint
            edge_labels[(source, target)] = label

    nx.draw_networkx_edge_labels(
        graph,
        pos,
        edge_labels=edge_labels,
        font_size=7,
        ax=ax,
    )

    fig.tight_layout()
    fig.savefig(output_path, format="png", bbox_inches="tight")
    plt.close(fig)
    print(f"Graph image generated at: {output_path}")


if __name__ == "__main__":
    generate_graph_image(EXAMPLE_RULES)
