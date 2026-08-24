import streamlit as st
import osmnx as ox
import networkx as nx
import numpy as np
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="ITS - Real-World Map QPSO", layout="wide")

st.title("🌍 Real-World Intelligent Traffic Optimizer")
st.markdown("**Powered by OpenStreetMap (OSM) & Quantum PSO**")


# ==========================================
# 1. FETCH & PROCESS REAL-WORLD MAP DATA
# ==========================================
@st.cache_resource(show_spinner="Fetching map from OpenStreetMap...")
def load_and_process_map(location="Times Square, New York, USA", radius=400):
    # 1. Download drive network
    G = ox.graph_from_address(location, dist=radius, network_type='drive')
    # 2. Keep only strongly connected nodes (using stable networkx)
    largest_cc = max(nx.strongly_connected_components(G), key=len)
    G = G.subgraph(largest_cc).copy()

    # 3. Map OSM IDs (large integers) to consecutive indices (0 to N-1)
    osm_nodes = list(G.nodes())
    node_to_idx = {osm_nodes[i]: i for i in range(len(osm_nodes))}
    idx_to_node = {i: osm_nodes[i] for i in range(len(osm_nodes))}

    N = len(osm_nodes)

    # 4. Build our T0 and Capacity matrices
    t0_matrix = np.full((N, N), np.inf)
    capacity_matrix = np.full((N, N), 1.0)  # Prevent division by zero

    for u, v, data in G.edges(data=True):
        u_idx, v_idx = node_to_idx[u], node_to_idx[v]

        # Get length (meters) and speed limit (km/h)
        length = data.get('length', 100)
        speed_str = data.get('maxspeed', '40')
        if isinstance(speed_str, list): speed_str = speed_str[0]
        try:
            speed_kmh = float(speed_str)
        except:
            speed_kmh = 40.0

        # Time = Distance / Speed (converted to minutes)
        speed_mpm = (speed_kmh * 1000) / 60.0
        travel_time = length / speed_mpm

        # Assume number of lanes for capacity (default 1 if missing)
        lanes = data.get('lanes', 1)
        if isinstance(lanes, list):
            lanes = int(lanes[0])
        else:
            lanes = int(lanes)

        t0_matrix[u_idx][v_idx] = travel_time
        capacity_matrix[u_idx][v_idx] = lanes * 15  # Approx 15 cars per lane segment

    return G, N, t0_matrix, capacity_matrix, idx_to_node


# ==========================================
# 2. SIDEBAR & USER CONTROLS
# ==========================================
st.sidebar.header("📍 Map Settings")
# You can change this to "Connaught Place, New Delhi", "Stanford University", etc.
city_input = st.sidebar.text_input("Enter City/Landmark", "Times Square, New York")
radius_input = st.sidebar.slider("Search Radius (meters)", 200, 800, 400, step=100)
st.sidebar.caption("Keep radius < 600m to ensure QPSO runs fast (under 40 nodes).")

G, num_nodes, T0, CAP, idx_map = load_and_process_map(city_input, radius_input)

st.sidebar.header("🚦 Live Traffic Simulation")
trigger_incident = st.sidebar.checkbox("Simulate Severe Traffic Jam")
congestion_multiplier = st.sidebar.slider("Jam Multiplier", 2.0, 10.0, 5.0) if trigger_incident else 1.0

# Select Start and End nodes randomly, but keep them consistent unless graph changes
start_idx = 0
end_idx = num_nodes - 1


# ==========================================
# 3. QPSO ENGINE ADAPTED FOR REAL MAPS
# ==========================================
def decode_particle(pos, start, end):
    intermediates = [n for n in range(num_nodes) if n != start and n != end]
    sorted_idx = np.argsort(pos)
    return [start] + [intermediates[i] for i in sorted_idx] + [end]


def evaluate_route(route, live_t0):
    cost = 0.0
    for i in range(len(route) - 1):
        u, v = route[i], route[i + 1]
        if np.isinf(live_t0[u][v]):
            return float('inf')
        cost += live_t0[u][v]
    return cost


def run_qpso(live_t0, start, end, particles=40, max_iter=50):
    dim = num_nodes - 2
    if dim <= 0: return [start, end], evaluate_route([start, end], live_t0)

    X = np.random.uniform(-1.0, 1.0, (particles, dim))
    P_best = np.copy(X)
    P_scores = np.full(particles, np.inf)
    G_best, G_best_score = np.zeros(dim), np.inf

    for t in range(max_iter):
        alpha = 1.0 - (0.5 * t / max_iter)
        mbest = np.mean(P_best, axis=0)

        for i in range(particles):
            phi, u = np.random.uniform(0, 1, dim), np.random.uniform(0, 1, dim)
            p = phi * P_best[i] + (1.0 - phi) * G_best
            sign = np.where(np.random.rand(dim) > 0.5, 1, -1)
            X[i] = p + sign * alpha * np.abs(mbest - X[i]) * np.log(1.0 / (u + 1e-9))

            r = decode_particle(X[i], start, end)
            cost = evaluate_route(r, live_t0)
            if cost < P_scores[i]:
                P_scores[i], P_best[i] = cost, np.copy(X[i])
                if cost < G_best_score:
                    G_best_score, G_best = cost, np.copy(X[i])

    return decode_particle(G_best, start, end), G_best_score


# ==========================================
# 4. EXECUTION & MAP RENDERING
# ==========================================
# Baseline Normal Flow
normal_route, normal_time = run_qpso(T0, start_idx, end_idx)

# Apply Incident (Congest the middle segment of the normal route)
live_t0 = np.copy(T0)
incident_u, incident_v = None, None
if trigger_incident and len(normal_route) > 2:
    mid_idx = len(normal_route) // 2
    incident_u, incident_v = normal_route[mid_idx - 1], normal_route[mid_idx]
    live_t0[incident_u][incident_v] *= congestion_multiplier

# Run Re-routing
active_route, active_time = run_qpso(live_t0, start_idx, end_idx)

col1, col2, col3 = st.columns(3)
col1.metric("Total Intersections (Nodes)", num_nodes)
col2.metric("Optimal Travel Time", f"{active_time:.2f} mins",
            delta=f"{active_time - normal_time:.2f} min delay" if trigger_incident else "Normal Flow",
            delta_color="inverse")
col3.metric("Algorithm Used", "Quantum PSO")

st.divider()

# Draw Folium Map
center_lat = np.mean([G.nodes[n]['y'] for n in G.nodes])
center_lon = np.mean([G.nodes[n]['x'] for n in G.nodes])
m = folium.Map(location=[center_lat, center_lon], zoom_start=15, tiles="CartoDB positron")

# Draw the optimal route in Blue
osm_route = [idx_map[n] for n in active_route]
route_coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in osm_route]
folium.PolyLine(route_coords, color="#3498db", weight=6, opacity=0.8).add_to(m)

# Highlight Incident in Red
if trigger_incident and incident_u is not None:
    inc_u_osm, inc_v_osm = idx_map[incident_u], idx_map[incident_v]
    inc_coords = [(G.nodes[inc_u_osm]['y'], G.nodes[inc_u_osm]['x']),
                  (G.nodes[inc_v_osm]['y'], G.nodes[inc_v_osm]['x'])]
    folium.PolyLine(inc_coords, color="#e74c3c", weight=8, opacity=1.0).add_to(m)

    # Add accident marker
    folium.Marker(inc_coords[0], popup="Severe Congestion", icon=folium.Icon(color="red", icon="info-sign")).add_to(m)

# Markers for Start and End
folium.Marker(route_coords[0], popup="Origin", icon=folium.Icon(color="green", icon="play")).add_to(m)
folium.Marker(route_coords[-1], popup="Destination", icon=folium.Icon(color="black", icon="flag")).add_to(m)

st_folium(m, width=1200, height=500)