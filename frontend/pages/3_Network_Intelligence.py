"""PROVISYN — Network Intelligence (Page 3).
Graph topology, PageRank centrality, betweenness bottlenecks, and Louvain community detection.
Ported from Supply Network page and NetworkX analytics notebook.
"""
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from frontend.components.styles import (
    inject_provisyn_styles,
    COLOR_CANVAS,
    COLOR_SURFACE,
    COLOR_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_RISK_HEALTHY,
    COLOR_RISK_WARNING,
    COLOR_RISK_HIGH,
    COLOR_RISK_CRITICAL,
)
from frontend.components import render_kpi
from frontend.utils.sidebar import render_sidebar
from backend.data.repository import get_repository
from backend.data.generator import seed_database
from backend.graph.analytics import (
    build_supply_chain_graph,
    compute_pagerank,
    compute_betweenness_centrality,
    compute_louvain_communities,
)

st.set_page_config(page_title="PROVISYN — Network Intelligence", layout="wide")
inject_provisyn_styles(st)
render_sidebar(current_page="Network Intelligence")

st.markdown("""
<div style="border-bottom: 1px solid #3A3A3C; padding-bottom: 0.75rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: baseline;">
    <div>
        <h1 style="margin: 0; font-size: 1.75rem;">03 NETWORK INTELLIGENCE</h1>
        <div style="color: #9C9A96; font-size: 0.85rem; margin-top: 4px;">Graph topology, PageRank node influence, betweenness bottlenecks, and Louvain community clustering</div>
    </div>
    <div>
        <span class="data-label">GRAPH ENGINE: NETWORKX</span>
    </div>
</div>
""", unsafe_allow_html=True)

repo = get_repository()
vendors_df = repo.get_vendors()
if vendors_df.empty:
    seed_database(repo, seed=42)
    vendors_df = repo.get_vendors()

materials_df = repo.get_materials()
regions_df = repo.get_regions()
po_df = repo.get_purchase_orders()
bom_df = repo.get_bill_of_materials()

@st.cache_data(ttl=600)
def load_graph_metrics():
    G = build_supply_chain_graph(vendors_df, materials_df, regions_df, po_df, bom_df)
    pr = compute_pagerank(G)
    bc = compute_betweenness_centrality(G)
    comm = compute_louvain_communities(G)
    return G, pr, bc, comm

G, pr, bc, comm = load_graph_metrics()

# KPI Header
num_nodes = G.number_of_nodes()
num_edges = G.number_of_edges()
density = nx.density(G)
num_comm = len(set(comm.values())) if comm else 1

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_kpi("Network Nodes", f"{num_nodes}", subtext="Vendors, Materials, Regions", data_label="observed")
with k2:
    render_kpi("Active Edges", f"{num_edges}", subtext="Supplies, BOM, Located-in", data_label="observed")
with k3:
    render_kpi("Network Density", f"{density:.4f}", subtext="Graph connectivity ratio", data_label="calculated")
with k4:
    render_kpi("Supply Clusters", f"{num_comm} Communities", subtext="Louvain modularity partition", data_label="calculated")

st.markdown("""<div style="margin-top: 1rem;"></div>""", unsafe_allow_html=True)

# Visualization and Top Influencers
col_graph, col_stats = st.columns([3, 2])

with col_graph:
    st.markdown("### Interactive Supply Chain Graph Topology")
    
    # Subgraph for clean rendering (e.g. top 60 nodes by PageRank)
    top_nodes = sorted(pr.keys(), key=lambda x: pr[x], reverse=True)[:65]
    subG = G.subgraph(top_nodes)
    pos = nx.spring_layout(subG, seed=42, k=0.35)

    # Edge traces
    edge_x = []
    edge_y = []
    for u, v in subG.edges():
        if u in pos and v in pos:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color=COLOR_BORDER),
        hoverinfo='none',
        mode='lines'
    )

    # Node traces by type (Flat colors, NO BLUE)
    # Vendor: Muted Green (#5B8266)
    # Material: Amber (#C99A3B)
    # Region: Orange (#C97A3B)
    TYPE_COLORS = {
        "vendor": COLOR_RISK_HEALTHY,
        "material": COLOR_RISK_WARNING,
        "region": COLOR_RISK_HIGH
    }

    node_traces = []
    for ntype, color in TYPE_COLORS.items():
        nx_coords = []
        ny_coords = []
        text_labels = []
        node_sizes = []
        for n in subG.nodes():
            if subG.nodes[n].get("node_type") == ntype:
                x, y = pos[n]
                nx_coords.append(x)
                ny_coords.append(y)
                name = subG.nodes[n].get("name", subG.nodes[n].get("description", n))
                node_pr = pr.get(n, 0.0)
                node_bc = bc.get(n, 0.0)
                text_labels.append(f"<b>{name}</b><br>Type: {ntype.upper()}<br>PageRank: {node_pr:.5f}<br>Betweenness: {node_bc:.5f}")
                node_sizes.append(max(8, min(24, int(node_pr * 800) + 10)))

        if nx_coords:
            node_traces.append(go.Scatter(
                x=nx_coords, y=ny_coords,
                mode='markers',
                hoverinfo='text',
                text=text_labels,
                name=ntype.upper(),
                marker=dict(
                    color=color,
                    size=node_sizes,
                    line=dict(width=1.5, color=COLOR_TEXT_PRIMARY)
                )
            ))

    fig = go.Figure(data=[edge_trace] + node_traces)
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=COLOR_SURFACE,
        showlegend=True,
        legend=dict(font=dict(color=COLOR_TEXT_PRIMARY), orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=480,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )
    st.plotly_chart(fig, use_container_width=True)

with col_stats:
    st.markdown("### Top Bottlenecks by Centrality")
    
    # Centrality summary table
    cent_rows = []
    for node in sorted(pr.keys(), key=lambda x: pr[x], reverse=True)[:15]:
        n_data = G.nodes[node]
        name = n_data.get("name", n_data.get("description", node))
        ntype = n_data.get("node_type", "unknown")
        cent_rows.append({
            "Node ID": node,
            "Type": ntype.upper(),
            "Name": name,
            "PageRank": f"{pr.get(node, 0):.5f}",
            "Betweenness": f"{bc.get(node, 0):.5f}",
            "Cluster": comm.get(node, -1)
        })
    df_cent = pd.DataFrame(cent_rows)
    st.dataframe(df_cent, use_container_width=True, hide_index=True)
