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
1. Install [Docker](https://docs.docker.com/engine/install/). Note Linux systems need Docker Engine **not Docker Desktop**, MacOS needs Docker Desktop, Windows TBD
1. Setup X11 forwarding privileges from docker to host:
    ```bash
    xhost +local:docker
    ```
1. Clone the repository and submodules:
    ```bash
    git clone git@github.com:ETHZ-RobotX/a2_ros.git --recursive
    ```

### Spawn Docker
1. Spawn up the `a2_ros_dev` service using docker compose
    ```bash
    docker compose up -d a2_ros_dev
    ```
1. Enter container:
    ```bash
    docker compose exec a2_ros_dev bash
    ```

### Inside container
1. The ROS environment is already sourced when starting up a bash shell. Use the `/a2_ros/scripts/setup.sh` for refreshing the workspace

### Stopping container
1. Stop the container with `docker compose stop a2_ros_dev`.
2. Remove all resources (if required) with `docker compose down`

## Setup - LEFT FOR COMPATIBILITY

```bash
conda deactivate   # repeat until $CONDA_PREFIX is empty
git clone git@github.com:ETHZ-RobotX/a2_ros.git --recursive
bash a2_ros/scripts/local/install.sh
```

## Run

Source in every new terminal:
```bash
source a2_ros/scripts/local/setup.sh
```

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

The docker setup is currently fully volume mounted. The image does not ship with the `a2_ros` workspace but will eventually do so.
