"""
Streamlit front-end for `src/road_simulation.py`.

`road_simulation.py` renders its PSO-tuned adaptive traffic simulation to a
native pygame window. This app drives the exact same simulation code (graph,
vehicles, traffic-light controller, PSO retuning) headlessly -- pygame is
initialized with the "dummy" video driver so it never needs a real display --
and streams each rendered frame into the browser via `st.image`, so the
output looks the same as running `python src/road_simulation.py` directly,
just inside a web page instead of a desktop window.
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import random
import sys
import time
from pathlib import Path

import numpy as np
import pygame
import streamlit as st

SRC_DIR = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC_DIR))

import road_simulation as sim  # noqa: E402  (path must be set up first)

SCREEN_SIZE = (927, 740)
TARGET_FPS = 30

st.set_page_config(page_title="Adaptive Traffic Signal Simulation", layout="wide")
st.title("Adaptive Traffic Signal Simulation (PSO)")
st.caption(
    "Live browser view of `src/road_simulation.py`: a pygame road-network "
    "simulation with PSO-tuned, load-aware adaptive traffic signals."
)


def new_simulation_state():
    pygame.init()
    return {
        "surface": pygame.Surface(SCREEN_SIZE),
        "vehicles": [sim.Vehicle(i, is_emergency=(i < 2)) for i in range(sim.INITIAL_VEHICLES)],
        "next_vehicle_idx": sim.INITIAL_VEHICLES,
        "actuation_timer": 0.0,
        "pso_timer": 0.0,
        "spawn_timer": 0.0,
        "next_spawn_at": random.uniform(*sim.SPAWN_INTERVAL_RANGE),
        "emergency_timer": 0.0,
        "next_emergency_at": random.uniform(*sim.EMERGENCY_SPAWN_RANGE),
        "frame": 0,
    }


def step(state, dt):
    """Advance the simulation by one tick -- mirrors the per-frame sequence
    in road_simulation.main() (spawn -> sense -> actuate -> retune -> tick
    lights -> move vehicles), just without the pygame event loop / display."""
    state["actuation_timer"] += dt
    state["pso_timer"] += dt
    state["spawn_timer"] += dt
    state["emergency_timer"] += dt

    vehicles = state["vehicles"]

    if state["spawn_timer"] >= state["next_spawn_at"] and len(vehicles) < sim.MAX_VEHICLES:
        vehicles.append(sim.Vehicle(state["next_vehicle_idx"], is_emergency=False))
        state["next_vehicle_idx"] += 1
        state["spawn_timer"] = 0.0
        state["next_spawn_at"] = random.uniform(*sim.SPAWN_INTERVAL_RANGE)

    if state["emergency_timer"] >= state["next_emergency_at"] and len(vehicles) < sim.MAX_VEHICLES:
        vehicles.append(sim.Vehicle(state["next_vehicle_idx"], is_emergency=True))
        state["next_vehicle_idx"] += 1
        state["emergency_timer"] = 0.0
        state["next_emergency_at"] = random.uniform(*sim.EMERGENCY_SPAWN_RANGE)

    sim.update_hub_loads(vehicles)

    if state["actuation_timer"] >= sim.ACTUATION_INTERVAL:
        sim.run_signal_actuation(vehicles)
        state["actuation_timer"] = 0.0

    if state["pso_timer"] >= sim.PSO_INTERVAL:
        sim.run_pso_retune()
        state["pso_timer"] = 0.0

    for tl in sim.lights.values():
        tl.update(dt)

    gaps = sim.compute_following_gaps(vehicles)
    for v in vehicles:
        v.update(dt, gaps.get(v))

    state["vehicles"] = [v for v in vehicles if v.active]
    state["frame"] += 1


def render(state):
    """Same drawing steps as road_simulation.main()'s render section, but
    onto an off-screen Surface, returned as an (H, W, 3) RGB array for
    st.image instead of being flipped to a real display."""
    screen = state["surface"]
    screen.fill((245, 245, 247))

    for e in sim.EDGES:
        pygame.draw.lines(screen, (70, 70, 70), False, e["pts"], sim.ROAD_WIDTH)
        sim.draw_dashed_centerline(screen, e["pts"])

    for nid in sim.RED_IDS:
        n = sim.NODES[nid]
        pygame.draw.circle(screen, (220, 38, 38), (int(n["x"]), int(n["y"])), 6)

    for hub_id, dots in sim.HUB_LIGHTS.items():
        tl = sim.lights[hub_id]
        for idx in range(len(dots)):
            anchor = sim._signal_render_anchor(hub_id, idx)
            sim.draw_signal_head(screen, anchor, tl.dot_state(idx))

    for v in state["vehicles"]:
        x, y = v.pos
        radius = 7 if v.is_emergency else 5
        pygame.draw.circle(screen, v.color, (int(x), int(y)), radius)
        pygame.draw.circle(screen, (0, 0, 0), (int(x), int(y)), radius, 1)
        if v.waiting:
            pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), 2)

    pygame.draw.rect(screen, (60, 60, 60), screen.get_rect(), width=3)

    frame = pygame.surfarray.array3d(screen)
    return np.transpose(frame, (1, 0, 2))


if "sim" not in st.session_state:
    st.session_state.sim = None
if "running" not in st.session_state:
    st.session_state.running = False

col1, col2, col3 = st.columns(3)
start_clicked = col1.button("Start", use_container_width=True)
stop_clicked = col2.button("Stop", use_container_width=True)
reset_clicked = col3.button("Reset", use_container_width=True)

if reset_clicked:
    st.session_state.sim = None
    st.session_state.running = False

if start_clicked:
    if st.session_state.sim is None:
        st.session_state.sim = new_simulation_state()
    st.session_state.running = True

if stop_clicked:
    st.session_state.running = False

status_placeholder = st.empty()
frame_placeholder = st.empty()
metrics_placeholder = st.empty()

if st.session_state.sim is None:
    status_placeholder.info("Click **Start** to launch the simulation.")
else:
    status_placeholder.success("Running" if st.session_state.running else "Paused")
    frame_placeholder.image(render(st.session_state.sim), channels="RGB", use_container_width=True)

# Streamlit interrupts a running script (including mid-loop) as soon as the
# user triggers another interaction, e.g. clicking Stop -- so this loop is
# what keeps streaming frames while running, and clicking Stop cleanly breaks
# out of it on the next rerun instead of needing a manual flag check.
if st.session_state.running:
    state = st.session_state.sim
    dt = 1.0 / TARGET_FPS
    while st.session_state.running:
        step(state, dt)
        frame_placeholder.image(render(state), channels="RGB", use_container_width=True)
        metrics_placeholder.caption(
            f"Frame {state['frame']} | Active vehicles: {len(state['vehicles'])}"
        )
        time.sleep(dt)
