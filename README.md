# a2_ros

ROS2 (Jazzy) simulation of the Unitree A2 quadruped using MuJoCo and a trained RL locomotion policy.

## TODOs
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

The `.env` file is gitignored and personal to your machine. It is also sourced by all setup scripts inside the container, so any runtime overrides (e.g. `RMW_IMPLEMENTATION`, `ROS_BAGS_DIR`) can be added there and they will be picked up automatically.

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
```bash
ros2 launch a2_ros sim.launch.py
ros2 launch a2_ros sim.launch.py rviz:=true
ros2 launch a2_ros sim.launch.py scene:=scene_terrain.xml
```

## Navigation

Requires two terminals. Start the simulation first, then the navigation stack.

**Terminal 1 — simulation:**
```bash
ros2 launch a2_ros sim.launch.py scene:=scene_obstacles.xml
```

**Terminal 2 — stand then walk:**
```bash
cd src/control/a2_locomotion_controller/scripts
./control_mode.sh --stand
./control_mode.sh --walk
```

**Terminal 3 — navigation:**
```bash
ros2 launch a2_ros navigation.launch.py rviz:=true
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
