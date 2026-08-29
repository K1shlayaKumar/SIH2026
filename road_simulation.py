import json
import math
import random
import heapq
import numpy as np
import pygame

# ============================================================
# 1. GRAPH DATA & EXTRACTION
# ============================================================
GRAPH_DATA_JSON = r'''
{"nodes": {"0": {"x": 538.0, "y": 36.0, "type": "plain"}, "1": {"x": 408.0, "y": 38.0, "type": "plain"}, "2": {"x": 359.0, "y": 71.0, "type": "plain"}, "3": {"x": 544.3, "y": 97.3, "type": "plain"}, "4": {"x": 183.8, "y": 122.3, "type": "red", "id": 1}, "5": {"x": 237.3, "y": 121.3, "type": "plain"}, "6": {"x": 272.0, "y": 122.2, "type": "plain"}, "7": {"x": 510.3, "y": 142.7, "type": "plain"}, "8": {"x": 711.0, "y": 165.0, "type": "plain"}, "9": {"x": 549.0, "y": 171.8, "type": "plain"}, "10": {"x": 699.0, "y": 203.2, "type": "plain"}, "11": {"x": 758.2, "y": 224.5, "type": "red", "id": 2}, "12": {"x": 745.7, "y": 224.7, "type": "plain"}, "13": {"x": 695.0, "y": 229.8, "type": "plain"}, "27": {"x": 259.9, "y": 285.0, "type": "light"}, "16": {"x": 646.0, "y": 241.0, "type": "plain"}, "17": {"x": 218.0, "y": 245.0, "type": "plain"}, "30": {"x": 588.8, "y": 288.5, "type": "light"}, "21": {"x": 182.8, "y": 264.0, "type": "plain"}, "26": {"x": 424.7, "y": 287.3, "type": "red", "id": 3}, "28": {"x": 787.0, "y": 282.0, "type": "plain"}, "38": {"x": 153.7, "y": 324.3, "type": "plain"}, "40": {"x": 692.0, "y": 362.0, "type": "plain"}, "41": {"x": 583.8, "y": 367.0, "type": "plain"}, "42": {"x": 81.0, "y": 372.0, "type": "plain"}, "43": {"x": 790.0, "y": 378.8, "type": "plain"}, "44": {"x": 440.0, "y": 382.0, "type": "plain"}, "45": {"x": 513.0, "y": 392.2, "type": "red", "id": 5}, "46": {"x": 524.0, "y": 385.6, "type": "plain"}, "47": {"x": 329.7, "y": 394.2, "type": "red", "id": 4}, "48": {"x": 267.0, "y": 422.0, "type": "plain"}, "49": {"x": 102.0, "y": 430.0, "type": "plain"}, "63": {"x": 389.5, "y": 476.2, "type": "light"}, "52": {"x": 888.0, "y": 445.0, "type": "plain"}, "53": {"x": 587.3, "y": 452.3, "type": "plain"}, "56": {"x": 171.0, "y": 471.0, "type": "plain"}, "61": {"x": 102.2, "y": 496.0, "type": "plain"}, "64": {"x": 747.3, "y": 513.7, "type": "plain"}, "65": {"x": 272.0, "y": 514.0, "type": "plain"}, "66": {"x": 802.0, "y": 549.0, "type": "plain"}, "67": {"x": 123.9, "y": 588.2, "type": "red", "id": 6}, "68": {"x": 323.0, "y": 584.0, "type": "plain"}, "69": {"x": 183.0, "y": 602.0, "type": "plain"}, "70": {"x": 615.3, "y": 620.7, "type": "plain"}, "71": {"x": 230.0, "y": 640.2, "type": "red", "id": 7}, "72": {"x": 516.0, "y": 664.0, "type": "plain"}, "73": {"x": 328.0, "y": 690.0, "type": "plain"}, "74": {"x": 430.2, "y": 708.4, "type": "red", "id": 8}}, "edges": [{"a": 3, "b": 0, "pts": [[544.3, 97.3], [538.0, 36.0]]}, {"a": 1, "b": 7, "pts": [[408.0, 38.0], [435.0, 121.0], [510.3, 142.7]]}, {"a": 2, "b": 6, "pts": [[359.0, 71.0], [318.0, 122.0], [272.0, 122.2]]}, {"a": 10, "b": 3, "pts": [[699.0, 203.2], [596.0, 180.0], [589.0, 99.0], [544.3, 97.3]]}, {"a": 3, "b": 9, "pts": [[544.3, 97.3], [549.0, 171.8]]}, {"a": 4, "b": 5, "pts": [[183.8, 122.3], [237.3, 121.3]]}, {"a": 5, "b": 6, "pts": [[237.3, 121.3], [272.0, 122.2]]}, {"a": 21, "b": 5, "pts": [[182.8, 264.0], [237.3, 121.3]]}, {"a": 27, "b": 6, "pts": [[259.9, 285.0], [272.0, 122.2]]}, {"a": 9, "b": 7, "pts": [[549.0, 171.8], [523.0, 173.0], [516.0, 146.0], [510.3, 142.7]]}, {"a": 7, "b": 26, "pts": [[510.3, 142.7], [387.0, 215.0], [424.7, 287.3]]}, {"a": 10, "b": 8, "pts": [[699.0, 203.2], [711.0, 165.0]]}, {"a": 30, "b": 9, "pts": [[588.8, 288.5], [549.0, 171.8]]}, {"a": 13, "b": 10, "pts": [[695.0, 229.8], [699.0, 203.2]]}, {"a": 11, "b": 12, "pts": [[758.2, 224.5], [745.7, 224.7]]}, {"a": 12, "b": 13, "pts": [[745.7, 224.7], [695.0, 229.8]]}, {"a": 13, "b": 16, "pts": [[695.0, 229.8], [656.0, 235.0], [646.0, 241.0]]}, {"a": 30, "b": 16, "pts": [[588.8, 288.5], [634.0, 249.0], [646.0, 241.0]]}, {"a": 40, "b": 16, "pts": [[692.0, 362.0], [644.0, 309.0], [646.0, 241.0]]}, {"a": 17, "b": 21, "pts": [[218.0, 245.0], [182.8, 264.0]]}, {"a": 38, "b": 21, "pts": [[153.7, 324.3], [182.8, 264.0]]}, {"a": 28, "b": 40, "pts": [[787.0, 282.0], [692.0, 362.0]]}, {"a": 27, "b": 44, "pts": [[259.9, 285.0], [440.0, 382.0]]}, {"a": 30, "b": 44, "pts": [[588.8, 288.5], [468.0, 341.0], [440.0, 382.0]]}, {"a": 61, "b": 27, "pts": [[102.2, 496.0], [105.0, 485.0], [170.0, 428.0], [259.9, 285.0]]}, {"a": 41, "b": 30, "pts": [[583.8, 367.0], [588.0, 333.0], [588.8, 288.5]]}, {"a": 38, "b": 42, "pts": [[153.7, 324.3], [146.0, 326.0], [81.0, 372.0]]}, {"a": 38, "b": 49, "pts": [[153.7, 324.3], [102.0, 430.0]]}, {"a": 27, "b": 48, "pts": [[259.9, 285.0], [261.0, 337.0], [267.0, 422.0]]}, {"a": 40, "b": 53, "pts": [[692.0, 362.0], [602.0, 444.0], [587.3, 452.3]]}, {"a": 41, "b": 46, "pts": [[583.8, 367.0], [524.0, 385.6]]}, {"a": 41, "b": 53, "pts": [[583.8, 367.0], [579.0, 412.0], [587.3, 452.3]]}, {"a": 64, "b": 43, "pts": [[747.3, 513.7], [721.0, 419.0], [790.0, 378.8]]}, {"a": 43, "b": 52, "pts": [[790.0, 378.8], [808.0, 459.0], [888.0, 445.0]]}, {"a": 63, "b": 44, "pts": [[389.5, 476.2], [440.0, 382.0]]}, {"a": 45, "b": 46, "pts": [[513.0, 392.2], [524.0, 385.6]]}, {"a": 48, "b": 47, "pts": [[267.0, 422.0], [329.7, 394.2]]}, {"a": 48, "b": 65, "pts": [[267.0, 422.0], [272.0, 514.0]]}, {"a": 70, "b": 53, "pts": [[615.3, 620.7], [587.3, 452.3]]}, {"a": 61, "b": 56, "pts": [[102.2, 496.0], [152.0, 518.0], [171.0, 471.0]]}, {"a": 63, "b": 72, "pts": [[389.5, 476.2], [437.0, 484.0], [479.0, 510.0], [516.0, 664.0]]}, {"a": 63, "b": 65, "pts": [[389.5, 476.2], [272.0, 514.0]]}, {"a": 67, "b": 61, "pts": [[123.9, 588.2], [102.2, 496.0]]}, {"a": 63, "b": 68, "pts": [[389.5, 476.2], [323.0, 584.0]]}, {"a": 69, "b": 65, "pts": [[183.0, 602.0], [209.0, 542.0], [272.0, 514.0]]}, {"a": 70, "b": 64, "pts": [[615.3, 620.7], [627.0, 617.0], [747.3, 513.7]]}, {"a": 64, "b": 66, "pts": [[747.3, 513.7], [802.0, 549.0]]}, {"a": 68, "b": 71, "pts": [[323.0, 584.0], [230.0, 640.2]]}, {"a": 73, "b": 68, "pts": [[328.0, 690.0], [369.0, 613.0], [323.0, 584.0]]}, {"a": 70, "b": 72, "pts": [[615.3, 620.7], [516.0, 664.0]]}, {"a": 72, "b": 74, "pts": [[516.0, 664.0], [430.2, 708.4]]}], "hub_lights": {"27": [[240.7, 293.6], [254.0, 244.8], [260.9, 322.4], [283.8, 279.1]], "30": [[584.4, 261.7], [568.3, 294.0], [611.6, 282.7], [590.7, 315.6]], "63": [[354.5, 482.1], [425.5, 476.1], [372.0, 504.6], [406.0, 442.0]]}}
'''

DATA = json.loads(GRAPH_DATA_JSON)
NODES = {str(k): v for k, v in DATA["nodes"].items()}
EDGES = DATA["edges"]
HUB_LIGHTS = {str(k): v for k, v in DATA["hub_lights"].items()}

POINTS = {k: (v["x"], v["y"]) for k, v in NODES.items()}
ROADS = [(str(e["a"]), str(e["b"])) for e in EDGES]
RED_IDS = [k for k, v in NODES.items() if v["type"] == "red"]
HUB_IDS = [k for k, v in NODES.items() if v["type"] == "light"]

# ============================================================
# 2. ROUTING & GRAPH UTILITIES
# ============================================================
def calculate_dist(p1, p2):
    return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

def poly_len(pts):
    return sum(calculate_dist(pts[i], pts[i-1]) for i in range(1, len(pts)))

adj = {k: [] for k in NODES}
for idx, e in enumerate(EDGES):
    a, b, L = str(e["a"]), str(e["b"]), poly_len(e["pts"])
    adj[a].append((b, idx, L))
    adj[b].append((a, idx, L))

def edge_points(edge_idx, from_id):
    e = EDGES[edge_idx]
    pts = e["pts"]
    return pts if str(e["a"]) == from_id else list(reversed(pts))

_node_centrality_cache = {}
def get_centrality(node, points, roads):
    if not _node_centrality_cache:
        counts = {n: 0 for n in points}
        for u, v in roads:
            counts[u] = counts.get(u, 0) + 1
            counts[v] = counts.get(v, 0) + 1
        max_deg = max(counts.values()) if counts else 1
        for n, c in counts.items():
            _node_centrality_cache[n] = c / max_deg
    return _node_centrality_cache.get(node, 0.0)

def get_noisy_shortest_path(noisy_graph, start, target):
    queue = [(0.0, start, [])]
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

def metaheuristic_qpso_route(start, target, traffic_lights, vehicles=None, is_emergency=False):
    if start == target: return [start]
    candidate_paths = []
    vehicles = vehicles or []

    for _ in range(8):
        noisy_graph = {node: {} for node in POINTS}
        for u, v in ROADS:
            d = calculate_dist(POINTS[u], POINTS[v])
            c_u, c_v = get_centrality(u, POINTS, ROADS), get_centrality(v, POINTS, ROADS)
            hierarchy_penalty = 1.0 if (c_u > 0.5 or c_v > 0.5 or is_emergency) else 1.3
            noise = random.uniform(0.95, 1.05)

            signal_delay = 0.0
            if v in traffic_lights:
                state = traffic_lights[v].effective_state(u)
                if state == "red": signal_delay = 5.0 if is_emergency else 60.0
                elif state == "yellow": signal_delay = 0.0 if is_emergency else 25.0
                else: signal_delay = -15.0

            weight = max(1.0, (d * noise * hierarchy_penalty) + signal_delay)
            noisy_graph[u][v] = weight
            noisy_graph[v][u] = weight

        path = get_noisy_shortest_path(noisy_graph, start, target)
        if path and len(path) > 1 and path not in candidate_paths:
            candidate_paths.append(path)

    if not candidate_paths:
        return [start, target]
    return min(candidate_paths, key=lambda p: sum(calculate_dist(POINTS[p[i]], POINTS[p[i+1]]) for i in range(len(p)-1)))

# ============================================================
# 3. REAL-TIME TRAFFIC LIGHT CONTROLLER (LOAD-DRIVEN, PSO-TUNED)
# ============================================================
# Each hub is a real 4-way intersection: its 4 signal dots belong to two
# opposing (parallel) approaches, e.g. North-South and East-West. Exactly one
# of these two phases may be green/yellow at a time; the other phase must be
# red, with an all-red clearance while switching between them.
MIN_GREEN_TIME = 4.0
MAX_GREEN_TIME = 45.0     # rarely-hit fairness backstop; the PSO tunes within this range,
                          # but day-to-day switching is driven by opposite-side load+wait, not this clock
YELLOW_TIME = 2.0
ALL_RED_TIME = 1.0
GREEN_REQUEST_THRESHOLD = 0.25   # min smoothed load before a hub actuates green
PHASE_SWITCH_MARGIN = 0.3        # hysteresis to stop phases flapping on near-equal load
MAX_PHASE_WAIT = 18.0            # hard cap (seconds): a loaded phase is never left waiting longer than this,
                                  # regardless of how the score comparison or PSO weights land -- this is what
                                  # actually bounds queue buildup, since max_green alone could otherwise be tuned
                                  # up to MAX_GREEN_TIME and let a waiting side queue for the full duration

# Priority score for a phase = load*LOAD_WEIGHT + wait_time*WAIT_WEIGHT. These
# two globals are the actual "opposite-side load + waiting time" decision
# weights the user asked for; a hub switches phase when the RED side's score
# overtakes the GREEN side's, not on a fixed clock. A PSO pass (section 5)
# periodically retunes them from live network data.
LOAD_WEIGHT = 1.0
WAIT_WEIGHT = 0.15

def _pair_hub_dots(hub_id):
    """Split a hub's 4 signal dots into two antipodal pairs (the two roads
    crossing at this intersection) by finding the pairing whose two dot-pairs
    each sum closest to zero relative to the hub center."""
    center = POINTS[hub_id]
    dots = HUB_LIGHTS[hub_id]
    idxs = list(range(len(dots)))
    if len(idxs) != 4:
        half = len(idxs) // 2
        return {"A": idxs[:half], "B": idxs[half:]}

    def offset(i):
        return (dots[i][0] - center[0], dots[i][1] - center[1])

    splits = [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]
    best, best_score = None, None
    for p1, p2 in splits:
        v1 = tuple(sum(offset(i)[c] for i in p1) for c in (0, 1))
        v2 = tuple(sum(offset(i)[c] for i in p2) for c in (0, 1))
        score = math.hypot(*v1) + math.hypot(*v2)
        if best_score is None or score < best_score:
            best_score, best = score, (list(p1), list(p2))
    return {"A": best[0], "B": best[1]}

def _circular_dist(a, b, period):
    d = abs(a - b) % period
    return min(d, period - d)

def _compute_hub_geometry():
    """For every hub, determine its two phase-groups of dots plus a mapping
    from each incoming neighbor node to the phase its approach belongs to."""
    phase_dots = {}
    neighbor_phase = {}
    for hub in HUB_IDS:
        pairs = _pair_hub_dots(hub)
        phase_dots[hub] = pairs
        center = POINTS[hub]
        axis_angle = {}
        for phase, idxs in pairs.items():
            dx = HUB_LIGHTS[hub][idxs[0]][0] - center[0]
            dy = HUB_LIGHTS[hub][idxs[0]][1] - center[1]
            axis_angle[phase] = math.atan2(dy, dx) % math.pi

        this_hub_map = {}
        for neighbor, eidx, _ in adj[hub]:
            pts = edge_points(eidx, neighbor)   # ordered neighbor -> hub
            if len(pts) >= 2:
                dx, dy = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
            else:
                nx, ny = POINTS[neighbor]
                dx, dy = center[0] - nx, center[1] - ny
            ang = math.atan2(dy, dx) % math.pi
            this_hub_map[neighbor] = min(axis_angle, key=lambda p: _circular_dist(ang, axis_angle[p], math.pi))
        neighbor_phase[hub] = this_hub_map
    return phase_dots, neighbor_phase

HUB_PHASE_DOTS, HUB_PHASE_OF_NEIGHBOR = _compute_hub_geometry()

class RealLifeTrafficLight:
    def __init__(self, hub_id):
        self.hub_id = hub_id
        self.phase_dots = HUB_PHASE_DOTS[hub_id]        # {"A": [dot_idx,...], "B": [...]}
        self.neighbor_phase = HUB_PHASE_OF_NEIGHBOR[hub_id]
        self.active = "A"          # which phase currently owns the green/yellow cycle
        self.state = "red"         # state of the ACTIVE phase; the other phase is always red
        self.timer = 0.0
        self.requested_state = "red"
        self.pending_phase = None  # forces a specific phase to activate next (emergency preemption)
        self.max_green = MAX_GREEN_TIME   # generous until the first PSO pass tightens it; a rare backstop, not the driver
        self.load = {"A": 0.0, "B": 0.0}       # smoothed per-phase demand, for HUD/debugging
        self.wait_time = {"A": 0.0, "B": 0.0}  # time since each phase was last served (fairness aging)

    def _other(self):
        return "B" if self.active == "A" else "A"

    def _score(self, phase):
        return self.load[phase] * LOAD_WEIGHT + self.wait_time[phase] * WAIT_WEIGHT

    def update(self, dt):
        self.timer += dt
        # age the phase that is NOT currently green so it can't starve forever
        # under equal/near-equal load -- its priority keeps rising until it wins
        idle_phase = self._other() if self.state == "green" else self.active
        served_phase = self.active if self.state == "green" else None
        self.wait_time[idle_phase] += dt
        if served_phase:
            self.wait_time[served_phase] = 0.0

        if self.state == "yellow" and self.timer >= YELLOW_TIME:
            self.state = "red"
            self.timer = 0.0
        elif self.state == "red":
            if self.timer >= ALL_RED_TIME:
                if self.pending_phase:
                    self.active = self.pending_phase
                    self.pending_phase = None
                else:
                    other = self._other()
                    if self.load[other] > GREEN_REQUEST_THRESHOLD and self._score(other) > self._score(self.active) + PHASE_SWITCH_MARGIN:
                        self.active = other
                if self.requested_state == "green" or self.load[self.active] > GREEN_REQUEST_THRESHOLD:
                    self.state = "green"
                    self.timer = 0.0
        elif self.state == "green":
            if self.timer < MIN_GREEN_TIME:
                return   # safety floor: never cut a green shorter than this, regardless of demand

            other = self._other()
            active_load, other_load = self.load[self.active], self.load[other]

            # Demand-driven gap-out: switch as soon as the RED side's priority
            # (its own queue load plus how long it has been waiting) overtakes
            # the currently GREEN side's -- not on a fixed clock. If the green
            # side has emptied out and the red side has anyone waiting, hand
            # over immediately too.
            opposite_deserves_turn = other_load > GREEN_REQUEST_THRESHOLD and self._score(other) > self._score(self.active) + PHASE_SWITCH_MARGIN
            green_side_emptied = active_load <= GREEN_REQUEST_THRESHOLD and other_load > GREEN_REQUEST_THRESHOLD
            # Hard starvation guard: never let a loaded phase queue past this,
            # no matter how the score comparison lands -- this is the real
            # bound on queue buildup (max_green alone could otherwise stretch
            # up to MAX_GREEN_TIME before rescuing the waiting side).
            starved_out = self.wait_time[other] >= MAX_PHASE_WAIT and other_load > GREEN_REQUEST_THRESHOLD
            hit_safety_cap = self.timer >= self.max_green   # PSO-tuned fairness backstop, rarely hit

            if opposite_deserves_turn or green_side_emptied or starved_out or hit_safety_cap:
                self.state = "yellow"
                self.timer = 0.0

    def set_target(self, wants_green):
        self.requested_state = "green" if wants_green else "red"

    def request_emergency(self, phase):
        """Force this hub to serve `phase` as soon as possible for a priority vehicle."""
        self.max_green = max(self.max_green, MIN_GREEN_TIME + 5.0)
        if self.active == phase:
            self.requested_state = "green"
            return
        if self.state == "green":
            self.state = "yellow"
            self.timer = YELLOW_TIME   # expedite: next update() clears to red immediately
        self.pending_phase = phase

    def effective_state(self, neighbor):
        """Signal state as seen by a vehicle arriving from `neighbor`."""
        phase = self.neighbor_phase.get(neighbor)
        if phase is None or phase != self.active:
            return "red"
        return self.state

    def dot_state(self, dot_idx):
        """Signal color for one of the hub's rendered dots."""
        phase = "A" if dot_idx in self.phase_dots["A"] else "B"
        return self.state if phase == self.active else "red"

# ============================================================
# 4. VEHICLE SIMULATION CLASS
# ============================================================
# Roads are modeled as two lanes (one per direction of travel) instead of a
# single shared centerline: each vehicle is rendered offset to the right of
# its own direction of travel, which automatically separates opposing traffic
# into its own half of the road. Vehicles travelling the same direction on
# the same edge additionally car-follow (no overtaking), so a third vehicle
# queues in behind the first two instead of clipping/crossing through them.
LANE_OFFSET = 3.5          # px, perpendicular offset from centerline into each direction's lane
MIN_FOLLOW_GAP = 16.0      # px, minimum bumper-to-bumper spacing enforced within a lane

class Vehicle:
    def __init__(self, idx, is_emergency=False):
        self.idx = idx
        self.is_emergency = is_emergency
        self.v_type = "EMERGENCY" if is_emergency else "STANDARD"
        self.active = True
        self.color = (239, 68, 68) if is_emergency else [(59,130,246), (16,185,129), (245,158,11), (139,92,246), (236,72,153)][idx % 5]
        self.curr_node = random.choice(RED_IDS)
        self.dest = random.choice([r for r in RED_IDS if r != self.curr_node])
        self.speed = 130.0 if is_emergency else 85.0
        self.path = []
        self.segment_idx = 0
        self.progress = 0.0
        self.waiting = False
        self.replan()

    def replan(self):
        self.path = metaheuristic_qpso_route(self.curr_node, self.dest, lights, [self], self.is_emergency)
        self.segment_idx = 0
        self.progress = 0.0
        self._load_current_segment()

    def _load_current_segment(self):
        if self.segment_idx < len(self.path) - 1:
            u, v = self.path[self.segment_idx], self.path[self.segment_idx + 1]
            eidx = next(ei for nb, ei, _ in adj[u] if nb == v)
            self.seg_eidx = eidx
            self.seg_points = edge_points(eidx, u)
            self.seg_len = poly_len(self.seg_points)
        else:
            self.seg_eidx = None
            self.seg_points = [POINTS[self.curr_node]]
            self.seg_len = 0.0

    @property
    def next_node(self):
        return self.path[self.segment_idx + 1] if self.segment_idx < len(self.path) - 1 else self.curr_node

    def update(self, dt, ahead_gap=None):
        if self.segment_idx >= len(self.path) - 1:
            # trip complete -- vehicle leaves the simulation instead of looping
            # forever, so the fleet composition actually changes over time
            self.active = False
            self.waiting = False
            return

        next_n = self.next_node
        rem_dist = (1.0 - self.progress) * self.seg_len
        self.waiting = False

        # Signal check approaching intersection (phase-aware: only this approach's signal matters)
        if next_n in lights and rem_dist < 22.0:
            tl = lights[next_n]
            eff = tl.effective_state(self.curr_node)
            if not self.is_emergency:
                if eff in ("red", "yellow"):
                    self.waiting = True
                    return
            else:
                # Emergency vehicles only wait if light hasn't transitioned yet
                if eff == "red" and rem_dist < 8.0:
                    self.waiting = True
                    return

        adv = (self.speed * dt) / max(1.0, self.seg_len)

        # Car-following: never advance past the minimum gap behind whichever
        # vehicle is directly ahead in the same lane (same edge, same direction)
        if ahead_gap is not None:
            max_adv_dist = max(0.0, ahead_gap - MIN_FOLLOW_GAP)
            max_adv = max_adv_dist / max(1.0, self.seg_len)
            if max_adv < adv:
                adv = max_adv
            if adv <= 1e-6:
                self.waiting = True
                return

        self.progress += adv
        if self.progress >= 1.0:
            self.progress = 0.0
            self.segment_idx += 1
            self.curr_node = next_n
            self._load_current_segment()

    @property
    def pos(self):
        if not self.seg_points or len(self.seg_points) < 2:
            return POINTS[self.curr_node]
        target_s = self.progress * self.seg_len
        acc = 0.0
        for i in range(1, len(self.seg_points)):
            p0, p1 = self.seg_points[i-1], self.seg_points[i]
            d = calculate_dist(p0, p1)
            if acc + d >= target_s:
                t = 0 if d == 0 else (target_s - acc) / d
                x = p0[0] + (p1[0]-p0[0])*t
                y = p0[1] + (p1[1]-p0[1])*t
                # offset to the right of the direction of travel -- opposing
                # traffic on the same edge travels the reverse tangent, so it
                # is automatically pushed into the other half of the road
                if d:
                    nx, ny = (p1[1]-p0[1]) / d, -(p1[0]-p0[0]) / d
                else:
                    nx, ny = 0.0, 0.0
                return (x + nx * LANE_OFFSET, y + ny * LANE_OFFSET)
            acc += d
        return self.seg_points[-1]

def compute_following_gaps(vehicles):
    """Group vehicles by (edge, direction) lane and return, for every vehicle
    that has one ahead of it in the same lane, the gap distance (px) to that
    lead vehicle. A vehicle with no entry here has open road ahead."""
    lanes = {}
    for v in vehicles:
        if v.seg_eidx is None or v.seg_len <= 0:
            continue
        lanes.setdefault((v.seg_eidx, v.curr_node), []).append(v)

    gaps = {}
    for lane_vehicles in lanes.values():
        lane_vehicles.sort(key=lambda vv: vv.progress, reverse=True)
        for i in range(1, len(lane_vehicles)):
            ahead, behind = lane_vehicles[i - 1], lane_vehicles[i]
            gaps[behind] = (ahead.progress - behind.progress) * behind.seg_len
    return gaps

# ============================================================
# 5. OPTIMIZATION CONTROLLER
# ============================================================
# Each hub in HUB_IDS is a physically separate junction (they sit in different
# parts of the map), so they are controlled INDEPENDENTLY -- one hub going
# green does not force the others red. Every hub actuates on its own live
# queue load, and a Particle Swarm Optimization pass periodically retunes how
# much green time each hub deserves given the *current* network-wide demand,
# instead of every junction sharing one fixed-length cycle.
lights = {hid: RealLifeTrafficLight(hid) for hid in HUB_IDS}
hub_load_ema = {hid: {"A": 0.0, "B": 0.0} for hid in HUB_IDS}

DETECT_RADIUS = 150.0      # distance (px) at which an approaching vehicle starts counting toward a hub's load
EMA_ALPHA = 0.2            # smoothing factor so single-frame noise doesn't flicker the lights
EMERGENCY_PREEMPT_DIST = 120.0

PSO_PARTICLES = 16
PSO_ITERS = 12
PSO_W, PSO_C1, PSO_C2 = 0.6, 1.4, 1.4

def compute_hub_loads(vehicles):
    """Continuous per-phase demand estimate per hub: closer, non-emergency
    vehicles weigh more, and are bucketed into whichever of the two crossing
    roads (phase A or B) their approach direction belongs to."""
    raw = {hid: {"A": 0.0, "B": 0.0} for hid in HUB_IDS}
    for v in vehicles:
        if v.is_emergency or v.next_node not in raw:
            continue
        dist = (1.0 - v.progress) * calculate_dist(POINTS[v.curr_node], POINTS[v.next_node])
        if dist < DETECT_RADIUS:
            phase = HUB_PHASE_OF_NEIGHBOR[v.next_node].get(v.curr_node)
            if phase is not None:
                raw[v.next_node][phase] += 1.0 - (dist / DETECT_RADIUS)
    return raw

def apply_emergency_preemption(vehicles):
    """Force-green only the specific hub+phase an emergency vehicle is approaching."""
    preempted = set()
    for v in vehicles:
        if v.is_emergency and v.next_node in lights:
            dist = (1.0 - v.progress) * calculate_dist(POINTS[v.curr_node], POINTS[v.next_node])
            if dist < EMERGENCY_PREEMPT_DIST:
                tl = lights[v.next_node]
                phase = tl.neighbor_phase.get(v.curr_node)
                if phase is not None:
                    tl.request_emergency(phase)
                    preempted.add(v.next_node)
    return preempted

def _pso_cost(vec, hubs, loads):
    """Lower is better: heavy queues pay a delay penalty for short green,
    light/empty queues pay an economy penalty for hogging green time."""
    total = 0.0
    for i, h in enumerate(hubs):
        load = loads.get(h, 0.0)
        green = vec[i]
        total += (load / green) * 12.0 + 0.15 * green
        if load < 0.15:
            total += green * 0.4
    return total

def pso_optimize_green_times(loads):
    """Particle Swarm Optimization over per-hub green-time allocation.
    Searches the [MIN_GREEN_TIME, MAX_GREEN_TIME] box for the green-time
    vector that minimizes estimated network delay given current hub loads."""
    hubs = HUB_IDS
    n = len(hubs)
    lo, hi = MIN_GREEN_TIME, MAX_GREEN_TIME

    positions = [[random.uniform(lo, hi) for _ in range(n)] for _ in range(PSO_PARTICLES)]
    velocities = [[0.0] * n for _ in range(PSO_PARTICLES)]
    pbest = [list(p) for p in positions]
    pbest_cost = [_pso_cost(p, hubs, loads) for p in positions]
    gbest_idx = min(range(PSO_PARTICLES), key=lambda i: pbest_cost[i])
    gbest = list(pbest[gbest_idx])
    gbest_cost = pbest_cost[gbest_idx]

    for _ in range(PSO_ITERS):
        for i in range(PSO_PARTICLES):
            for d in range(n):
                r1, r2 = random.random(), random.random()
                velocities[i][d] = (PSO_W * velocities[i][d]
                                     + PSO_C1 * r1 * (pbest[i][d] - positions[i][d])
                                     + PSO_C2 * r2 * (gbest[d] - positions[i][d]))
                positions[i][d] = min(hi, max(lo, positions[i][d] + velocities[i][d]))
            c = _pso_cost(positions[i], hubs, loads)
            if c < pbest_cost[i]:
                pbest[i] = list(positions[i])
                pbest_cost[i] = c
                if c < gbest_cost:
                    gbest = list(positions[i])
                    gbest_cost = c

    return {h: gbest[i] for i, h in enumerate(hubs)}

WEIGHT_BOUNDS = {"load": (0.2, 3.0), "wait": (0.0, 1.0)}

def _signal_weight_cost(vec):
    """Lower is better. For every hub and every ordered (loser, winner) phase
    pair under this (load_weight, wait_weight) choice, charge a penalty equal
    to the loser's own queue load times how badly it lost the arbitration.
    A heavily-loaded phase that keeps losing to a lightly-loaded one is
    exactly the "wrong" outcome this is meant to punish."""
    lw, ww = vec
    total = 0.0
    for h in HUB_IDS:
        loads = hub_load_ema[h]
        waits = lights[h].wait_time
        for p, q in (("A", "B"), ("B", "A")):
            score_p = loads[p] * lw + waits[p] * ww
            score_q = loads[q] * lw + waits[q] * ww
            if score_q > score_p:
                total += loads[p] * (score_q - score_p)
    return total

def pso_optimize_signal_weights():
    """Particle Swarm Optimization over the two decision weights (how much a
    phase's own queue load matters vs. how long it has been waiting) that
    every hub uses to decide when the red side should get the green. Tuned
    from live, network-wide load/wait data instead of being fixed constants."""
    global LOAD_WEIGHT, WAIT_WEIGHT
    dims = ["load", "wait"]
    lo = [WEIGHT_BOUNDS[d][0] for d in dims]
    hi = [WEIGHT_BOUNDS[d][1] for d in dims]
    n = len(dims)

    positions = [[random.uniform(lo[d], hi[d]) for d in range(n)] for _ in range(PSO_PARTICLES)]
    velocities = [[0.0] * n for _ in range(PSO_PARTICLES)]
    pbest = [list(p) for p in positions]
    pbest_cost = [_signal_weight_cost(p) for p in positions]
    gbest_idx = min(range(PSO_PARTICLES), key=lambda i: pbest_cost[i])
    gbest = list(pbest[gbest_idx])
    gbest_cost = pbest_cost[gbest_idx]

    for _ in range(PSO_ITERS):
        for i in range(PSO_PARTICLES):
            for d in range(n):
                r1, r2 = random.random(), random.random()
                velocities[i][d] = (PSO_W * velocities[i][d]
                                     + PSO_C1 * r1 * (pbest[i][d] - positions[i][d])
                                     + PSO_C2 * r2 * (gbest[d] - positions[i][d]))
                positions[i][d] = min(hi[d], max(lo[d], positions[i][d] + velocities[i][d]))
            c = _signal_weight_cost(positions[i])
            if c < pbest_cost[i]:
                pbest[i] = list(positions[i])
                pbest_cost[i] = c
                if c < gbest_cost:
                    gbest = list(positions[i])
                    gbest_cost = c

    LOAD_WEIGHT, WAIT_WEIGHT = gbest[0], gbest[1]

def update_hub_loads(vehicles):
    raw = compute_hub_loads(vehicles)
    for h in HUB_IDS:
        for phase in ("A", "B"):
            hub_load_ema[h][phase] = (1.0 - EMA_ALPHA) * hub_load_ema[h][phase] + EMA_ALPHA * raw[h][phase]
        lights[h].load = dict(hub_load_ema[h])

def run_signal_actuation(vehicles):
    """Frequent, cheap pass: decide who gets to request green right now.
    Whichever phase is under-served (or currently active with real demand)
    keeps requesting green; the perpendicular phase stays red until its turn."""
    preempted = apply_emergency_preemption(vehicles)
    for h in HUB_IDS:
        if h in preempted:
            continue
        total_load = hub_load_ema[h]["A"] + hub_load_ema[h]["B"]
        lights[h].set_target(total_load > GREEN_REQUEST_THRESHOLD)

def run_pso_retune():
    """Infrequent, heavier pass: re-optimize each hub's safety-cap green-time
    budget, and re-tune the shared load/wait decision weights that actually
    drive every phase switch, both from live network-wide demand."""
    totals = {h: hub_load_ema[h]["A"] + hub_load_ema[h]["B"] for h in HUB_IDS}
    green_times = pso_optimize_green_times(totals)
    for h, g in green_times.items():
        lights[h].max_green = g
    pso_optimize_signal_weights()

# ============================================================
# 6. MAIN SIMULATION LOOP
# ============================================================
INITIAL_VEHICLES = 18
MAX_VEHICLES = 65
# Vehicles spawn at a random origin and vanish on arrival (they don't loop
# forever), and arrivals come at randomized intervals -- so the number of
# vehicles converging on any one approach rises and falls over time instead
# of holding at a constant, evenly-spread level. The spawn rate is tuned to
# what 3 signalized intersections can actually keep flowing: pushed too high
# (as it previously was), the network oversaturates and most of the fleet
# sits queued at all times no matter how good the signal logic is -- that's
# a demand problem, not a controller problem.
SPAWN_INTERVAL_RANGE = (0.35, 0.9)
EMERGENCY_SPAWN_RANGE = (10.0, 20.0)
ACTUATION_INTERVAL = 0.4   # how often signals re-check live demand
PSO_INTERVAL = 2.5         # how often the PSO retunes green-time budgets and decision weights

ROAD_WIDTH = 10            # widened so it visually reads as a 2-lane road

def draw_dashed_centerline(screen, pts, color=(255, 255, 255), dash_len=6, gap_len=6):
    for i in range(1, len(pts)):
        p0, p1 = pts[i - 1], pts[i]
        seg_len = calculate_dist(p0, p1)
        if seg_len == 0:
            continue
        dx, dy = (p1[0] - p0[0]) / seg_len, (p1[1] - p0[1]) / seg_len
        dist, draw = 0.0, True
        while dist < seg_len:
            step = dash_len if draw else gap_len
            seg_end = min(dist + step, seg_len)
            if draw:
                sx, sy = p0[0] + dx * dist, p0[1] + dy * dist
                ex, ey = p0[0] + dx * seg_end, p0[1] + dy * seg_end
                pygame.draw.line(screen, color, (sx, sy), (ex, ey), 1)
            dist = seg_end
            draw = not draw

# ------------------------------------------------------------
# Elevated, pole-mounted signal heads (rendering only)
# ------------------------------------------------------------
# The raw HUB_LIGHTS coordinates sit right on the road centerline, which is
# what made signals look "mixed into" the road. For drawing only (this does
# not touch the coordinates used for phase geometry/detection), each signal
# is anchored to the NEAREST point on the hub's actual road geometry (not an
# offset guessed from the hub center, which can drift far from the pavement
# wherever a road bends sharply near the hub) and nudged a few px sideways,
# then drawn as a small pole + lamp housing standing above that point with a
# ground shadow -- a simple 2D trick ("draw it higher on screen, shadow it on
# the ground") that reads as a traffic light standing at height above the
# road instead of a flat dot painted on the pavement.
SIGNAL_LATERAL_OFFSET = 7    # px, sideways -- just enough to clear both travel lanes (each only ~3.5px off center)
POLE_HEIGHT = 16
HOUSING_W, HOUSING_H = 10, 20
LAMP_RADIUS = 3
LAMP_GAP = 6

LAMP_ORDER = ["red", "yellow", "green"]
LAMP_LIT_COLOR = {"red": (239, 68, 68), "yellow": (234, 179, 8), "green": (34, 197, 94)}
LAMP_DIM_COLOR = {"red": (95, 45, 45), "yellow": (95, 85, 35), "green": (40, 75, 50)}

def _closest_point_on_segment(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    length2 = dx * dx + dy * dy
    if length2 == 0:
        return a
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length2))
    return (ax + dx * t, ay + dy * t)

def _nearest_road_anchor(hub_id, ref_point):
    """Nearest point (and local road direction) on any road segment touching
    this hub, to `ref_point`. Anchoring here -- instead of to a fixed offset
    from the hub center -- guarantees the signal always hugs real pavement
    even when the hand-authored dot position doesn't track a sharp bend."""
    best_dist, best_pt, best_dir = None, None, (1.0, 0.0)
    for neighbor, eidx, _ in adj[hub_id]:
        pts = edge_points(eidx, hub_id)
        for i in range(1, len(pts)):
            a, b = pts[i - 1], pts[i]
            cp = _closest_point_on_segment(ref_point, a, b)
            d = calculate_dist(ref_point, cp)
            if best_dist is None or d < best_dist:
                seg_len = calculate_dist(a, b) or 1.0
                best_dist, best_pt = d, cp
                best_dir = ((b[0] - a[0]) / seg_len, (b[1] - a[1]) / seg_len)
    return (best_pt if best_pt is not None else ref_point), best_dir

def _signal_render_anchor(hub_id, dot_idx):
    """Ground-contact point for a signal head's pole: the nearest spot on the
    hub's actual road geometry to its (hand-authored, approximate) dot, then
    nudged sideways off that road's own direction so it clears the lane."""
    base = tuple(HUB_LIGHTS[hub_id][dot_idx])
    road_pt, (dx, dy) = _nearest_road_anchor(hub_id, base)
    px, py = dy, -dx    # perpendicular to the road at that point
    return (road_pt[0] + px * SIGNAL_LATERAL_OFFSET,
            road_pt[1] + py * SIGNAL_LATERAL_OFFSET)

def draw_signal_head(screen, base_pos, state):
    bx, by = int(base_pos[0]), int(base_pos[1])
    pole_top_y = by - POLE_HEIGHT

    # Ground shadow implies the housing above is standing at a height, not lying flat
    shadow = pygame.Surface((12, 6), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
    screen.blit(shadow, (bx - 6, by - 3))

    pygame.draw.line(screen, (70, 70, 70), (bx, by), (bx, pole_top_y), 3)

    housing = pygame.Rect(0, 0, HOUSING_W, HOUSING_H)
    housing.midbottom = (bx, pole_top_y)
    pygame.draw.rect(screen, (28, 28, 32), housing, border_radius=3)
    pygame.draw.rect(screen, (10, 10, 10), housing, 1, border_radius=3)

    lamp_y = housing.top + 5
    for name in LAMP_ORDER:
        lit = (name == state)
        color = LAMP_LIT_COLOR[name] if lit else LAMP_DIM_COLOR[name]
        if lit:
            glow = pygame.Surface((LAMP_RADIUS * 5, LAMP_RADIUS * 5), pygame.SRCALPHA)
            gc = LAMP_RADIUS * 5 // 2
            pygame.draw.circle(glow, (*color, 90), (gc, gc), gc)
            screen.blit(glow, (housing.centerx - gc, lamp_y - gc))
        pygame.draw.circle(screen, color, (housing.centerx, lamp_y), LAMP_RADIUS)
        lamp_y += LAMP_GAP

def main():
    pygame.init()
    screen = pygame.display.set_mode((927, 740))
    pygame.display.set_caption("Smart Adaptive Traffic Control (PSO)")
    clock = pygame.time.Clock()

    vehicles = [Vehicle(i, is_emergency=(i < 2)) for i in range(INITIAL_VEHICLES)]
    next_vehicle_idx = INITIAL_VEHICLES
    actuation_timer = 0.0
    pso_timer = 0.0
    spawn_timer = 0.0
    next_spawn_at = random.uniform(*SPAWN_INTERVAL_RANGE)
    emergency_timer = 0.0
    next_emergency_at = random.uniform(*EMERGENCY_SPAWN_RANGE)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        actuation_timer += dt
        pso_timer += dt
        spawn_timer += dt
        emergency_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # New vehicles arrive from random origins at randomized intervals, and
        # completed trips are pruned below -- together this makes the fleet
        # (and therefore each hub's load) rise and fall unpredictably instead
        # of holding at one fixed, evenly-spread vehicle count.
        if spawn_timer >= next_spawn_at and len(vehicles) < MAX_VEHICLES:
            vehicles.append(Vehicle(next_vehicle_idx, is_emergency=False))
            next_vehicle_idx += 1
            spawn_timer = 0.0
            next_spawn_at = random.uniform(*SPAWN_INTERVAL_RANGE)

        if emergency_timer >= next_emergency_at and len(vehicles) < MAX_VEHICLES:
            vehicles.append(Vehicle(next_vehicle_idx, is_emergency=True))
            next_vehicle_idx += 1
            emergency_timer = 0.0
            next_emergency_at = random.uniform(*EMERGENCY_SPAWN_RANGE)

        # Live demand is tracked every frame so the EMA stays responsive
        update_hub_loads(vehicles)

        if actuation_timer >= ACTUATION_INTERVAL:
            run_signal_actuation(vehicles)
            actuation_timer = 0.0

        if pso_timer >= PSO_INTERVAL:
            run_pso_retune()
            pso_timer = 0.0

        for tl in lights.values():
            tl.update(dt)
        following_gaps = compute_following_gaps(vehicles)
        for v in vehicles:
            v.update(dt, following_gaps.get(v))
        vehicles = [v for v in vehicles if v.active]

        screen.fill((245, 245, 247))

        # Roads -- widened surface with a dashed centerline to read as a 2-lane road
        for e in EDGES:
            pygame.draw.lines(screen, (70, 70, 70), False, e["pts"], ROAD_WIDTH)
            draw_dashed_centerline(screen, e["pts"])

        # Spawn Nodes
        for nid in RED_IDS:
            n = NODES[nid]
            pygame.draw.circle(screen, (220, 38, 38), (int(n["x"]), int(n["y"])), 6)

        # Traffic Lights -- rendered as pole-mounted signal heads standing above
        # the road (own phase per head), instead of flat dots on the pavement
        for hub_id, dots in HUB_LIGHTS.items():
            tl = lights[hub_id]
            for idx in range(len(dots)):
                anchor = _signal_render_anchor(hub_id, idx)
                draw_signal_head(screen, anchor, tl.dot_state(idx))

        # Vehicles
        for v in vehicles:
            x, y = v.pos
            pygame.draw.circle(screen, v.color, (int(x), int(y)), 7 if v.is_emergency else 5)
            pygame.draw.circle(screen, (0, 0, 0), (int(x), int(y)), 7 if v.is_emergency else 5, 1)
            if v.waiting:
                pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), 2)

        # Simple border frame around the play area for a neat, contained look
        pygame.draw.rect(screen, (60, 60, 60), screen.get_rect(), width=3)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()