# a2_ros

ROS2 (Jazzy) simulation of the Unitree A2 quadruped using MuJoCo and a trained RL locomotion policy.

## TODOs
- [x] Provide base docker setup for development
- [ ] Move dependency installations from install scripts to docker **Until this time, try not to recreate containers to save time**
- [ ] Decide whether install script should manage git submodules too (and thus lie inside the docker runtime)
- [ ] Remove interactive components of install script
- [ ] Ship `a2_ros` source code with built image
- [ ] Setup docker managed volumes for build artifacts (also requires deciding how to organize these)
- [ ] Setup docker managed volumes for data artifacts (rosbags, pytorch models etc.)(also requires deciding how to organize these)
- [ ] Remove all source code from meta-package `a2_ros` and only maintain dependencies
- [ ] Add source folders for each subsystem `core/ sim/` etc.

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
1. **\[FIRST TIME ONLY\]**: Execute the install script. After the install script completes, you should expect to see a mujoco window. If not, there are X11 forwarding issues.
    ```
    ./install.sh
    ```
1. Source `/a2_ros/setup.sh`

### Stopping container
1. Stop the container with `docker compose stop a2_ros_dev`. As
As long as the container is not recreated (either using `--force-recreate` or `docker compose down`), the installation scripts do not have to be re-run. The container will be restarted with all the source configurations ready.

## Setup

```bash
conda deactivate   # repeat until $CONDA_PREFIX is empty
git clone git@github.com:ETHZ-RobotX/a2_ros.git --recursive
bash a2_ros/install.sh
```

## Run

Source in every new terminal:
```bash
source a2_ros/setup.sh
```

Launch the simulation:
```bash
ros2 launch a2_ros sim.launch.py
ros2 launch a2_ros sim.launch.py rviz:=true
ros2 launch a2_ros sim.launch.py scene:=scene_terrain.xml
```

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
