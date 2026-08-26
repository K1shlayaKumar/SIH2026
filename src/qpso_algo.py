import math
import heapq
import random
import numpy as np


# ============================================================
# UTILITIES & DISTANCE MATH
# ============================================================
def calculate_dist(p1, p2):
    """Calculates Euclidean distance between two coordinate points."""
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def get_shortest_path(graph, start, target):
    """Standard Dijkstra fallback."""
    queue = [(0, start, [])]
    visited = set()
    while queue:
        cost, cur, path = heapq.heappop(queue)
        if cur in visited:
            continue
        path = path + [cur]
        visited.add(cur)
        if cur == target:
            return path
        for neighbor, weight in graph[cur].items():
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor, path))
    return [start, target]


def get_noisy_shortest_path(noisy_graph, start, target):
    """Exploration routing with randomized dynamic weights."""
    queue = [(0, start, [])]
    visited = set()
    while queue:
        cost, cur, path = heapq.heappop(queue)
        if cur in visited:
            continue
        path = path + [cur]
        visited.add(cur)
        if cur == target:
            return path
        for neighbor, weight in noisy_graph[cur].items():
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor, path))
    return [start, target]


# ============================================================
# 1. LOWER LEVEL: VEHICLE ROUTING WITH DYNAMIC SIGNAL COST
# ============================================================
def metaheuristic_qpso_route(start, target, traffic_lights_state, points, roads):
    """Calculates optimal path considering current signal phases and highway hierarchy."""
    if start == target:
        return [start]
    candidate_paths = []

    # 1. Candidate exploration
    for _ in range(12):
        noisy_graph = {node: {} for node in points}
        for u, v in roads:
            d = calculate_dist(points[u], points[v])
            noise = random.uniform(0.92, 1.08)

            # Prefer major arterial rings and corridors
            is_main_road = (u in ["J13", "J14", "J15", "J16", "J17", "J18", "J19", "J20"] or
                            v in ["J13", "J14", "J15", "J16", "J17", "J18", "J19", "J20"])
            hierarchy_penalty = 1.0 if is_main_road else 1.35

            signal_delay = 0.0
            if v in traffic_lights_state:
                if traffic_lights_state[v]["state"] == "RED":
                    signal_delay = 70.0
                else:
                    signal_delay = -20.0

            weight = max(1.0, (d * noise * hierarchy_penalty) + signal_delay)
            noisy_graph[u][v] = weight
            noisy_graph[v][u] = weight

        path = get_noisy_shortest_path(noisy_graph, start, target)
        if path and path not in candidate_paths:
            candidate_paths.append(path)

    if not candidate_paths:
        graph = {node: {} for node in points}
        for u, v in roads:
            d = calculate_dist(points[u], points[v])
            graph[u][v] = graph[v][u] = d
        return get_shortest_path(graph, start, target)

        # 2. QPSO Swarm Selection
    num_particles, dim = 10, 1
    X = np.random.uniform(0, len(candidate_paths) - 1, (num_particles, dim))
    P_best, P_scores = np.copy(X), np.full(num_particles, np.inf)
    G_best, G_best_score = np.zeros(dim), np.inf

    def evaluate_path(idx):
        path = candidate_paths[int(round(idx[0]))]
        cost = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            cost += calculate_dist(points[u], points[v])
            if v in traffic_lights_state:
                if traffic_lights_state[v]["state"] == "RED":
                    cost += 70.0
                else:
                    cost -= 20.0
        return cost

    for t in range(15):
        mbest = np.mean(P_best, axis=0)
        alpha = 1.0 - (0.5 * t / 15)
        for i in range(num_particles):
            phi, u = np.random.uniform(0, 1, dim), np.random.uniform(0, 1, dim)
            p = phi * P_best[i] + (1.0 - phi) * G_best
            sign = np.where(np.random.rand(dim) > 0.5, 1, -1)
            X[i] = np.clip(p + sign * alpha * np.abs(mbest - X[i]) * np.log(1.0 / (u + 1e-9)), 0,
                           len(candidate_paths) - 1)

            score = evaluate_path(X[i])
            if score < P_scores[i]:
                P_scores[i], P_best[i] = score, np.copy(X[i])
                if score < G_best_score:
                    G_best_score, G_best = score, np.copy(X[i])

    return candidate_paths[int(round(G_best[0]))]


# ============================================================
# 2. UPPER LEVEL: BI-LEVEL PREDICTIVE SIGNAL OPTIMIZATION
# ============================================================
def qpso_optimize_traffic_lights(vehicles, traffic_lights, points):
    """Optimizes signal states using real-time queue demand and multi-step vehicle path intent."""
    light_keys = list(traffic_lights.keys())
    dim = len(light_keys)
    if dim == 0:
        return np.array([])

    num_particles = 15
    max_iter = 20

    X = np.random.uniform(-1.0, 1.0, (num_particles, dim))
    P_best, P_scores = np.copy(X), np.full(num_particles, np.inf)
    G_best, G_best_score = np.zeros(dim), np.inf

    def evaluate_signals(state):
        cost = 0.0

        # 1. Total active green phases cost (prevents all-green deadlocks)
        num_green = sum(1 for val in state if val > 0)
        cost += num_green * 20.0

        # 2. Green Wave axis alignment reward
        green_nodes = [light_keys[i] for i, val in enumerate(state) if val > 0]
        for i in range(len(green_nodes)):
            for j in range(i + 1, len(green_nodes)):
                n1, n2 = green_nodes[i], green_nodes[j]
                p1, p2 = points[n1], points[n2]
                if p1[0] == p2[0] or p1[1] == p2[1]:
                    cost -= 15.0

        # 3. Bi-level feedback: immediate queue + upcoming path intent
        for v in vehicles:
            if not v.active or not v.path or v.segment_idx >= len(v.path) - 1:
                continue

            # Immediate approaching junction
            if v.next_node in light_keys:
                idx = light_keys.index(v.next_node)
                is_green = state[idx] > 0
                dist_to_junction = (1.0 - v.progress) * calculate_dist(points[v.curr_node], points[v.next_node])

                if not is_green:
                    if v.v < 0.05 and dist_to_junction < 15.0:
                        cost += 550.0 / (dist_to_junction + 1.0)
                    else:
                        cost += 120.0 / (dist_to_junction + 1.0)
                else:
                    if v.v > 0.12:
                        cost -= 140.0 / (dist_to_junction + 1.0)

            # Predictive ETA for downstream junctions along the vehicle's planned path
            future_nodes = v.path[v.segment_idx + 1:v.segment_idx + 4]
            for hop, node_name in enumerate(future_nodes, start=1):
                if node_name in light_keys:
                    f_idx = light_keys.index(node_name)
                    if state[f_idx] > 0:
                        # Reward green corridors for high-density routes
                        cost -= 25.0 / hop

        return cost

    for t in range(max_iter):
        mbest = np.mean(P_best, axis=0)
        alpha = 1.0 - (0.6 * t / max_iter)

        for i in range(num_particles):
            phi, u = np.random.uniform(0, 1, dim), np.random.uniform(0, 1, dim)
            p = phi * P_best[i] + (1.0 - phi) * G_best
            sign = np.where(np.random.rand(dim) > 0.5, 1, -1)
            X[i] = np.clip(p + sign * alpha * np.abs(mbest - X[i]) * np.log(1.0 / (u + 1e-9)), -1.0, 1.0)

            score = evaluate_signals(X[i])
            if score < P_scores[i]:
                P_scores[i], P_best[i] = score, np.copy(X[i])
                if score < G_best_score:
                    G_best_score, G_best = score, np.copy(X[i])

    return G_best