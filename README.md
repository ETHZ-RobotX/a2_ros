# a2_ros

ROS2 (Jazzy) simulation of the Unitree A2 quadruped using MuJoCo and a trained RL locomotion policy.

## TODOs

> **CRITICAL**
> - [ ] `pathFollower` / `localPlanner` autonomy mode is overridden to `false` by the joystick node on every `/joy` message (axes[4] < 0.1 at rest). The `autonomyMode: True` launch parameter has no effect while a controller is connected. Either kill `joy_node` before running nav (`ros2 node kill /joy_node`), push the right stick forward to hold axes[4] > 0.1, or patch pathFollower/localPlanner to only respect the joystick override when `joySpeedRaw > 0`.
> - [ ] Move `registered_scan` publisher out of `a2_sim_utils` into a standalone `a2_utils` node so it can be used with real hardware and DLIO without a sim dependency (see DLIO integration notes below).

- [ ] Remove all source code from meta-package `a2_ros` and only maintain dependencies

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

## Meta Packages

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

## Launching Subsystems

All launch files live in `a2_ros`. Use the `a2` CLI to invoke them:

| Command | Launch file | Description |
|---|---|---|
| `a2 start [--rviz] [--dlio]` | `sim.launch.py` | MuJoCo simulation + locomotion controller |
| `a2 nav [--rviz]` | `navigation.launch.py` | CMU navigation stack (terrain analysis + path planner) |
| `a2 explore [--rviz]` | `exploration.launch.py` | Autonomous exploration (TARE planner) |
| `a2 dlio [--rviz]` | `dlio.launch.py` | DLIO LiDAR-inertial odometry |
| — | `real.launch.py` | Real robot — locomotion executor + bridge (NUC) |
| — | `teleop_joy.launch.py` | Joystick teleop |

For `a2_pc2` (run directly on the second compute unit):
```bash
ros2 launch a2_pc2 pc2.launch.py
ros2 launch a2_pc2 camera.launch.py
```

### Typical simulation workflow

**Terminal 1 — simulation:**
```bash
a2 start
```

**Terminal 2 — walk:**
```bash
a2 walk
```

**Terminal 3 — navigation / exploration / odometry:**
```bash
a2 nav --rviz
# or
a2 explore --rviz
# or
a2 dlio --rviz
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
