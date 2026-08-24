import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. BASE ROAD NETWORK MATRIX
# ==========================================
NODE_NAMES = ["Node_0 (Start)", "Node_1", "Node_2", "Node_3", "Node_4", "Node_5 (End)"]

# Baseline free-flow travel times (minutes)
BASE_COST_MATRIX = np.array([
    [0.0, 12.0, 18.5, np.inf, np.inf, np.inf],
    [12.0, 0.0, 8.2, 15.0, 22.1, np.inf],
    [18.5, 8.2, 0.0, 11.4, np.inf, 28.0],
    [np.inf, 15.0, 11.4, 0.0, 9.3, 14.2],
    [np.inf, 22.1, np.inf, 9.3, 0.0, 7.5],
    [np.inf, np.inf, 28.0, 14.2, 7.5, 0.0]
])


# ==========================================
# 2. DYNAMIC INCIDENT INJECTION
# ==========================================
def apply_traffic_incident(matrix, u, v, congestion_multiplier=4.0):
    """
    Simulates a sudden traffic incident or road bottleneck between node u and node v.
    """
    live_matrix = np.copy(matrix)
    if not np.isinf(live_matrix[u][v]):
        live_matrix[u][v] *= congestion_multiplier
        live_matrix[v][u] *= congestion_multiplier  # Bidirectional road
    return live_matrix


# ==========================================
# 3. QPSO OPTIMIZATION ENGINE
# ==========================================
def evaluate_route(route_order, cost_matrix):
    total_cost = 0.0
    for i in range(len(route_order) - 1):
        u, v = route_order[i], route_order[i + 1]
        cost = cost_matrix[u][v]
        if np.isinf(cost):
            total_cost += 1000.0  # Barrier penalty for non-existent edges
        else:
            total_cost += cost
    return total_cost


def decode_particle_to_route(position, intermediate_nodes, start_node=0, end_node=5):
    sorted_indices = np.argsort(position)
    ordered_intermediates = [intermediate_nodes[i] for i in sorted_indices]
    return [start_node] + ordered_intermediates + [end_node]


def run_qpso_routing(cost_matrix, num_particles=30, max_iter=80):
    start_node = 0
    end_node = cost_matrix.shape[0] - 1
    intermediate_nodes = list(range(1, end_node))
    dim = len(intermediate_nodes)

    # Initialize particle positions in search space [-1, 1]
    X = np.random.uniform(-1.0, 1.0, (num_particles, dim))
    P_best = np.copy(X)
    P_best_scores = np.full(num_particles, np.inf)

    G_best = np.zeros(dim)
    G_best_score = np.inf
    history = []

    # Initial fitness evaluation
    for i in range(num_particles):
        route = decode_particle_to_route(X[i], intermediate_nodes, start_node, end_node)
        score = evaluate_route(route, cost_matrix)
        P_best_scores[i] = score
        if score < G_best_score:
            G_best_score = score
            G_best = np.copy(X[i])

    # Quantum evolutionary cycle
    for t in range(max_iter):
        alpha = 1.0 - (0.5 * t / max_iter)  # Contraction-expansion factor
        mbest = np.mean(P_best, axis=0)  # Mean of all personal bests

        for i in range(num_particles):
            # Local attractor
            phi = np.random.uniform(0, 1, dim)
            p = phi * P_best[i] + (1.0 - phi) * G_best

            # Delta potential well wave equation
            u = np.random.uniform(0, 1, dim)
            sign = np.where(np.random.rand(dim) > 0.5, 1, -1)
            X[i] = p + sign * alpha * np.abs(mbest - X[i]) * np.log(1.0 / (u + 1e-9))

            # Evaluate new position
            route = decode_particle_to_route(X[i], intermediate_nodes, start_node, end_node)
            score = evaluate_route(route, cost_matrix)

            if score < P_best_scores[i]:
                P_best_scores[i] = score
                P_best[i] = np.copy(X[i])
                if score < G_best_score:
                    G_best_score = score
                    G_best = np.copy(X[i])

        history.append(G_best_score)

    best_route = decode_particle_to_route(G_best, intermediate_nodes, start_node, end_node)
    return best_route, G_best_score, history


# ==========================================
# 4. SIMULATION & COMPARISON WORKFLOW
# ==========================================
if __name__ == "__main__":
    np.random.seed(42)

    # Phase 1: Baseline Normal Flow
    print("=== PHASE 1: NORMAL TRAFFIC CONDITIONS ===")
    route_normal, time_normal, hist_normal = run_qpso_routing(BASE_COST_MATRIX)
    path_str_normal = " -> ".join([NODE_NAMES[n] for n in route_normal])
    print(f"Optimal Route : {path_str_normal}")
    print(f"Travel Time   : {time_normal:.2f} mins\n")

    # Phase 2: Traffic Incident (e.g., Heavy Congestion on Edge (3, 5))
    congested_u, congested_v = 3, 5
    congested_matrix = apply_traffic_incident(BASE_COST_MATRIX, congested_u, congested_v, congestion_multiplier=5.0)

    print(f"=== PHASE 2: INCIDENT DETECTED ON ROAD ({NODE_NAMES[congested_u]} <-> {NODE_NAMES[congested_v]}) ===")
    old_route_new_cost = evaluate_route(route_normal, congested_matrix)
    print(f"If vehicle stays on original path, new travel time: {old_route_new_cost:.2f} mins")

    # Phase 3: Dynamic QPSO Re-routing
    route_dynamic, time_dynamic, hist_dynamic = run_qpso_routing(congested_matrix)
    path_str_dynamic = " -> ".join([NODE_NAMES[n] for n in route_dynamic])
    print(f"Re-routed Path: {path_str_dynamic}")
    print(f"New Opt. Time : {time_dynamic:.2f} mins")
    print(f"Time Saved by Re-routing: {old_route_new_cost - time_dynamic:.2f} mins\n")

    # Visualization of Convergence under both states
    plt.figure(figsize=(9, 5))
    plt.plot(hist_normal, label='Normal Traffic QPSO Convergence', color='green', linewidth=2)
    plt.plot(hist_dynamic, label='Post-Incident Dynamic Re-routing Convergence', color='red', linestyle='--',
             linewidth=2)
    plt.title('Dynamic Traffic Re-Routing using QPSO', fontsize=12)
    plt.xlabel('Iteration', fontsize=10)
    plt.ylabel('Route Cost / Travel Time (min)', fontsize=10)
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.show()