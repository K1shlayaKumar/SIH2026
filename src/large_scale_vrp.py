import numpy as np
import time


# =======================================================
# 1. LARGE-SCALE PROBLEM INSTANCE GENERATION (N = 120)
# =======================================================
class LargeScaleVRPInstance:
    def __init__(self, num_customers=120, num_vehicles=6, vehicle_capacity=40, seed=42):
        np.random.seed(seed)
        self.num_customers = num_customers
        self.num_vehicles = num_vehicles
        self.capacity = vehicle_capacity

        # Depot at origin (0, 0); Customers dispersed across 100x100 grid
        self.depot = np.array([0.0, 0.0])
        self.customer_coords = np.random.uniform(-50.0, 50.0, size=(num_customers, 2))
        self.all_coords = np.vstack([self.depot, self.customer_coords])

        # Customer demands between 1 and 4 units
        self.demands = np.random.randint(1, 5, size=num_customers)

        # Precompute Euclidean distance / base time matrix
        diff = self.all_coords[:, np.newaxis, :] - self.all_coords[np.newaxis, :, :]
        self.dist_matrix = np.sqrt(np.sum(diff ** 2, axis=-1))


# =======================================================
# 2. MICRO-ENGINE: QUANTUM PSO SUB-ROUTE OPTIMIZER
# =======================================================
def optimize_subroute_qpso(route_nodes, dist_matrix, num_particles=20, max_iter=40):
    """
    Solves Traveling Salesperson corridor sequencing for a specific vehicle's node cluster.
    """
    k = len(route_nodes)
    if k <= 2:
        return route_nodes, sum(dist_matrix[route_nodes[i]][route_nodes[i + 1]] for i in range(k - 1))

    # Search space dimension is the sequence of intermediate cluster nodes
    intermediates = route_nodes[1:-1]
    dim = len(intermediates)

    # Initialize quantum particles in [-1, 1]
    X = np.random.uniform(-1.0, 1.0, (num_particles, dim))
    P_best = np.copy(X)

    def decode_and_eval(pos):
        order = np.argsort(pos)
        ordered_intermediates = [intermediates[idx] for idx in order]
        full_path = [route_nodes[0]] + ordered_intermediates + [route_nodes[-1]]
        cost = sum(dist_matrix[full_path[i]][full_path[i + 1]] for i in range(len(full_path) - 1))
        return full_path, cost

    P_scores = np.array([decode_and_eval(p)[1] for p in X])
    g_idx = np.argmin(P_scores)
    G_best = np.copy(X[g_idx])
    G_best_score = P_scores[g_idx]

    # QPSO Evolution loop
    for t in range(max_iter):
        alpha = 1.0 - (0.5 * t / max_iter)
        mbest = np.mean(P_best, axis=0)

        for i in range(num_particles):
            phi = np.random.uniform(0, 1, dim)
            p = phi * P_best[i] + (1.0 - phi) * G_best
            u = np.random.uniform(0, 1, dim)
            sign = np.where(np.random.rand(dim) > 0.5, 1, -1)

            # Delta potential well update
            X[i] = p + sign * alpha * np.abs(mbest - X[i]) * np.log(1.0 / (u + 1e-9))

            _, score = decode_and_eval(X[i])
            if score < P_scores[i]:
                P_scores[i] = score
                P_best[i] = np.copy(X[i])
                if score < G_best_score:
                    G_best_score = score
                    G_best = np.copy(X[i])

    best_path, best_cost = decode_and_eval(G_best)
    return best_path, best_cost


# =======================================================
# 3. MACRO-ENGINE: QUANTUM-INSPIRED GENETIC CLUSTERING
# =======================================================
def solve_large_scale_cvrp_quantum(vrp: LargeScaleVRPInstance, qga_pop_size=25, qga_generations=50):
    start_time = time.time()
    num_nodes = vrp.num_customers
    num_vehicles = vrp.num_vehicles

    # Qubit chromosome representation: probability angles theta in [0, pi/2]
    # Dimensions: (Population, Nodes, Vehicles)
    q_angles = np.full((qga_pop_size, num_nodes, num_vehicles), np.pi / 4.0)

    global_best_routes = None
    global_best_fitness = float('inf')

    for gen in range(qga_generations):
        # 1. Collapse qubits into discrete cluster assignments (Quantum Measurement)
        probabilities = np.sin(q_angles) ** 2
        assignments = np.zeros((qga_pop_size, num_nodes), dtype=int)

        for p in range(qga_pop_size):
            for n in range(num_nodes):
                p_dist = probabilities[p, n] / np.sum(probabilities[p, n])
                assignments[p, n] = np.random.choice(num_vehicles, p=p_dist)

        # 2. Evaluate individual fleet plans
        for p in range(qga_pop_size):
            pop_total_cost = 0.0
            vehicle_routes = []

            for v in range(num_vehicles):
                # Customers allocated to vehicle v (indices shifted by +1 for depot=0)
                cust_ids = np.where(assignments[p] == v)[0] + 1
                total_demand = np.sum(vrp.demands[cust_ids - 1]) if len(cust_ids) > 0 else 0

                # Capacity Constraint Penalty
                if total_demand > vrp.capacity:
                    pop_total_cost += 5000.0 + (total_demand - vrp.capacity) * 200.0

                if len(cust_ids) > 0:
                    raw_subroute = [0] + cust_ids.tolist() + [0]
                    # Sequence corridor via Micro-QPSO
                    opt_subroute, sub_cost = optimize_subroute_qpso(raw_subroute, vrp.dist_matrix, num_particles=15,
                                                                    max_iter=20)
                    pop_total_cost += sub_cost
                    vehicle_routes.append((opt_subroute, total_demand, sub_cost))
                else:
                    vehicle_routes.append(([0, 0], 0, 0.0))

            # Update best state
            if pop_total_cost < global_best_fitness:
                global_best_fitness = pop_total_cost
                global_best_routes = vehicle_routes

                # Dynamic Quantum Rotation Gate: Align population angles toward best collapse
                for n in range(num_nodes):
                    best_v = assignments[p, n]
                    q_angles[:, n, :] -= 0.05 * np.sin(q_angles[:, n, :])
                    q_angles[:, n, best_v] += 0.10 * np.cos(q_angles[:, n, best_v])
                    # Bound angles to [0.01, pi/2 - 0.01]
                    q_angles = np.clip(q_angles, 0.01, (np.pi / 2.0) - 0.01)

    exec_time = time.time() - start_time
    return global_best_routes, global_best_fitness, exec_time


# =======================================================
# 4. EXECUTION & METRIC VALIDATION
# =======================================================
if __name__ == "__main__":
    print("==========================================================================")
    print("  QUANTUM-INSPIRED METAHEURISTIC FRAMEWORK: LARGE-SCALE CVRP BENCHMARK   ")
    print("==========================================================================")

    vrp_system = LargeScaleVRPInstance(num_customers=120, num_vehicles=6, vehicle_capacity=70)
    print(f"Dataset Size      : {vrp_system.num_customers} Nodes | {vrp_system.num_vehicles} Vehicle Fleet")
    print(f"Vehicle Capacity  : {vrp_system.capacity} units/truck | Total Demand: {np.sum(vrp_system.demands)} units")
    print("Executing Quantum Decomposition & Potential Well Optimization...\n")

    best_fleet, total_dist, duration = solve_large_scale_cvrp_quantum(vrp_system, qga_pop_size=20, qga_generations=30)

    print("-" * 74)
    print(f"{'Vehicle ID':<12} | {'Demand Assigned':<18} | {'Nodes Visited':<15} | {'Sub-Route Distance'}")
    print("-" * 74)
    for v_idx, (path, dem, cost) in enumerate(best_fleet):
        print(
            f"Vehicle #{v_idx + 1:<5} | {dem:>3}/{vrp_system.capacity} units ({dem / vrp_system.capacity * 100:4.1f}%) | {len(path) - 2:<15} | {cost:6.2f} km")
    print("-" * 74)
    print(f"Global System Optimized Distance : {total_dist:.2f} km")
    print(f"Quantum Swarm Computation Time  : {duration:.2f} seconds")