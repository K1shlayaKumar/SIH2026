"""
Side-by-side comparison: adaptive, load/wait-based signals (road_simulation.py)
vs plain fixed-time signals (road_simulation_fixedtime.py) -- in ONE window,
so the difference in queuing/wait behavior is visible in a single frame
instead of two separate windows a reviewer has to eyeball side by side.

Left panel  -> road_simulation.py:            RealLifeTrafficLight (PSO-tuned, load+wait driven)
Right panel -> road_simulation_fixedtime.py:   FixedTimeTrafficLight (unconditional round-robin timer)

Both panels reuse their source script's actual graph data, Vehicle class,
routing, car-following, and rendering functions unmodified -- this script
only adds the side-by-side stepping/layout. Both use the same spawn/despawn
settings (already identical between the two source scripts), so the only
variable being compared is signal-timing POLICY, not traffic volume.

Usage:
    python road_simulation_compare.py
    python road_simulation_compare.py --fixed-time 20
    python road_simulation_compare.py --scale 0.75   # shrink to fit smaller screens
"""
import argparse
import random

import pygame

import road_simulation as adaptive
import road_simulation_fixedtime as fixedtime

PANEL_SIZE = (927, 740)
HEADER_HEIGHT = 56
GUTTER = 6

BG_COLOR = (245, 245, 247)
HEADER_BG = (24, 24, 28)
TITLE_COLOR_LEFT = (110, 231, 183)
TITLE_COLOR_RIGHT = (252, 165, 165)
STATS_COLOR = (215, 215, 220)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Side-by-side comparison of adaptive (load-based) vs fixed-time traffic signals.")
    parser.add_argument(
        "--fixed-time", "-t", type=float, default=fixedtime.DEFAULT_FIXED_GREEN_TIME,
        help=f"Green duration (seconds) per phase for the fixed-time panel "
             f"(default: {fixedtime.DEFAULT_FIXED_GREEN_TIME:.0f}).")
    parser.add_argument(
        "--scale", type=float, default=1.0,
        help="Display scale for both panels, e.g. 0.75 to fit smaller screens (default: 1.0).")
    args = parser.parse_args()
    if args.fixed_time <= 0:
        parser.error("--fixed-time must be a positive number of seconds")
    if args.scale <= 0:
        parser.error("--scale must be a positive number")
    return args


class SimSide:
    """One panel's simulation state: an independent vehicle fleet, spawn
    timers, and off-screen rendering surface, tied to one of the two
    simulation modules (adaptive or fixedtime)."""

    def __init__(self, mod):
        self.mod = mod
        self.surface = pygame.Surface(PANEL_SIZE)
        self.vehicles = [mod.Vehicle(i, is_emergency=(i < 2)) for i in range(mod.INITIAL_VEHICLES)]
        self.next_vehicle_idx = mod.INITIAL_VEHICLES
        self.spawn_timer = 0.0
        self.next_spawn_at = random.uniform(*mod.SPAWN_INTERVAL_RANGE)
        self.emergency_timer = 0.0
        self.next_emergency_at = random.uniform(*mod.EMERGENCY_SPAWN_RANGE)
        self.actuation_timer = 0.0
        self.pso_timer = 0.0

    def spawn(self, dt):
        mod = self.mod
        self.spawn_timer += dt
        self.emergency_timer += dt
        if self.spawn_timer >= self.next_spawn_at and len(self.vehicles) < mod.MAX_VEHICLES:
            self.vehicles.append(mod.Vehicle(self.next_vehicle_idx, is_emergency=False))
            self.next_vehicle_idx += 1
            self.spawn_timer = 0.0
            self.next_spawn_at = random.uniform(*mod.SPAWN_INTERVAL_RANGE)
        if self.emergency_timer >= self.next_emergency_at and len(self.vehicles) < mod.MAX_VEHICLES:
            self.vehicles.append(mod.Vehicle(self.next_vehicle_idx, is_emergency=True))
            self.next_vehicle_idx += 1
            self.emergency_timer = 0.0
            self.next_emergency_at = random.uniform(*mod.EMERGENCY_SPAWN_RANGE)

    def waiting_count(self):
        return sum(1 for v in self.vehicles if v.waiting)


def step_adaptive(side, dt):
    mod = side.mod
    side.spawn(dt)
    mod.update_hub_loads(side.vehicles)

    side.actuation_timer += dt
    if side.actuation_timer >= mod.ACTUATION_INTERVAL:
        mod.run_signal_actuation(side.vehicles)
        side.actuation_timer = 0.0

    side.pso_timer += dt
    if side.pso_timer >= mod.PSO_INTERVAL:
        mod.run_pso_retune()
        side.pso_timer = 0.0

    for tl in mod.lights.values():
        tl.update(dt)

    gaps = mod.compute_following_gaps(side.vehicles)
    for v in side.vehicles:
        v.update(dt, gaps.get(v))
    side.vehicles = [v for v in side.vehicles if v.active]


def step_fixed(side, dt):
    mod = side.mod
    side.spawn(dt)
    mod.update_hub_loads(side.vehicles)  # HUD only -- does not affect switching

    for tl in mod.lights.values():
        tl.update(dt)

    gaps = mod.compute_following_gaps(side.vehicles)
    for v in side.vehicles:
        v.update(dt, gaps.get(v))
    side.vehicles = [v for v in side.vehicles if v.active]


def hub_label_adaptive(tl):
    return (f"{tl.active}:{tl.state} A{tl.load['A']:.1f} B{tl.load['B']:.1f} "
            f"wA{tl.wait_time['A']:.0f}s wB{tl.wait_time['B']:.0f}s g{tl.max_green:.0f}s")


def hub_label_fixed(tl):
    return (f"{tl.active}:{tl.state} {tl.timer:.1f}s/{tl.fixed_green_time:.0f}s "
            f"A{tl.load['A']:.1f} B{tl.load['B']:.1f}")


def render_panel(side, label_fn, small_font):
    """Same drawing steps as each source script's own main() render section,
    onto this panel's own off-screen surface, plus a per-hub diagnostic label
    so the reviewer can see WHY each panel's lights are doing what they do."""
    mod = side.mod
    screen = side.surface
    screen.fill(BG_COLOR)

    for e in mod.EDGES:
        pygame.draw.lines(screen, (70, 70, 70), False, e["pts"], mod.ROAD_WIDTH)
        mod.draw_dashed_centerline(screen, e["pts"])

    for nid in mod.RED_IDS:
        n = mod.NODES[nid]
        pygame.draw.circle(screen, (220, 38, 38), (int(n["x"]), int(n["y"])), 6)

    for hub_id, dots in mod.HUB_LIGHTS.items():
        tl = mod.lights[hub_id]
        for idx in range(len(dots)):
            anchor = mod._signal_render_anchor(hub_id, idx)
            mod.draw_signal_head(screen, anchor, tl.dot_state(idx))
        label_x, label_y = dots[0][0] + 14, dots[0][1] - 46
        text = small_font.render(label_fn(tl), True, (20, 20, 20))
        screen.blit(text, (label_x, label_y))

    for v in side.vehicles:
        x, y = v.pos
        radius = 7 if v.is_emergency else 5
        pygame.draw.circle(screen, v.color, (int(x), int(y)), radius)
        pygame.draw.circle(screen, (0, 0, 0), (int(x), int(y)), radius, 1)
        if v.waiting:
            pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), 2)

    pygame.draw.rect(screen, (60, 60, 60), screen.get_rect(), width=3)


def main():
    args = parse_args()
    # road_simulation_fixedtime.py normally builds `lights` inside its own
    # main() once --fixed-time is parsed; we replicate that here since we
    # never call that main().
    fixedtime.lights = {hid: fixedtime.FixedTimeTrafficLight(hid, args.fixed_time)
                         for hid in fixedtime.HUB_IDS}

    panel_w, panel_h = int(PANEL_SIZE[0] * args.scale), int(PANEL_SIZE[1] * args.scale)
    window_size = (panel_w * 2 + GUTTER, HEADER_HEIGHT + panel_h)

    pygame.init()
    screen = pygame.display.set_mode(window_size)
    pygame.display.set_caption("Adaptive (Load-Based) vs Fixed-Time Traffic Signals")
    clock = pygame.time.Clock()
    title_font = pygame.font.SysFont("Arial", 18, bold=True)
    stats_font = pygame.font.SysFont("Arial", 14)
    hub_font = pygame.font.SysFont("Arial", 12)

    left = SimSide(adaptive)
    right = SimSide(fixedtime)
    right_x = panel_w + GUTTER

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        step_adaptive(left, dt)
        step_fixed(right, dt)

        render_panel(left, hub_label_adaptive, hub_font)
        render_panel(right, hub_label_fixed, hub_font)

        screen.fill(HEADER_BG)
        left_view = left.surface if args.scale == 1.0 else pygame.transform.smoothscale(left.surface, (panel_w, panel_h))
        right_view = right.surface if args.scale == 1.0 else pygame.transform.smoothscale(right.surface, (panel_w, panel_h))
        screen.blit(left_view, (0, HEADER_HEIGHT))
        screen.blit(right_view, (right_x, HEADER_HEIGHT))

        screen.blit(title_font.render("ADAPTIVE -- load + wait based (PSO-tuned)", True, TITLE_COLOR_LEFT), (16, 8))
        screen.blit(title_font.render(f"FIXED-TIME -- {args.fixed_time:.0f}s/phase regardless of load", True, TITLE_COLOR_RIGHT), (right_x + 16, 8))

        screen.blit(stats_font.render(
            f"Vehicles: {len(left.vehicles)}   Waiting now: {left.waiting_count()}", True, STATS_COLOR), (16, 32))
        screen.blit(stats_font.render(
            f"Vehicles: {len(right.vehicles)}   Waiting now: {right.waiting_count()}", True, STATS_COLOR), (right_x + 16, 32))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
