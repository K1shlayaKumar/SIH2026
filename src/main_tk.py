import tkinter as tk
import math
import random
import json
import numpy as np

import queue
import threading
from concurrent.futures import ThreadPoolExecutor

from qpso_algo import metaheuristic_qpso_route, qpso_optimize_traffic_lights, calculate_dist

# ============================================================
# 1. AUTO-SNAP GRAPH & POLYLINE BUILDER
# ============================================================
try:
    with open("map_coordinates.json", "r") as f:
        map_data = json.load(f)
except FileNotFoundError:
    print("ERROR: map_coordinates.json not found! Please run map_extractor.py first.")
    exit()

img_w = map_data["image_size"]["width"]
img_h = map_data["image_size"]["height"]

scale_x = 100.0 / img_w
scale_y = 100.0 / img_h

raw_points = {}
road_geometry_raw = {}
roads_list = []

# A. Extract Nodes and Polylines
for route in map_data["road_routes"]:
    start_id = f"J{route['start_node']}"
    end_id = f"J{route['end_node']}"

    # Scale all waypoints to 0-100 physics grid
    scaled_coords = [(pt[0] * scale_x, pt[1] * scale_y) for pt in route["coordinates"]]

    raw_points[start_id] = scaled_coords[0]
    raw_points[end_id] = scaled_coords[-1]

    # Store path for both directions for rendering and physics
    road_geometry_raw[(start_id, end_id)] = scaled_coords
    road_geometry_raw[(end_id, start_id)] = list(reversed(scaled_coords))
    roads_list.append((start_id, end_id))

# B. Snap Destinations to Nearest Node
all_destinations = []
points = {}
dest_mapping = {}

for d in map_data["destinations"]:
    dx, dy = d["coordinate"][0] * scale_x, d["coordinate"][1] * scale_y
    closest_node = min(raw_points.keys(), key=lambda k: math.hypot(raw_points[k][0] - dx, raw_points[k][1] - dy))

    dest_id = d["id"]
    dest_mapping[closest_node] = dest_id
    points[dest_id] = raw_points.pop(closest_node)
    all_destinations.append(dest_id)

for k, v in raw_points.items():
    points[k] = v

# Update road geometry with the new Destination IDs
road_geometry = {}
roads = []
for (u, v), polyline in road_geometry_raw.items():
    u_new = dest_mapping.get(u, u)
    v_new = dest_mapping.get(v, v)
    road_geometry[(u_new, v_new)] = polyline
    if (u_new, v_new) not in roads and (v_new, u_new) not in roads:
        roads.append((u_new, v_new))

# C. Snap Traffic Lights to Nearest Node
traffic_lights = {}
for tl in map_data["traffic_lights"]:
    tx, ty = tl["coordinate"][0] * scale_x, tl["coordinate"][1] * scale_y
    closest_node = min(points.keys(), key=lambda k: math.hypot(points[k][0] - tx, points[k][1] - ty))
    traffic_lights[closest_node] = {"state": "RED", "pos": points[closest_node]}


def get_edge_length(u, v):
    """Calculates the true physical length of a curved polyline road."""
    edge = (u, v)
    if edge in road_geometry:
        polyline = road_geometry[edge]
        return sum(math.hypot(polyline[i + 1][0] - polyline[i][0], polyline[i + 1][1] - polyline[i][1]) for i in
                   range(len(polyline) - 1))
    return calculate_dist(points[u], points[v])


# ============================================================
# 2. FLEET SETTINGS & MULTI-THREADING
# ============================================================
NUM_VEHICLES = 30
LANE_OFFSET = 0.9  # Reduced slightly for curvy roads
COLLISION_RADIUS = 2.8
STOP_LINE_DISTANCE = 3.2

VEHICLE_COLORS = ["#e11d48", "#2563eb", "#d97706", "#7c3aed", "#059669", "#ea580c", "#0891b2", "#4f46e5",
                  "#c026d3", "#16a34a", "#b45309", "#0369a1", "#9d174d", "#4338ca", "#047857", "#be123c",
                  "#fbbf24", "#34d399", "#818cf8", "#f472b6", "#a78bfa", "#2dd4bf", "#f87171", "#60a5fa"]

thread_pool = ThreadPoolExecutor(max_workers=8)
signal_ai_queue = queue.Queue()
reroute_queue = queue.Queue()


def async_signal_optimization(v_list, tl_dict, pts):
    best_state = qpso_optimize_traffic_lights(v_list, tl_dict, pts)
    signal_ai_queue.put(best_state)


def async_vehicle_reroute(vid, next_node, target, tl_dict):
    new_subpath = metaheuristic_qpso_route(next_node, target, tl_dict, points, roads)
    reroute_queue.put((vid, new_subpath))


# ============================================================
# 3. IDM PHYSICS (POLYLINE INTERPOLATION UPGRADE)
# ============================================================
class Vehicle:
    def __init__(self, vehicle_id):
        self.id = vehicle_id
        self.color = VEHICLE_COLORS[vehicle_id % len(VEHICLE_COLORS)]

        self.v0 = random.uniform(0.35, 0.60)
        self.v = 0.0
        self.a_max = 0.04
        self.b = 0.08
        self.T = 4.0
        self.s0 = 3.5

        self.active = True
        self.is_rerouting = False

        self.start = random.choice(all_destinations) if all_destinations else list(points.keys())[0]
        choices = [d for d in all_destinations if d != self.start]
        self.target = random.choice(choices) if choices else self.start

        self.path = metaheuristic_qpso_route(self.start, self.target, traffic_lights, points, roads)
        self.segment_idx = 0
        self.progress = 0.0
        self.x, self.y = self.get_projected_coords(0.0)

    @property
    def curr_node(self):
        return self.path[self.segment_idx]

    @property
    def next_node(self):
        return self.path[self.segment_idx + 1] if self.segment_idx + 1 < len(self.path) else None

    def get_projected_coords(self, prog):
        """Calculates precise physical position dynamically along curved waypoints."""
        if self.next_node is None: return points[self.curr_node]

        edge = (self.curr_node, self.next_node)
        polyline = road_geometry.get(edge, [points[self.curr_node], points[self.next_node]])

        segment_lengths = []
        total_len = 0.0
        for i in range(len(polyline) - 1):
            p1, p2 = polyline[i], polyline[i + 1]
            d = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
            segment_lengths.append(d)
            total_len += d

        if total_len == 0:
            return polyline[0][0], polyline[0][1]

        target_dist = prog * total_len
        accumulated = 0.0

        # Traverse the polyline segments to find current location
        for i in range(len(segment_lengths)):
            seg_d = segment_lengths[i]
            if accumulated + seg_d >= target_dist - 1e-9:
                local_prog = (target_dist - accumulated) / seg_d if seg_d > 0 else 0
                p1, p2 = polyline[i], polyline[i + 1]
                dx, dy = p2[0] - p1[0], p2[1] - p1[1]
                dist = math.hypot(dx, dy)
                if dist == 0: return p1

                # Apply Lane Offset perfectly normal to the current micro-curve
                nx, ny = dy / dist, -dx / dist
                return (p1[0] + dx * local_prog) + nx * LANE_OFFSET, (p1[1] + dy * local_prog) + ny * LANE_OFFSET
            accumulated += seg_d

        # Fallback to absolute end
        p1, p2 = polyline[-2], polyline[-1]
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        dist = math.hypot(dx, dy)
        nx, ny = (dy / dist, -dx / dist) if dist > 0 else (0, 0)
        return p2[0] + nx * LANE_OFFSET, p2[1] + ny * LANE_OFFSET

    def step(self, all_vehicles, speed_mult):
        if not self.active: return
        if self.next_node is None:
            self.active = False
            return

        seg_dist = get_edge_length(self.curr_node, self.next_node)
        if seg_dist == 0:
            self.segment_idx += 1
            return

        s_min = float('inf')
        v_lead = 0.0
        dist_to_junction = (1.0 - self.progress) * seg_dist

        if self.next_node in traffic_lights and traffic_lights[self.next_node]["state"] == "RED":
            s_red = dist_to_junction - STOP_LINE_DISTANCE
            if s_red < s_min:
                s_min = s_red
                v_lead = 0.0

        for other in all_vehicles:
            if not other.active or other.id == self.id: continue
            if self.curr_node == other.curr_node and self.next_node == other.next_node:
                if other.progress > self.progress:
                    s_veh = (other.progress - self.progress) * seg_dist
                    if s_veh < s_min:
                        s_min = s_veh
                        v_lead = other.v
            elif self.next_node == other.next_node and self.id > other.id:
                other_dist_to_junc = (1.0 - other.progress) * get_edge_length(other.curr_node, other.next_node)
                if other_dist_to_junc < COLLISION_RADIUS * 2.5:
                    if dist_to_junction < s_min:
                        s_min = dist_to_junction
                        v_lead = 0.0

        v0_eff = self.v0 * speed_mult
        s_min = max(0.001, s_min)

        if speed_mult == 0.0:
            accel = -self.b * 2.0
            v0_eff = 0.001
        else:
            delta_v = self.v - v_lead
            if s_min == float('inf'):
                accel = self.a_max * (1 - (self.v / v0_eff) ** 4)
            else:
                s_star = self.s0 + max(0.0, self.v * self.T + (self.v * delta_v) / (2 * math.sqrt(self.a_max * self.b)))
                accel = self.a_max * (1 - (self.v / v0_eff) ** 4 - (s_star / s_min) ** 2)

        self.v += accel
        self.v = max(0.0, min(self.v, v0_eff))

        next_prog_test = self.progress + (self.v / seg_dist)
        nx, ny = self.get_projected_coords(next_prog_test)
        for other in all_vehicles:
            if other.active and other.id < self.id and self.curr_node != other.curr_node and self.next_node == other.next_node:
                if calculate_dist((nx, ny), (other.x, other.y)) < COLLISION_RADIUS:
                    self.v = 0.0
                    break

        self.progress += (self.v / seg_dist)

        if self.progress >= 1.0:
            self.progress = 0.0
            self.segment_idx += 1
            if self.segment_idx >= len(self.path) - 1:
                self.active = False
                return
            self.x, self.y = self.get_projected_coords(0.0)
        else:
            self.x, self.y = self.get_projected_coords(self.progress)


# ============================================================
# 4. TKINTER UI
# ============================================================
root = tk.Tk()
root.title("Autonomous Traffic: CV Polyline Extraction")
root.geometry("1250x820")
root.configure(bg="#121212")

canvas = tk.Canvas(root, width=800, height=800, bg="#121212", highlightthickness=0)
canvas.pack(side=tk.LEFT, padx=10, pady=10)

dash_frame = tk.Frame(root, width=420, height=800, bg="#1e1e1e")
dash_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(0, 10), pady=10)

title_lbl = tk.Label(dash_frame, text="CV Custom Map QPSO", font=("Segoe UI", 16, "bold"), fg="white", bg="#1e1e1e")
title_lbl.pack(anchor="w", padx=20, pady=(15, 2))

status_lbl = tk.Label(dash_frame, text="Engine: Background Threading Active", font=("Consolas", 10), fg="#10b981",
                      bg="#1e1e1e")
status_lbl.pack(anchor="w", padx=20, pady=(0, 10))

speed_frame = tk.LabelFrame(dash_frame, text=" Global Speed Adjustment ", font=("Segoe UI", 10, "bold"), fg="#38bdf8",
                            bg="#1e1e1e", padx=10, pady=8)
speed_frame.pack(fill=tk.X, padx=15, pady=5)

speed_val_var = tk.DoubleVar(value=1.0)
speed_text_lbl = tk.Label(speed_frame, text="Multiplier: 1.00x", font=("Consolas", 11, "bold"), fg="#facc15",
                          bg="#1e1e1e")
speed_text_lbl.pack(anchor="w")


def on_slider_change(val):
    speed_text_lbl.config(text=f"Multiplier: {float(val):.2f}x")


speed_slider = tk.Scale(
    speed_frame, from_=0.0, to=3.0, resolution=0.1, orient=tk.HORIZONTAL,
    variable=speed_val_var, command=on_slider_change,
    bg="#1e1e1e", fg="white", highlightthickness=0, troughcolor="#334155", activebackground="#38bdf8"
)
speed_slider.pack(fill=tk.X, pady=(2, 8))

btn_row = tk.Frame(speed_frame, bg="#1e1e1e")
btn_row.pack(fill=tk.X)


def set_preset(multiplier):
    speed_val_var.set(multiplier)
    on_slider_change(multiplier)


tk.Button(btn_row, text="Pause (0x)", font=("Segoe UI", 8), bg="#dc2626", fg="white", command=lambda: set_preset(0.0),
          width=8).pack(side=tk.LEFT, padx=2)
tk.Button(btn_row, text="Slow (0.5x)", font=("Segoe UI", 8), bg="#d97706", fg="white", command=lambda: set_preset(0.5),
          width=8).pack(side=tk.LEFT, padx=2)
tk.Button(btn_row, text="Normal (1.0x)", font=("Segoe UI", 8), bg="#2563eb", fg="white",
          command=lambda: set_preset(1.0), width=9).pack(side=tk.LEFT, padx=2)
tk.Button(btn_row, text="Fast (2.0x)", font=("Segoe UI", 8), bg="#059669", fg="white", command=lambda: set_preset(2.0),
          width=8).pack(side=tk.LEFT, padx=2)

headers_lbl = tk.Label(dash_frame, text="ID     START  ➔  TARGET     SPD", font=("Consolas", 10, "bold"), fg="#94a3b8",
                       bg="#1e1e1e")
headers_lbl.pack(anchor="w", padx=20, pady=(15, 2))

tracking_canvas = tk.Canvas(dash_frame, bg="#1e1e1e", highlightthickness=0)
scrollbar = tk.Scrollbar(dash_frame, orient="vertical", command=tracking_canvas.yview)
scrollable_frame = tk.Frame(tracking_canvas, bg="#1e1e1e")

scrollable_frame.bind("<Configure>", lambda e: tracking_canvas.configure(scrollregion=tracking_canvas.bbox("all")))
tracking_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
tracking_canvas.configure(yscrollcommand=scrollbar.set)

tracking_canvas.pack(side="left", fill="both", expand=True, padx=(20, 0))
scrollbar.pack(side="right", fill="y")

vehicle_rows = []
for i in range(NUM_VEHICLES):
    lbl = tk.Label(scrollable_frame, text="", font=("Consolas", 9), fg="white", bg="#1e1e1e")
    lbl.pack(anchor="w", pady=1)
    vehicle_rows.append(lbl)


def to_screen(x, y):
    return int(x * 7.5 + 25), int(y * 7.5 + 25)


global_vehicle_id = 0
vehicles = []
if len(all_destinations) >= 2:
    for _ in range(NUM_VEHICLES):
        vehicles.append(Vehicle(global_vehicle_id))
        global_vehicle_id += 1

# ============================================================
# 5. ASYNC SIMULATION LOOP
# ============================================================
frame_counter = 0
is_ai_processing = False


def update_loop():
    global frame_counter, global_vehicle_id, is_ai_processing
    frame_counter += 1
    current_speed_mult = speed_val_var.get()

    if len(all_destinations) < 2:
        status_lbl.config(text="ERROR: Need at least 2 Dest (Red) Points!", fg="#ef4444")
        return

    # 1. FIRE BACKGROUND SIGNAL OPTIMIZATION
    if frame_counter % 45 == 0 and current_speed_mult > 0 and not is_ai_processing and traffic_lights:
        is_ai_processing = True
        status_lbl.config(text="Swarm Computing Signals...", fg="#f59e0b")
        thread_pool.submit(async_signal_optimization, vehicles, traffic_lights, points)

    # 2. CHECK QUEUE FOR COMPLETED SIGNAL CALCS
    try:
        best_signal_state = signal_ai_queue.get_nowait()
        is_ai_processing = False
        status_lbl.config(text="Engine: Background Threading Active", fg="#10b981")

        light_keys = list(traffic_lights.keys())
        newly_red, newly_green = [], []

        for i, key in enumerate(light_keys):
            new_state = "GREEN" if best_signal_state[i] > 0 else "RED"
            if traffic_lights[key]["state"] != new_state:
                if new_state == "RED":
                    newly_red.append(key)
                else:
                    newly_green.append(key)
                traffic_lights[key]["state"] = new_state

        if newly_red or newly_green:
            for v in vehicles:
                if not v.active or v.next_node is None or v.is_rerouting: continue
                is_blocked = any(node in newly_red for node in v.path[v.segment_idx:])
                is_shortcut = len(newly_green) > 0 and random.random() > 0.5

                if is_blocked or is_shortcut:
                    v.is_rerouting = True
                    tl_snapshot = {k: {"state": val["state"]} for k, val in traffic_lights.items()}
                    thread_pool.submit(async_vehicle_reroute, v.id, v.next_node, v.target, tl_snapshot)
    except queue.Empty:
        pass

    # 3. CHECK QUEUE FOR COMPLETED REROUTES
    while not reroute_queue.empty():
        try:
            vid, new_subpath = reroute_queue.get_nowait()
            for v in vehicles:
                if v.id == vid and v.active:
                    v.path = [v.curr_node] + new_subpath
                    v.segment_idx = 0
                    v.is_rerouting = False
                    break
        except queue.Empty:
            break

    # 4. STEP PHYSICS ENGINE
    for i, v in enumerate(vehicles):
        if not v.active:
            vehicles[i] = Vehicle(global_vehicle_id)
            global_vehicle_id += 1
        else:
            v.step(vehicles, current_speed_mult)

    # 5. RENDER GRAPHICS
    canvas.delete("all")

    # Draw Polylines instead of straight node-to-node lines
    for (u, v), polyline in road_geometry.items():
        if u < v:  # Only draw one direction to prevent overlay artifacts
            screen_coords = []
            for px, py in polyline:
                sx, sy = to_screen(px, py)
                screen_coords.extend([sx, sy])
            if len(screen_coords) >= 4:
                # Using capstyle/joinstyle ROUND makes curves look smooth and connected
                canvas.create_line(*screen_coords, fill="#3a3a3a", width=12, joinstyle=tk.ROUND, capstyle=tk.ROUND,
                                   smooth=False)

    # Draw Destinations (Boxes)
    for d_id in all_destinations:
        if d_id in points:
            sx, sy = to_screen(points[d_id][0], points[d_id][1])
            canvas.create_rectangle(sx - 10, sy - 10, sx + 10, sy + 10, fill="#2563eb", outline="white")
            canvas.create_text(sx + 16, sy - 8, text=d_id, fill="white", font=("Arial", 9, "bold"))

    # Draw Inner Nodes (Grey Dots)
    for name, pos in points.items():
        if name not in all_destinations and name not in traffic_lights:
            sx, sy = to_screen(*pos)
            canvas.create_oval(sx - 3, sy - 3, sx + 3, sy + 3, fill="#64748b", outline="")

    # Draw Traffic Lights
    for tl_node, data in traffic_lights.items():
        sx, sy = to_screen(*data["pos"])
        color = "#22c55e" if data["state"] == "GREEN" else "#ef4444"
        canvas.create_oval(sx - 9, sy - 9, sx + 9, sy + 9, fill=color, outline="black", width=2)
        canvas.create_text(sx, sy - 16, text=tl_node, fill="white", font=("Arial", 8, "bold"))

    # Draw Vehicles
    for i, v in enumerate(vehicles):
        if v.active:
            sx, sy = to_screen(v.x, v.y)
            canvas.create_oval(sx - 5, sy - 5, sx + 5, sy + 5, fill=v.color, outline="white")

            spd_text = f"{v.v:.2f}" if v.v > 0.01 else "HALT"
            indicator = " ⟳" if v.is_rerouting else ""
            vehicle_rows[i].config(
                text=f"#{v.id:03d}   {v.start:4s}➔ {v.target:4s} [{spd_text:>4s}]{indicator}",
                fg=v.color
            )

    root.after(30, update_loop)


update_loop()
root.mainloop()