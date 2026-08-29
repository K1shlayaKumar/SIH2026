"""
Fixed-time traffic signal simulation -- a demonstration counterpart to
road_simulation.py.

road_simulation.py controls its intersections adaptively: which phase gets
green, and for how long, is driven by live opposite-side vehicle load plus
how long that side has been waiting (see RoadSimulationReadme.md).

This script uses the SAME road network, vehicle model, two-lane rendering,
and car-following logic, but every hub instead cycles its two phases on a
plain fixed-duration timer -- phase A gets exactly `--fixed-time` seconds of
green, then phase B gets exactly `--fixed-time` seconds, forever, regardless
of how many vehicles are waiting on either side. Running both scripts side
by side (ideally with the same vehicle spawn settings) is meant to make the
difference between "signals on a clock" and "signals that read the road"
visible.

Usage:
    python road_simulation_fixedtime.py                 # default 15s per phase
    python road_simulation_fixedtime.py --fixed-time 25
    python road_simulation_fixedtime.py -t 8
"""
import argparse
import json
import math
import random
import heapq
import pygame

# ============================================================
# 1. GRAPH DATA & EXTRACTION (identical to road_simulation.py)
# ============================================================
GRAPH_DATA_JSON = r'''
{"nodes": {"H1": {"x": 250.0, "y": 370.0, "type": "light"}, "H2": {"x": 480.0, "y": 370.0, "type": "light"}, "H3": {"x": 710.0, "y": 370.0, "type": "light"}, "W": {"x": 60.0, "y": 370.0, "type": "red"}, "E": {"x": 900.0, "y": 370.0, "type": "red"}, "N1": {"x": 250.0, "y": 120.0, "type": "red"}, "S1": {"x": 250.0, "y": 650.0, "type": "red"}, "N2": {"x": 480.0, "y": 120.0, "type": "red"}, "S2": {"x": 480.0, "y": 650.0, "type": "red"}, "N3": {"x": 710.0, "y": 120.0, "type": "red"}, "S3": {"x": 710.0, "y": 650.0, "type": "red"}}, "edges": [{"a": "W", "b": "H1", "pts": [[60.0, 370.0], [250.0, 370.0]]}, {"a": "H1", "b": "H2", "pts": [[250.0, 370.0], [480.0, 370.0]]}, {"a": "H2", "b": "H3", "pts": [[480.0, 370.0], [710.0, 370.0]]}, {"a": "H3", "b": "E", "pts": [[710.0, 370.0], [900.0, 370.0]]}, {"a": "H1", "b": "N1", "pts": [[250.0, 370.0], [250.0, 120.0]]}, {"a": "H1", "b": "S1", "pts": [[250.0, 370.0], [250.0, 650.0]]}, {"a": "H2", "b": "N2", "pts": [[480.0, 370.0], [480.0, 120.0]]}, {"a": "H2", "b": "S2", "pts": [[480.0, 370.0], [480.0, 650.0]]}, {"a": "H3", "b": "N3", "pts": [[710.0, 370.0], [710.0, 120.0]]}, {"a": "H3", "b": "S3", "pts": [[710.0, 370.0], [710.0, 650.0]]}], "hub_lights": {"H1": [[250.0, 344.0], [250.0, 396.0], [276.0, 370.0], [224.0, 370.0]], "H2": [[480.0, 344.0], [480.0, 396.0], [506.0, 370.0], [454.0, 370.0]], "H3": [[710.0, 344.0], [710.0, 396.0], [736.0, 370.0], [684.0, 370.0]]}}
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
# 2. ROUTING & GRAPH UTILITIES (identical to road_simulation.py)
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
# 3. FIXED-TIME TRAFFIC LIGHT CONTROLLER
# ============================================================
# Same physical 2-phase intersection model as road_simulation.py (each hub's
# 4 signal dots belong to two crossing roads, only one phase green at a
# time), but the switching decision here ignores load and wait time
# entirely: each phase simply gets `fixed_green_time` seconds, then the
# other phase gets `fixed_green_time` seconds, forever.
YELLOW_TIME = 2.0
ALL_RED_TIME = 1.0
DEFAULT_FIXED_GREEN_TIME = 15.0

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

class FixedTimeTrafficLight:
    """A 2-phase intersection controller that ignores demand entirely: each
    phase gets exactly `fixed_green_time` seconds of green, then yields to
    the other phase, on an unconditional round-robin -- the classic
    "signals on a clock" behavior this script exists to demonstrate."""
    def __init__(self, hub_id, fixed_green_time):
        self.hub_id = hub_id
        self.phase_dots = HUB_PHASE_DOTS[hub_id]
        self.neighbor_phase = HUB_PHASE_OF_NEIGHBOR[hub_id]
        self.fixed_green_time = fixed_green_time
        self.active = "A"          # which phase currently owns the green/yellow cycle
        self.state = "red"         # state of the ACTIVE phase; the other phase is always red
        self.timer = 0.0
        self.load = {"A": 0.0, "B": 0.0}   # for HUD/comparison display ONLY -- never read by update()

    def _other(self):
        return "B" if self.active == "A" else "A"

    def update(self, dt):
        self.timer += dt
        if self.state == "green" and self.timer >= self.fixed_green_time:
            self.state = "yellow"
            self.timer = 0.0
        elif self.state == "yellow" and self.timer >= YELLOW_TIME:
            self.state = "red"
            self.timer = 0.0
        elif self.state == "red" and self.timer >= ALL_RED_TIME:
            # unconditional round-robin -- no load/wait comparison of any kind
            self.active = self._other()
            self.state = "green"
            self.timer = 0.0

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
# 4. VEHICLE SIMULATION CLASS (identical to road_simulation.py)
# ============================================================
# Roads are modeled as two lanes (one per direction of travel): each vehicle
# renders offset to the right of its own direction of travel, and vehicles
# travelling the same direction on the same edge car-follow (no overtaking).
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
# 5. LOAD TRACKING (for HUD/comparison display only)
# ============================================================
# road_simulation.py uses this same measurement to DECIDE which phase gets
# green. Here it is computed purely so the on-screen HUD can show "look how
# much load is waiting" next to a signal that is about to switch anyway on
# its fixed schedule, regardless of that number. There is deliberately no
# actuation, no PSO, and no emergency preemption in this script -- a fixed-
# time controller reacts to nothing.
lights = {}   # populated in main() once the configured fixed_green_time is known
hub_load_ema = {hid: {"A": 0.0, "B": 0.0} for hid in HUB_IDS}

DETECT_RADIUS = 150.0
EMA_ALPHA = 0.2

def compute_hub_loads(vehicles):
    """Continuous per-phase demand estimate per hub, for display purposes only."""
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

def update_hub_loads(vehicles):
    raw = compute_hub_loads(vehicles)
    for h in HUB_IDS:
        for phase in ("A", "B"):
            hub_load_ema[h][phase] = (1.0 - EMA_ALPHA) * hub_load_ema[h][phase] + EMA_ALPHA * raw[h][phase]
        lights[h].load = dict(hub_load_ema[h])

# ============================================================
# 6. MAIN SIMULATION LOOP
# ============================================================
INITIAL_VEHICLES = 18
MAX_VEHICLES = 65
# Same spawn/despawn model as road_simulation.py so the two scripts are a
# fair side-by-side comparison of signal POLICY, not of traffic volume.
SPAWN_INTERVAL_RANGE = (0.35, 0.9)
EMERGENCY_SPAWN_RANGE = (10.0, 20.0)

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
# is pushed a little further out and to the side of its approach, then drawn
# as a small pole + lamp housing standing above that point with a ground
# shadow -- a simple 2D trick ("draw it higher on screen, shadow it on the
# ground") that reads as a traffic light standing at height above the road
# instead of a flat dot painted on the pavement.
SIGNAL_OUTWARD_OFFSET = 10   # px, pushes the head further from the hub center
SIGNAL_LATERAL_OFFSET = 15   # px, sideways -- clear of both travel lanes (each only ~3.5px off center)
POLE_HEIGHT = 16
HOUSING_W, HOUSING_H = 10, 20
LAMP_RADIUS = 3
LAMP_GAP = 6

LAMP_ORDER = ["red", "yellow", "green"]
LAMP_LIT_COLOR = {"red": (239, 68, 68), "yellow": (234, 179, 8), "green": (34, 197, 94)}
LAMP_DIM_COLOR = {"red": (95, 45, 45), "yellow": (95, 85, 35), "green": (40, 75, 50)}

def _signal_render_anchor(hub_id, dot_idx):
    """Ground-contact point for a signal head's pole, offset off the road
    centerline so the elevated sprite doesn't sit on top of traffic."""
    cx, cy = POINTS[hub_id]
    dx0, dy0 = HUB_LIGHTS[hub_id][dot_idx]
    vx, vy = dx0 - cx, dy0 - cy
    dist = math.hypot(vx, vy) or 1.0
    ux, uy = vx / dist, vy / dist       # outward, along the approach
    px, py = uy, -ux                     # perpendicular, away from the incoming travel lane
    return (dx0 + ux * SIGNAL_OUTWARD_OFFSET + px * SIGNAL_LATERAL_OFFSET,
            dy0 + uy * SIGNAL_OUTWARD_OFFSET + py * SIGNAL_LATERAL_OFFSET)

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

def parse_args():
    parser = argparse.ArgumentParser(
        description="Fixed-time traffic signal simulation (demonstration counterpart to road_simulation.py).")
    parser.add_argument(
        "--fixed-time", "-t", type=float, default=DEFAULT_FIXED_GREEN_TIME,
        help=f"Green duration (seconds) given to each phase before switching, "
             f"unconditionally, regardless of load (default: {DEFAULT_FIXED_GREEN_TIME:.0f}).")
    args = parser.parse_args()
    if args.fixed_time <= 0:
        parser.error("--fixed-time must be a positive number of seconds")
    return args

def main():
    args = parse_args()
    fixed_green_time = args.fixed_time

    global lights
    lights = {hid: FixedTimeTrafficLight(hid, fixed_green_time) for hid in HUB_IDS}

    pygame.init()
    screen = pygame.display.set_mode((927, 740))
    pygame.display.set_caption(f"Fixed-Time Traffic Control (T={fixed_green_time:.0f}s per phase)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 14)
    small_font = pygame.font.SysFont("Arial", 12)

    vehicles = [Vehicle(i, is_emergency=(i < 2)) for i in range(INITIAL_VEHICLES)]
    next_vehicle_idx = INITIAL_VEHICLES
    spawn_timer = 0.0
    next_spawn_at = random.uniform(*SPAWN_INTERVAL_RANGE)
    emergency_timer = 0.0
    next_emergency_at = random.uniform(*EMERGENCY_SPAWN_RANGE)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        spawn_timer += dt
        emergency_timer += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

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

        # Tracked for HUD comparison only -- does NOT influence tl.update() below
        update_hub_loads(vehicles)

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
            label_x, label_y = dots[0][0] + 14, dots[0][1] - 46
            stats = small_font.render(
                f"{tl.active}:{tl.state} {tl.timer:.1f}s/fixed{tl.fixed_green_time:.0f}s "
                f"A{tl.load['A']:.1f} B{tl.load['B']:.1f}",
                True, (20, 20, 20))
            screen.blit(stats, (label_x, label_y))

        # Vehicles
        for v in vehicles:
            x, y = v.pos
            pygame.draw.circle(screen, v.color, (int(x), int(y)), 7 if v.is_emergency else 5)
            pygame.draw.circle(screen, (0, 0, 0), (int(x), int(y)), 7 if v.is_emergency else 5, 1)
            if v.waiting:
                pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), 2)

        # HUD
        hud = font.render(
            f"FIXED-TIME MODE: every phase gets {fixed_green_time:.0f}s regardless of load | "
            f"Vehicles: {len(vehicles)}",
            True, (40, 40, 40))
        screen.blit(hud, (10, 10))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
