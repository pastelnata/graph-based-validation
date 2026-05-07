from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.schemas.rule import Rule, RuleDetails
from app.services.graph.graph_builder import GraphBuilder


RULES = [
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
    ),
    Rule(
        source="MIN_INPUT_CURRENT",
        target="MAX_INPUT_CURRENT",
        rule_details=RuleDetails(
            constraint="MAX_INPUT_CURRENT >= MIN_INPUT_CURRENT",
            message="Maximum input current must be greater than or equal to minimum input current.",
        ),
    ),
    Rule(
        source="MIN_OUTPUT_CURRENT",
        target="MAX_OUTPUT_CURRENT",
        rule_details=RuleDetails(
            constraint="MAX_OUTPUT_CURRENT >= MIN_OUTPUT_CURRENT",
            message="Maximum output current must be greater than or equal to minimum output current.",
        ),
    ),
    Rule(
        source="FORM_FACTOR",
        target="U_HEIGHT",
        rule_details=RuleDetails(
            condition="FORM_FACTOR == 'Rack-mount'",
            constraint="U_HEIGHT != null",
            message="U_HEIGHT is required when FORM_FACTOR is set to Rack-mount.",
        ),
    ),
    Rule(
        source="FORM_FACTOR",
        target="RACK_MOUNTING_POSITION",
        rule_details=RuleDetails(
            condition="FORM_FACTOR == 'Rack-mount'",
            constraint="RACK_MOUNTING_POSITION != null",
            message="RACK_MOUNTING_POSITION must be specified for Rack-mount products.",
        ),
    ),
    Rule(
        source="RACK_MOUNT_PDU_TYPE",
        target="POWER_OUTLET_NUMBERING",
        rule_details=RuleDetails(
            condition="RACK_MOUNT_PDU_TYPE != null",
            constraint="POWER_OUTLET_NUMBERING != null",
            message="Power outlet numbering configuration is required for PDU products.",
        ),
    ),
    Rule(
        source="NUM_PHASES_IN",
        target="NUM_PHASES_OUT",
        rule_details=RuleDetails(
            condition="NUM_PHASES_IN == 1",
            constraint="NUM_PHASES_OUT == 1",
            message="Single phase input typically restricts output to single phase.",
        ),
    ),
    Rule(
        source="MAX_INPUT_VOLTS",
        target="MAX_OUTPUT_VOLTS",
        rule_details=RuleDetails(
            condition="RACK_MOUNT_PDU_TYPE == 'Passive'",
            constraint="MAX_OUTPUT_VOLTS <= MAX_INPUT_VOLTS",
            message="For passive PDUs, output voltage cannot exceed input voltage.",
        ),
    ),
    Rule(
        source="MAX_INPUT_CURRENT",
        target="MAX_OUTPUT_CURRENT",
        rule_details=RuleDetails(
            condition="NUM_PHASES_IN == NUM_PHASES_OUT",
            constraint="MAX_OUTPUT_CURRENT <= MAX_INPUT_CURRENT",
            message="Total output current cannot exceed total input current for non-transforming units.",
        ),
    ),
    Rule(
        source="U_HEIGHT",
        target="HEIGHT",
        rule_details=RuleDetails(
            condition="U_HEIGHT != null",
            constraint="HEIGHT >= (U_HEIGHT * 1.75)",
            message="Physical height must be consistent with the specified U_HEIGHT (1U = 1.75 inches).",
        ),
    ),
    Rule(
        source="NETWORK_PORT_CONFIGURATION",
        target="RACK_MOUNT_PDU_TYPE",
        rule_details=RuleDetails(
            condition="NETWORK_PORT_CONFIGURATION != null",
            constraint="RACK_MOUNT_PDU_TYPE != 'Basic'",
            message="Basic PDUs do not have network port configurations; check if PDU type should be Monitored or Switched.",
        ),
    ),
]


def generate_graph_image(rules: list[Rule]):
    builder = GraphBuilder()
    graph_obj = builder.build_graph(rules)
    graph = graph_obj.graph
    
    repo_root = Path(__file__).resolve().parent.parent
    output_path = repo_root / "app" / "resources" / "example_rule_graph.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Nodes: {list(graph.nodes())}")
    print(f"Edges: {list(graph.edges())}")
    
    fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
    ax.set_title("Example Validation Rule Graph", fontsize=16, pad=16)
    ax.axis("off")
    
    import networkx as nx
    pos = nx.spring_layout(graph, seed=42, k=2, iterations=50)
    
    # Draw nodes
    nx.draw_networkx_nodes(
        graph,
        pos,
        node_size=2000,
        node_color="#E8F0FE",
        edgecolors="#1A73E8",
        linewidths=1.8,
        ax=ax,
    )
    
    # Draw edges explicitly
    nx.draw_networkx_edges(
        graph,
        pos,
        edge_color="#5F6368",
        width=2,
        arrows=True,
        arrowsize=20,
        arrowstyle="->",
        ax=ax,
    )
    
    # Draw labels
    nx.draw_networkx_labels(
        graph,
        pos,
        font_size=9,
        font_weight="bold",
        ax=ax,
    )
    
    # Draw edge labels (constraints)
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
    generate_graph_image(RULES)
