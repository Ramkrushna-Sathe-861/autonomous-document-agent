from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx


def build_graph_image(output_path: str = "output/graph.png") -> Path:
    graph_img = Path(output_path)
    graph_img.parent.mkdir(parents=True, exist_ok=True)

    graph = nx.DiGraph()
    graph.add_nodes_from(
        [
            ("template_lookup", {"label": "Template Lookup"}),
            ("planner", {"label": "Planner Agent"}),
            ("executor", {"label": "Executor Agent"}),
            ("validate", {"label": "Validation"}),
            ("reflector", {"label": "Reflection Agent"}),
            ("revise", {"label": "Revise"}),
            ("render_document", {"label": "Render Document"}),
            ("render", {"label": "Render Response"}),
        ]
    )
    graph.add_edges_from(
        [
            ("template_lookup", "planner"),
            ("planner", "executor"),
            ("executor", "validate"),
            ("validate", "reflector"),
            ("reflector", "revise"),
            ("reflector", "render"),
            ("revise", "validate"),
            ("render_document", "render"),
        ]
    )

    pos = nx.spring_layout(graph, seed=42)
    plt.figure(figsize=(10, 5))
    nx.draw_networkx_nodes(graph, pos, node_color="#dbeafe", node_size=2200)
    nx.draw_networkx_edges(graph, pos, arrows=True, arrowstyle="->", arrowsize=16)
    nx.draw_networkx_labels(graph, pos, labels={n: d["label"] for n, d in graph.nodes(data=True)}, font_size=9)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(graph_img, dpi=200)
    plt.close()

    return graph_img


if __name__ == "__main__":
    path = build_graph_image()
    print(path)
