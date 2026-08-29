import math
import heapq
import random
import numpy as np


# ============================================================
# UTILITIES & DISTANCE MATH
# ============================================================
def calculate_dist(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])


def get_shortest_path(graph, start, target):
    queue = [(0, start, [])]
    visited = set()
    while queue:
        cost, cur, path = heapq.heappop(queue)
        if cur in visited: continue
        path = path + [cur]
        visited.add(cur)
        if cur == target: return path
        for neighbor, weight in graph[cur].items():
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor, path))
    return [start, target]


def get_noisy_shortest_path(noisy_graph, start, target):
    queue = [(0, start, [])]
    visited = set()
    while queue:
        cost, cur, path = heapq.heappop(queue)
        if cur in visited: continue
        path = path + [cur]
        visited.add(cur)
        if cur == target: return path
        for neighbor, weight in noisy_graph[cur].items():
            if neighbor not in visited:
                heapq.heappush(queue, (cost + weight, neighbor, path))
    return [start, target]


# ============================================================
# DYNAMIC GRAPH CENTRALITY
# ============================================================
_node_centrality_cache = {}


def get_centrality(node, points, roads):
    if not _node_centrality_cache:
        counts = {n: 0 for n in points}
        for u, v in roads:
            counts[u] = counts.get(u, 0) + 1
            counts[v] = counts.get(v, 0) + 1
        if counts:
            max_deg = max(counts.values())
            for n, c in counts.items():
                _node_centrality_cache[n] = c / max_deg if max_deg > 0 else 0
    return _node_centrality_cache.get(node, 0.0)


# ============================================================
# 1. LOWER LEVEL: VEHICLE ROUTING
# ============================================================
def metaheuristic_qpso_route(start, target, traffic_lights_state, points, roads, vehicles=None, blocked_edges=None,
                             is_emergency=False):
    if start == target: return [start]

    blocked_edges = blocked_edges or set()
    candidate_paths = []
    vehicles = vehicles or []

    edge_momentum = {}
    for v in vehicles:
        if getattr(v, 'path', None) and getattr(v, 'active', False) and hasattr(v, 'segment_idx'):
            path = v.path
            idx = v.segment_idx
            for lookahead in range(3):
                if idx + lookahead < len(path) - 1:
                    edge = tuple(sorted((path[idx + lookahead], path[idx + lookahead + 1])))
                    weight = 1.0 / (2 ** lookahead)
                    edge_momentum[edge] = edge_momentum.get(edge, 0.0) + weight

    for _ in range(12):
        noisy_graph = {node: {} for node in points}
        for u, v in roads:
            if (u, v) in blocked_edges or (v, u) in blocked_edges: continue

            d = calculate_dist(points[u], points[v])
            sorted_edge = tuple(sorted((u, v)))
            vol = edge_momentum.get(sorted_edge, 0.0)

            momentum = 1.0 + 0.08 * (vol ** 1.5)
            noise = random.uniform(0.98, 1.02) * momentum

            c_u, c_v = get_centrality(u, points, roads), get_centrality(v, points, roads)
            hierarchy_penalty = 1.0 if (c_u > 0.5 or c_v > 0.5) else 1.35
            if is_emergency: hierarchy_penalty = 1.0

            signal_delay = 0.0
            if v in traffic_lights_state:
                state = traffic_lights_state[v]["state"]
                if state == "RED":
                    signal_delay = 10.0 if is_emergency else 70.0
                elif state == "YELLOW":
                    signal_delay = 0.0 if is_emergency else 30.0
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
            if (u, v) in blocked_edges or (v, u) in blocked_edges: continue
            graph[u][v] = graph[v][u] = calculate_dist(points[u], points[v])
        path = get_shortest_path(graph, start, target)
        if len(path) <= 2 and path[0] != start and path[-1] != target: return [start]
        return path

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
                state = traffic_lights_state[v]["state"]
                if state == "RED":
                    cost += 10.0 if is_emergency else 70.0
                elif state == "YELLOW":
                    cost += 0.0 if is_emergency else 30.0
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
def qpso_optimize_traffic_lights(vehicles, traffic_lights, points, clusters):
    light_keys = list(traffic_lights.keys())
    dim = len(light_keys)
    if dim == 0: return []

    num_particles = 15
    max_iter = 20

    junction_volume = {node: 0 for node in light_keys}
    emergency_volume = {node: 0 for node in light_keys}

    for v in vehicles:
        if getattr(v, 'active', False) and getattr(v, 'path', None) and v.segment_idx < len(v.path) - 1:
            if v.next_node in light_keys:
                dist = (1.0 - v.progress) * calculate_dist(points[v.curr_node], points[v.next_node])
                if dist < 75.0:
                    if getattr(v, 'v_type', 'STANDARD') == 'EMERGENCY':
                        emergency_volume[v.next_node] += 1
                    else:
                        junction_volume[v.next_node] += 1

    X = np.random.uniform(-1.0, 1.0, (num_particles, dim))
    P_best, P_scores = np.copy(X), np.full(num_particles, np.inf)
    G_best, G_best_score = np.zeros(dim), np.inf

    def get_cluster_greens(state_array):
        green_nodes = set()
        for intersection, lights in clusters.items():
            best_light = None
            max_val = -float('inf')
            for l in lights:
                if l in light_keys:
                    idx = light_keys.index(l)
                    val = state_array[idx]
                    if val > max_val:
                        max_val = val
                        best_light = l
            if best_light:
                green_nodes.add(best_light)
        return green_nodes

    def evaluate_signals(state):
        cost = 0.0
        green_nodes = get_cluster_greens(state)

        for node in light_keys:
            is_green = node in green_nodes
            vol, em_vol = junction_volume[node], emergency_volume[node]

            if not is_green:
                cost += (vol * 150.0) + (em_vol * 5000.0)
            else:
                cost -= (vol * 200.0) + (em_vol * 2000.0)

        for v in vehicles:
            if getattr(v, 'active', False) and getattr(v, 'path', None) and v.segment_idx < len(v.path) - 1:
                future_nodes = v.path[v.segment_idx + 1:v.segment_idx + 4]
                for hop, node_name in enumerate(future_nodes, start=1):
                    if node_name in green_nodes:
                        multiplier = 10.0 if getattr(v, 'v_type', 'STANDARD') == 'EMERGENCY' else 1.0
                        cost -= (25.0 * multiplier) / hop

        return cost

    for t in range(max_iter):
        mbest = np.mean(P_best, axis=0)
        diversity = np.mean(np.linalg.norm(X - G_best, axis=1))
        alpha = 0.5 + 0.5 * np.exp(-diversity / (t + 1))

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

    return get_cluster_greens(G_best)