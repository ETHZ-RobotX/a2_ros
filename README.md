# A2 ROS2 Workspace

<p align="center">
  <img src="docs/a2.png" alt="Unitree A2 quadruped" width="100%">
</p>

ROS2 (Jazzy) simulation of the Unitree A2 quadruped using MuJoCo and a trained RL locomotion policy.

## 🐳 Setup with Docker

### Prerequisites
1. Install [Docker](https://docs.docker.com/engine/install/). Note Linux systems need Docker Engine **not Docker Desktop**, MacOS needs Docker Desktop, Windows TBD.
1. Setup X11 forwarding privileges from docker to host:
    ```bash
    xhost +local:docker
    ```
1. Clone the repository and submodules:
    ```bash
    git clone git@github.com:ETHZ-RobotX/a2_ros.git --recursive
    ```

### First-time setup
Run the dev environment setup script once from the repo root. This writes your host UID and GID into `.env` so the Docker image is built with matching file ownership:
```bash
./scripts/setup_devenv.sh
```

The `.env` file is gitignored and personal to your machine. It is also sourced by all setup scripts inside the container, so any runtime overrides can be added there and they will be picked up automatically. Common ones:

| Variable | Purpose | Default |
|---|---|---|
| `RMW_IMPLEMENTATION` | Selects the middleware (`rmw_zenoh_cpp` or `rmw_cyclonedds_cpp`) | `rmw_zenoh_cpp` |
| `ROS_DOMAIN_ID` | ROS 2 domain for the Zenoh (sim) path | `30` |
| `ZENOH_ROUTER_IP_SIM` | Router address sim nodes connect to | `127.0.0.1` |
| `ZENOH_ROUTER_IP_ROBOT` | Router address robot nodes connect to | `127.0.0.1` |
| `ZENOH_ROUTER_IP` | Shared fallback used if the per-profile vars are unset | `127.0.0.1` |
| `ROS_BAGS_DIR` | Host directory bind-mounted to `/a2_ros_ws/bags` | `./bags` |

### Build and spawn
```bash
docker compose build a2_ros_dev
docker compose up -d a2_ros_dev
```

> `a2_ros_dev` builds on top of the prebuilt **`a2_base`** image, which CI publishes multi-arch (x86_64 **and** arm64 — Apple Silicon works) to GHCR. The base is therefore **pulled, not built locally**. After CI publishes a new base, refresh it with `docker compose build --pull a2_ros_dev` (a plain `build` keeps the cached base). To build the base yourself instead, set `A2_BASE_IMAGE=a2_ros:base` and run `docker compose build a2_base` first.

Enter the container:
```bash
docker compose exec a2_ros_dev bash
```

### Inside the container
The ROS environment and workspace (if built) are sourced automatically on shell startup via `scripts/setup.sh`. To manually re-source or refresh the workspace:
```bash
source scripts/setup.sh
```

### Zenoh middleware

ROS 2 nodes use Zenoh (`rmw_zenoh_cpp`) by default. Two pieces are involved:

- **Session config** — rendered automatically on every shell by `scripts/setup.sh` → `setup_zenoh.sh`. It selects the `sim`/`robot` profile (from `A2_MODE`), sets `ROS_DOMAIN_ID`, points nodes at the router IP, and prints a summary like:
  ```
  [a2_ros] Zenoh: localhost
  [a2_ros] Zenoh session config: /home/ubuntu/.tmp/zenoh-ros2-config.sim.json5
  [a2_ros] ROS_DOMAIN_ID=30
  ```
- **Router** (`rmw_zenohd`) — a per-machine discovery singleton all nodes need. It now **starts automatically** as a compose service: `a2_ros_dev` depends on `zenoh_router_sim`, and `a2_ros_robot` on `zenoh_router_robot`, so `docker compose up -d a2_ros_dev` brings the router up first (with `restart: unless-stopped`). Check it with:
  ```bash
  docker compose logs -f zenoh_router_sim   # "Started Zenoh router with id ..."
  ```

**Manual fallback** — to run a router inside the container in a foreground terminal instead (e.g. for debugging):
```bash
scripts/start_zenoh_router.sh
```

> Run only **one** router per host — `zenoh_router_sim` and `zenoh_router_robot` both bind TCP `7447`. For a multi-machine setup, run the router on one host and set `ZENOH_ROUTER_IP_SIM` / `ZENOH_ROUTER_IP_ROBOT` in `.env` on the others.

### Stopping
```bash
docker compose stop a2_ros_dev       # pause, keeps volumes
docker compose down                  # stop and remove containers
docker compose down -v               # also remove volumes (wipes build cache)
```

## 📦 Meta Packages

The `src/meta_packages/` directory contains stack-level packages. Each one declares `exec_depend` entries for a particular deployment scenario — build it with `colcon build --packages-up-to <name>` to pull in all required dependencies. All launch files and config live in `a2_ros` and are launched from there, except `a2_pc2` which runs on a separate compute unit and owns its own launch files.

| Package | Pull in for | Key deps |
|---|---|---|
| `a2_sim` | Simulation | `a2_sim_utils`, `a2_locomotion_controller`, `unitree_mujoco` |
| `a2_sim_full` | Full simulation with perception | `a2_sim` + `a2_state_estimation` + `a2_object_detection` |
| `a2_state_estimation` | LiDAR-inertial odometry | `direct_lidar_inertial_odometry` |
| `a2_object_detection` | Object detection | `object_detection`, `object_detection_msgs` |
| `a2_robot` | Real robot | `a2_ros` + `a2_state_estimation` + `a2_object_detection` + `hesai_ros_driver` |
| `a2_pc2` | Second compute unit | `a2_unitree_bridge`, `gscam2`, Unitree SDK — has its own launch files |

Hardware-conditional dependencies are handled at the stack level: `hesai_ros_driver` is an `exec_depend` of `a2_robot` only, so the LiDAR driver is not required when building for simulation.

**Typical workflow:** build the meta package for your target, then use `a2` commands:
```bash
colcon build --packages-up-to a2_robot   # real robot
# or
colcon build --packages-up-to a2_sim_full  # simulation with perception
```

## 🚀 Launching Subsystems

All launch files live in `a2_ros`. Use the `a2` CLI to invoke them:

| Command | Launch file | Description |
|---|---|---|
| `a2 sim [--rviz] [--dlio] [--headless] [--scene <file>]` | `sim.launch.py` | MuJoCo simulation + locomotion controller |
| `a2 nav [--rviz]` | `navigation.launch.py` | CMU navigation stack (terrain analysis + path planner) |
| `a2 explore [--rviz]` | `exploration.launch.py` | Autonomous exploration (TARE planner) |
| `a2 dlio [--rviz]` | `dlio.launch.py` | DLIO LiDAR-inertial odometry |
| `a2 detect` | `object_detection.launch.py` | Object detection (ONNX Runtime); uses `object_detection_real.launch.py` on the robot |

**`a2 sim` options:**
- `--rviz` — also open RViz.
- `--dlio` — use DLIO for odometry instead of ground-truth TF (run `a2 dlio` in another terminal).
- `--headless` — run MuJoCo with no viewer window; visualize in RViz/Foxglove. LiDAR and the RGB camera still render (camera via offscreen EGL). Needs no X server/VNC — useful on macOS/Windows or over SSH.
- `--scene <file>` — pick the MuJoCo scene: `scene.xml` (default), `scene_flat.xml`, `scene_terrain.xml`, `scene_obstacles.xml`, `scene_maze.xml`, `scene_test_meshes.xml`.

> Running on the second compute unit (**pc2**)? Its setup and launch live in [`docs/pc2.md`](docs/pc2.md).

### Typical simulation workflow

**Terminal 1 — simulation:**
```bash
a2 sim
```

**Terminal 2 — bring the robot up, then walk** (run in order):
```bash
a2 stand     # stand up
a2 unlock    # release to balance stand
a2 walk      # start walking
```
Then `a2 stop` to stop moving (keeps balance), and `a2 sit` to sit / stand down.

To drive manually with the keyboard, run `a2 keyboard` in its own terminal once the robot is in walk mode — it publishes `/cmd_vel` from your key presses.

**Terminal 3 — navigation / exploration / odometry:**

```bash
# Set a 2D Nav Goal in RViz to send the robot to a target pose.
a2 nav --rviz
# Autonomous Exploration
a2 explore --rviz
# LIO State Estimation
a2 dlio --rviz
```

**Terminal 4 — object detection:**
```bash
a2 detect
```

## 📊 Visualization (Foxglove)

A prebuilt [Foxglove Studio](https://foxglove.dev/) layout for the full stack ships at
[`docs/rss26_layout.json`](docs/rss26_layout.json).

Download and install Foxglove Studio from [foxglove.dev/download](https://foxglove.dev/download).

**1. Start the Foxglove bridge** — exposes ROS topics over a WebSocket at `ws://localhost:8765`
(in sim it is launched with `use_sim_time` so timestamps track `/clock`):
```bash
a2 foxglove
```

**2. Connect and load the layout** in Foxglove Studio (desktop or web app):
- Add a connection → **Foxglove WebSocket** → `ws://localhost:8765`.
- **Layouts** → **Import from file…** → select `docs/rss26_layout.json`.

The layout contains:

| Panel | Shows |
|---|---|
| **3D** | Robot model + TF, front/rear lidar (`/front_lidar/points`, `/rear_lidar/points`), `/registered_scan`, terrain maps, navigation paths/goals, and TARE exploration markers |
| **Image** | `/camera/image_raw` with object-detection overlays (`/detection_annotations`, `/detections_in_image`) |
| **Transform Tree** | Live TF tree |
| **Joystick** | Live gamepad input |

Notes:
- The `/detection_annotations` overlay only appears when the object-detection node is running (`a2 detect`).
- Send navigation goals straight from the 3D panel using the `/goal_point` (far_planner) publish control.

## 💾 Recording & Playback

Record ROS 2 topics to MCAP and replay them with the `a2` CLI. Bags are written to the bag directory — `$ROS_BAGS_DIR`, default `/a2_ros_ws/bags` in the container (bind-mounted to `./bags` on the host) — named `bag_<timestamp>[_suffix]`.

**Record** — choose what to capture (`--all`, `--topics`, or a `--config` YAML); stop with Ctrl+C:
```bash
a2 bag record --all run1                                    # everything, suffix "run1"
a2 bag record --all --ignore '/camera/image_raw'           # all except some topics
a2 bag record --topics '/cmd_vel /odom /registered_scan' nav_test
```
A `--config` YAML can set `all:`, `topics:`, and `ignore:` (see `a2 bag record --help`).

**Play back** — pass just the bag name (resolved against the bag dir) or a full path:
```bash
a2 bag play bag_<timestamp>_run1                  # from the bag dir
a2 bag play bag_<timestamp>_run1 --clock --pause  # publish /clock, start paused
```

## 🎮 Gamepad

> These controls are for driving the **real robot**.

<p align="center">
  <img src="docs/controller.png" alt="Gamepad controls: left stick = longitudinal/lateral, right stick = yaw, L2+△ steps the FSM to a higher state, L2+X to a lower state, ○ soft stop, PS button on/off" width="85%">
</p>


## 🛠️ Development
Development happens with the `a2_ros_dev` docker compose service. This contains all dependencies to run the stack in simulation along with object detection.

To speed up development, many artifacts are cached using docker volumes. This includes the colcon build artifacts.

### Git Submodules
This repo pulls in its packages as git submodules (see `.gitmodules`). Handy commands:

```bash
# Clone everything from scratch (submodules included)
git clone git@github.com:ETHZ-RobotX/a2_ros.git --recursive

# Check out the pinned submodule commits. Run this after a non-recursive clone,
# and after every `git pull` of main, to sync submodules to the commits this
# repo pins.
git submodule update --init --recursive
# ...or have git do it automatically on every pull/checkout:
git config submodule.recurse true

# See which submodules changed (or are on the wrong commit)
git submodule status
git status

# Pull the latest upstream for every submodule (moves them off the pinned commit)
git submodule update --remote --merge

# If a submodule URL changed in .gitmodules, re-sync the local config
git submodule sync --recursive
```

Submodules check out a detached HEAD at the pinned commit. To work in one, `cd` into it
(paths vary — many live under `src/`, not `external/`; see `.gitmodules`), check out its
branch, commit and push there first, then commit the new submodule pointer in this repo:
```bash
cd <submodule-path>            # e.g. src/object_detection or external/unitree_mujoco
git checkout <branch> && git pull   # the submodule's own branch (often main)
# ... make changes, commit, push ...
cd -
git add <submodule-path>       # records the new pinned commit
git commit -m "bump <submodule>"
```

**Feature branches & avoiding submodule conflicts.** A submodule pointer is a single
gitlink in the superproject tree, so if two branches bump the same submodule to different
commits, merging produces a conflict on that path. To keep this painless:

```bash
# Always commit on a branch inside the submodule, never on the detached HEAD.
cd <submodule-path>
git switch -c my-feature        # or: git checkout <existing-branch>
# ... work, commit ...
git push -u origin my-feature   # push the submodule branch FIRST — others (and CI)
cd -                            # can't fetch a pointer to an unpushed commit
git add <submodule-path> && git commit -m "bump <submodule> to my-feature"

# Make the two repos move together so branch switches don't leave stale checkouts,
# and so pushing the superproject also pushes any new submodule commits:
git config submodule.recurse true
git config push.recurseSubmodules on-demand
```

Resolving a pointer conflict (the conflict is over *which commit* to pin, so pick one —
don't hand-edit the gitlink):
```bash
git checkout <branch-or-ref> -- <submodule-path>   # take that side's pinned commit
# ...or pin an explicit commit:
cd <submodule-path> && git checkout <sha> && cd -
git add <submodule-path>                           # marks it resolved
```

**Forking.** `.gitmodules` pins upstream `ETHZ-RobotX` URLs. If you fork a submodule to push
your own work, point your local clone at the fork **without committing the URL change** (so
you don't conflict with upstream `.gitmodules` or break others):
```bash
git submodule set-url <submodule-path> git@github.com:<you>/<repo>.git
git submodule sync <submodule-path>            # apply the URL to your local .git/config
git update-index --skip-worktree .gitmodules   # keep the URL edit local-only
```

### Cleaning the ROS Workspace
Colcon build artifacts live in named volumes mounted under `/a2_ros_ws` (`build`, `install`, `log`), so the directories can't be removed — only their contents. Use the `a2` CLI inside the container:
```bash
a2 clean          # add --yes to skip the confirmation prompt
```
