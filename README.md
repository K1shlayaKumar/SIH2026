# Adaptive Traffic Signal Simulation

A `pygame` simulation of a small road network with **PSO (Particle Swarm
Optimization)-tuned, load-aware adaptive traffic signals**, plus a
`streamlit` web front-end so the simulation can be watched in a browser
without a native display.

For the full technical deep-dive (architecture diagrams, algorithm details,
function reference, tuning parameters), see
[TrafficSignelSimulationReadme.md](TrafficSignelSimulationReadme.md).

## What it simulates

- A fixed road graph with 3 real 4-way signalized intersections ("hubs"),
  each with 2 conflicting phases (e.g. North-South vs East-West).
- A fleet of vehicles that spawn from random origins, drive to random
  destinations, and disappear on arrival — including occasional emergency
  vehicles that get signal preemption.
- Traffic lights that switch phase based on **live queue load + wait time**
  at each hub, not a fixed timer — a starvation guard guarantees a
  heavily-waiting phase eventually gets green.
- Two Particle Swarm Optimization passes that continuously retune (a) each
  hub's green-time safety cap and (b) the load/wait weighting used to decide
  when to switch phases, both driven from live network data.

The project also includes:

| File | Purpose |
|---|---|
| `src/road_simulation.py` | The main adaptive simulation (pygame window). |
| `src/road_simulation_fixedtime.py` | A fixed-time-signal counterpart used to visually compare against the adaptive controller. |
| `src/road_simulation_compare.py` | Runs both of the above side by side in **one window**, so the difference in queuing/wait behavior is visible in a single frame. |
| `src/qpso_algo_2.py` | A standalone bi-level PSO routing/signal-optimization reference implementation. |
| `streamlit_app.py` | Browser front-end that streams the same simulation as live frames. |
| `setup.py` | One-command installer + launcher for the Streamlit app. |

## Requirements

- Python 3.9+
- See [requirements.txt](requirements.txt) (`pygame`, `numpy`, `streamlit`)

## Setup

### Option A — one command (installs deps and opens the browser app)

```bash
python setup.py
```

This installs everything in `requirements.txt` and then runs
`streamlit run streamlit_app.py`, which opens the simulation in your default
browser.

### Option B — manual setup

1. (Recommended) Create and activate a virtual environment:

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app in one of two ways:

   - **Browser (Streamlit)**:

     ```bash
     streamlit run streamlit_app.py
     ```

     Click **Start** to begin the simulation, **Stop** to pause it, and
     **Reset** to start over with a fresh fleet.

   - **Native pygame window**:

     ```bash
     python src/road_simulation.py
     ```

     For the fixed-time comparison version:

     ```bash
     python src/road_simulation_fixedtime.py --fixed-time 15
     ```

     For **both signal policies side by side in one window** (adaptive on
     the left, fixed-time on the right — useful for demonstrating the
     difference to reviewers):

     ```bash
     python src/road_simulation_compare.py
     python src/road_simulation_compare.py --fixed-time 20   # change the fixed-time panel's cycle
     python src/road_simulation_compare.py --scale 0.75      # shrink to fit a smaller screen
     ```

## Reading the simulation

Colored dots at the 3 intersections are traffic signal heads; small circles
are vehicles (a red-outlined, larger circle is an emergency vehicle). A
white dot inside a vehicle means it's currently waiting at a signal or
behind another vehicle.

## Deploying to Streamlit Community Cloud

The repo is already set up for [Streamlit Community
Cloud](https://share.streamlit.io):

- `.python-version` pins Python 3.11 (needed because `pygame` doesn't ship
  prebuilt wheels for the newest Python versions yet — on 3.11/3.12, `pip`
  gets a prebuilt wheel that already bundles its own SDL2/freetype, so no
  `packages.txt` / system libraries are needed).
- `streamlit_app.py` runs pygame headless (`SDL_VIDEODRIVER`/`SDL_AUDIODRIVER`
  forced to `dummy`), so it doesn't need a real display or audio device,
  which suits a cloud container.

To deploy:

1. Push this repo to GitHub (already done for this project).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with
   GitHub.
3. Click **New app**, pick this repository and the `main` branch, and set
   **Main file path** to `streamlit_app.py`.
4. **Before clicking Deploy**, open **"Advanced settings..."** and set
   **Python version** to **3.11** (or 3.12) explicitly. Streamlit Cloud does
   not reliably pick up `.python-version` on its own, and without this step
   it may default to a Python version `pygame` has no prebuilt wheel for,
   causing a build-from-source failure (`Unable to run "sdl-config"`).
5. Click **Deploy**. You'll get a public `*.streamlit.app` URL to share.

If an app was already created without setting this, the Python version
generally can't be changed from its Settings afterward — delete the app and
redeploy following step 4.

Note: the app's Start/Stop loop keeps the container busy while running, so
click **Stop** when you're not actively demoing it to avoid burning through
the free tier's compute hours.
