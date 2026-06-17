# a2_ros

ROS2 (Jazzy) simulation of the Unitree A2 quadruped using MuJoCo and a trained RL locomotion policy.

## TODOs

> **CRITICAL**
> - [ ] `pathFollower` / `localPlanner` autonomy mode is overridden to `false` by the joystick node on every `/joy` message (axes[4] < 0.1 at rest). The `autonomyMode: True` launch parameter has no effect while a controller is connected. Either kill `joy_node` before running nav (`ros2 node kill /joy_node`), push the right stick forward to hold axes[4] > 0.1, or patch pathFollower/localPlanner to only respect the joystick override when `joySpeedRaw > 0`.
> - [ ] Move `registered_scan` publisher out of `a2_sim_utils` into a standalone `a2_utils` node so it can be used with real hardware and DLIO without a sim dependency (see DLIO integration notes below).

- [x] Provide base docker setup for development
- [x] Move dependency installations from install scripts to docker **Until this time, try not to recreate containers to save time**
- [x] Decide whether install script should manage git submodules too (and thus lie inside the docker runtime)
- [x] Remove interactive components of install script
- [x] Ship `a2_ros` source code with built image
- [x] Setup docker managed volumes for build artifacts (also requires deciding how to organize these)
- [ ] Setup docker managed volumes for data artifacts (rosbags, pytorch models etc.)(also requires deciding how to organize these)
- [ ] Remove all source code from meta-package `a2_ros` and only maintain dependencies
- [x] Add source folders for each subsystem `core/ sim/` etc.
- [x] Install other third party drivers related to lidars and other peripherals.

## Setup with Docker

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
| `ROS_BAGS_DIR` | Host directory bind-mounted to `/a2_ros/bags` | `./bags` |

### Build and spawn
```bash
docker compose build a2_ros_dev
docker compose up -d a2_ros_dev
```

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

**Note:** Build artifacts are stored in Docker named volumes, so cleaning the workspace requires deleting the contents rather than the directories:
```bash
rm -rf build/* install/* log
```

### Stopping
```bash
docker compose stop a2_ros_dev       # pause, keeps volumes
docker compose down                  # stop and remove containers
docker compose down -v               # also remove volumes (wipes build cache)
```

## Launching Subsystems
Launch the simulation:
## Local development with a2.sh

`a2.sh` is the main entry point for local (non-Docker) development. It deactivates any active conda environment before sourcing ROS so builds and launches are not affected by conda Python.

### One-time shell setup

Register the `a2` convenience function in your shell (run once):

```bash
source ./a2.sh --bashrc
```

This appends an `a2()` function to `~/.bashrc` so you can call `a2 <command>` from any directory. The `--source` sub-command is handled inline (via `source`) so it takes effect in the current shell; all other commands are forwarded to `a2.sh`.

### Commands

| Command | Description |
|---|---|
| `a2 --start` | Launch the MuJoCo simulation (`scene_maze.xml`) |
| `a2 --walk` | Command the robot to walk (publishes `mode=3` on `/mode`) |
| `a2 --nav` | Launch the navigation stack |
| `a2 --exploration` | Launch autonomous exploration (TARE) |
| `a2 --dlio` | Launch DLIO LiDAR-inertial odometry |
| `a2 --source` | Source the workspace setup in the current shell |
| `a2 --bashrc` | Add the `a2` function to `~/.bashrc` (idempotent) |
| `a2 --init` | Open a 4-pane terminator window with commands pre-filled |

Append `--rviz` to any launch command to open RViz alongside it, e.g.:

```bash
a2 --start --rviz
a2 --nav --rviz
```

### Quick start with `--init`

The fastest way to get going. Requires `terminator` (`sudo apt install terminator`) and `--bashrc` to have been run first:

```bash
a2 --init
```

This opens a single terminator window split into 4 panes, each with a command pre-filled and ready to run (press Enter or edit as needed):

| Pane | Command | Background |
|---|---|---|
| Top-left | `a2 --start` | dark green |
| Bottom-left | `a2 --walk` | dark blue |
| Top-right | `a2 --nav` | dark red |
| Bottom-right | `a2 --source` | dark amber |

### Typical workflow

**Terminal 1 — simulation:**
```bash
a2 --start
```

**Terminal 2 — walk:**
```bash
a2 --walk
```

**Terminal 3 — navigation / exploration / odometry:**
```bash
a2 --nav --rviz
# or
a2 --exploration --rviz
# or
a2 --dlio --rviz
```

Set a 2D Nav Goal in RViz to send the robot to a target pose.

## Gamepad

| Input | Action |
|---|---|
| Left stick | Forward / strafe |
| Right stick horizontal | Yaw |
| X + L2 | Sit |
| Triangle + L2 | Stand |
| L2 + R2 | Walk |


### Development
Development happens with the `a2_ros_dev` docker compose service. This contains all dependencies to run the stack in simulation along with object detection.

To speed up development, many artifacts are cached using docker volumes. This includes the colcon build artifacts.

#### Cleaning the ROS Workspace
Since the build artifacts are also a volume, the folders cannot be deleted. However, their contents can be deleted.
```bash
$ rm -rf build/* install/* log
```
