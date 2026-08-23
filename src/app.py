import streamlit as st
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import time

# Set Streamlit Page Config test
st.set_page_config(page_title="ITS - QPSO Route Optimizer", layout="wide")

st.title("🚦 Intelligent Transportation System (ITS)")
st.markdown("**Multi-Objective Traffic Route Optimization via Quantum-Behaved PSO (QPSO)**")

# ==========================================
# 1. NETWORK TOPOLOGY DEFINITION
# ==========================================
NUM_NODES = 6
NODE_NAMES = [f"Node_{i}" for i in range(NUM_NODES)]

T0_MATRIX = np.array([
    [0.0, 10.0, 15.0, np.inf, np.inf, np.inf],
    [10.0, 0.0, 5.0, 12.0, 18.0, np.inf],
    [15.0, 5.0, 0.0, 8.0, np.inf, 20.0],
    [np.inf, 12.0, 8.0, 0.0, 6.0, 10.0],
    [np.inf, 18.0, np.inf, 6.0, 0.0, 5.0],
    [np.inf, np.inf, 20.0, 10.0, 5.0, 0.0]
])

DIST_MATRIX = np.array([
    [0.0, 12.0, 18.5, np.inf, np.inf, np.inf],
    [12.0, 0.0, 8.2, 15.0, 22.1, np.inf],
    [18.5, 8.2, 0.0, 11.4, np.inf, 28.0],
    [np.inf, 15.0, 11.4, 0.0, 9.3, 14.2],
    [np.inf, 22.1, np.inf, 9.3, 0.0, 7.5],
    [np.inf, np.inf, 28.0, 14.2, 7.5, 0.0]
])

BASE_CAPACITY = np.array([
    [np.inf, 15, 25, np.inf, np.inf, np.inf],
    [15, np.inf, 10, 12, 15, np.inf],
    [25, 10, np.inf, 20, np.inf, 15],
    [np.inf, 12, 20, np.inf, 20, 20],
    [np.inf, 15, np.inf, 20, np.inf, 25],
    [np.inf, np.inf, 15, 20, 25, np.inf]
])

# Fixed spatial coordinates for 2D network rendering
NODE_POSITIONS = {
    0: (0.0, 1.0),
    1: (1.5, 2.0),
    2: (1.5, 0.0),
    3: (3.0, 1.5),
    4: (3.0, 0.0),
    5: (4.5, 1.0)
}

# ==========================================
# 2. SIDEBAR CONTROLS & HYPERPARAMETERS
# ==========================================
st.sidebar.header("🕹️ Simulation Controls")

st.sidebar.subheader("1. Multi-OD Demand (Fleet Volume)")
demand_0_5 = st.sidebar.slider("Vehicles: Node 0 ➔ Node 5", 5, 50, 25)
demand_1_4 = st.sidebar.slider("Vehicles: Node 1 ➔ Node 4", 0, 30, 15)
demand_2_5 = st.sidebar.slider("Vehicles: Node 2 ➔ Node 5", 0, 30, 10)

od_demand = [
    (0, 5, demand_0_5),
    (1, 4, demand_1_4),
    (2, 5, demand_2_5)
]
total_vehicles = sum(d[2] for d in od_demand)

st.sidebar.subheader("2. Multi-Objective Weights")
w_time = st.sidebar.slider("Time Weight (w1)", 0.0, 1.0, 0.7, 0.05)
w_fuel = round(1.0 - w_time, 2)
st.sidebar.info(f"Fuel Weight (w2): **{w_fuel}** (Sum = 1.0)")

st.sidebar.subheader("3. Live Road Incident Simulation")
incident_active = st.sidebar.checkbox("Trigger Road Bottleneck / Accident")
incident_road = st.sidebar.selectbox("Select Blocked Segment",
                                     ["Node 3 ➔ Node 5", "Node 1 ➔ Node 2", "Node 2 ➔ Node 3"])
incident_mult = st.sidebar.slider("Congestion Multiplier", 2.0, 8.0, 4.0) if incident_active else 1.0


# ==========================================
# 3. CORE ROUTING & OPTIMIZATION LOGIC
# ==========================================
def get_live_metrics(u, v, flow, live_t0, cap_mat):
    t0, dist, cap = live_t0[u][v], DIST_MATRIX[u][v], cap_mat[u][v]
    live_time = t0 * (1.0 + 0.15 * (flow / cap) ** 4)
    live_fuel = (dist * 0.08) * (1.0 + 0.2 * (flow / cap))
    return live_time, live_fuel


def evaluate_route(route, edge_flow, live_t0, cap_mat, wt, wf):
    total_time, total_fuel = 0.0, 0.0
    for i in range(len(route) - 1):
        u, v = route[i], route[i + 1]
        if np.isinf(live_t0[u][v]):
            return float('inf'), 0.0, 0.0
        l_time, l_fuel = get_live_metrics(u, v, edge_flow[u][v], live_t0, cap_mat)
        total_time += l_time
        total_fuel += l_fuel
    cost = (wt * total_time) + (wf * total_fuel * 10)
    return cost, total_time, total_fuel


def decode_particle(pos, start, end):
    intermediates = [n for n in range(NUM_NODES) if n != start and n != end]
    sorted_idx = np.argsort(pos)
    return [start] + [intermediates[i] for i in sorted_idx] + [end]


def optimize_pso(edge_flow, start, end, live_t0, cap_mat, wt, wf, qpso=False, particles=25, max_iter=30):
    dim = NUM_NODES - 2
    X = np.random.uniform(-1.0, 1.0, (particles, dim))
    V = np.random.uniform(-0.5, 0.5, (particles, dim))
    P_best, P_scores = np.copy(X), np.full(particles, np.inf)
    G_best, G_best_score = np.zeros(dim), np.inf

    for t in range(max_iter):
        mbest = np.mean(P_best, axis=0) if qpso else None
        alpha = 1.0 - (0.5 * t / max_iter) if qpso else None

        for i in range(particles):
            if qpso:
                phi, u = np.random.uniform(0, 1, dim), np.random.uniform(0, 1, dim)
                p = phi * P_best[i] + (1.0 - phi) * G_best
                sign = np.where(np.random.rand(dim) > 0.5, 1, -1)
                X[i] = p + sign * alpha * np.abs(mbest - X[i]) * np.log(1.0 / (u + 1e-9))
            else:
                r1, r2 = np.random.rand(dim), np.random.rand(dim)
                V[i] = 0.7 * V[i] + 1.5 * r1 * (P_best[i] - X[i]) + 1.5 * r2 * (G_best - X[i])
                X[i] += V[i]

            route = decode_particle(X[i], start, end)
            cost, _, _ = evaluate_route(route, edge_flow, live_t0, cap_mat, wt, wf)
            if cost < P_scores[i]:
                P_scores[i], P_best[i] = cost, np.copy(X[i])
                if cost < G_best_score:
                    G_best_score, G_best = cost, np.copy(X[i])

    return decode_particle(G_best, start, end)


def dijkstra_route(edge_flow, start, end, live_t0, cap_mat, wt, wf):
    dist = {i: float('inf') for i in range(NUM_NODES)}
    prev = {i: None for i in range(NUM_NODES)}
    dist[start] = 0
    unvisited = list(range(NUM_NODES))

    while unvisited:
        curr = min(unvisited, key=lambda n: dist[n])
        if curr == end or dist[curr] == float('inf'):
            break
        unvisited.remove(curr)

        for nxt in range(NUM_NODES):
            if not np.isinf(live_t0[curr][nxt]) and nxt in unvisited:
                cost, _, _ = evaluate_route([curr, nxt], edge_flow, live_t0, cap_mat, wt, wf)
                if dist[curr] + cost < dist[nxt]:
                    dist[nxt] = dist[curr] + cost
                    prev[nxt] = curr

    path, curr = [], end
    while curr is not None:
        path.insert(0, curr)
        curr = prev[curr]
    return path


# ==========================================
# 4. SIMULATION EXECUTION
# ==========================================
def run_fleet_simulation(algo_name, live_t0, cap_mat, wt, wf):
    edge_flow = np.zeros((NUM_NODES, NUM_NODES))
    total_time, total_fuel = 0.0, 0.0
    start_cpu = time.time()

    for orig, dest, count in od_demand:
        for _ in range(count):
            if algo_name == "Dijkstra":
                r = dijkstra_route(edge_flow, orig, dest, live_t0, cap_mat, wt, wf)
            elif algo_name == "Standard PSO":
                r = optimize_pso(edge_flow, orig, dest, live_t0, cap_mat, wt, wf, qpso=False)
            else:  # QPSO
                r = optimize_pso(edge_flow, orig, dest, live_t0, cap_mat, wt, wf, qpso=True)

            _, v_time, v_fuel = evaluate_route(r, edge_flow, live_t0, cap_mat, wt, wf)
            total_time += v_time
            total_fuel += v_fuel

            for i in range(len(r) - 1):
                u, v = r[i], r[i + 1]
                edge_flow[u][v] += 1
                edge_flow[v][u] += 1

    cpu_ms = (time.time() - start_cpu) * 1000
    return {
        "Avg Time (min)": round(total_time / total_vehicles, 2),
        "Avg Fuel (L)": round(total_fuel / total_vehicles, 2),
        "CPU Time (ms)": round(cpu_ms, 1),
        "Final Flow": edge_flow
    }


# Build active network state
live_t0 = np.copy(T0_MATRIX)
if incident_active:
    road_map = {"Node 3 ➔ Node 5": (3, 5), "Node 1 ➔ Node 2": (1, 2), "Node 2 ➔ Node 3": (2, 3)}
    iu, iv = road_map[incident_road]
    live_t0[iu][iv] *= incident_mult
    live_t0[iv][iu] *= incident_mult

# Run comparison
np.random.seed(42)
res_dijkstra = run_fleet_simulation("Dijkstra", live_t0, BASE_CAPACITY, w_time, w_fuel)
res_pso = run_fleet_simulation("Standard PSO", live_t0, BASE_CAPACITY, w_time, w_fuel)
res_qpso = run_fleet_simulation("QPSO", live_t0, BASE_CAPACITY, w_time, w_fuel)

# ==========================================
# 5. DASHBOARD LAYOUT & VISUALIZATIONS
# ==========================================
col1, col2, col3 = st.columns(3)
col1.metric("QPSO Avg Commute Time", f"{res_qpso['Avg Time (min)']} min",
            delta=f"{round(res_dijkstra['Avg Time (min)'] - res_qpso['Avg Time (min)'], 2)} min vs Dijkstra",
            delta_color="inverse")
col2.metric("QPSO Avg Fuel Consumed", f"{res_qpso['Avg Fuel (L)']} L",
            delta=f"{round(res_dijkstra['Avg Fuel (L)'] - res_qpso['Avg Fuel (L)'], 2)} L vs Dijkstra",
            delta_color="inverse")
col3.metric("Total Fleet Volume", f"{total_vehicles} Vehicles")

st.divider()

# Benchmark Summary Table
st.subheader("📊 Comparative Algorithm Benchmark")
df_results = pd.DataFrame([
    {"Algorithm": "Dijkstra (Greedy)", **{k: v for k, v in res_dijkstra.items() if k != 'Final Flow'}},
    {"Algorithm": "Standard PSO", **{k: v for k, v in res_pso.items() if k != 'Final Flow'}},
    {"Algorithm": "Quantum PSO (QPSO)", **{k: v for k, v in res_qpso.items() if k != 'Final Flow'}}
])
st.dataframe(df_results, use_container_width=True)

# Visual Network Graph Representation
st.subheader("🗺️ Live Road Congestion Heatmap (QPSO Distributed Load)")

fig, ax = plt.subplots(figsize=(8, 4.5))
G = nx.Graph()

for i in range(NUM_NODES):
    G.add_node(i, pos=NODE_POSITIONS[i])

edge_colors = []
edge_widths = []
flow_data = res_qpso["Final Flow"]

for u in range(NUM_NODES):
    for v in range(u + 1, NUM_NODES):
        if not np.isinf(T0_MATRIX[u][v]):
            G.add_edge(u, v)
            volume = flow_data[u][v]
            cap = BASE_CAPACITY[u][v]
            ratio = volume / cap

            # Color coding: Green (Clear) -> Orange (Moderate) -> Red (Saturated)
            if ratio < 0.6:
                edge_colors.append('#2ecc71')
            elif ratio < 1.0:
                edge_colors.append('#f39c12')
            else:
                edge_colors.append('#e74c3c')

            edge_widths.append(max(1.5, ratio * 4.5))

pos = nx.get_node_attributes(G, 'pos')
nx.draw_networkx_nodes(G, pos, ax=ax, node_color='#34495e', node_size=700)
nx.draw_networkx_labels(G, pos, ax=ax, font_color='white', font_weight='bold', font_size=9)
nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_colors, width=edge_widths)

# Draw edge labels (Volume / Capacity)
edge_labels = {(u, v): f"{int(flow_data[u][v])}/{int(BASE_CAPACITY[u][v])}" for u, v in G.edges()}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax, font_size=8)

ax.set_title("Edge Labels: [Assigned Vehicles / Road Capacity] | Green: Flowing, Orange: Busy, Red: Congested",
             fontsize=9)
ax.axis('off')
st.pyplot(fig)