# pc2 — Second Compute Unit

`pc2` is the robot's second onboard computer. It hosts the **Zenoh router for the
robot network** (which the NUC and other machines connect to) and runs the
camera / perception bridge. Unlike the rest of the stack, `a2_pc2` owns its own
launch files and is run directly on pc2.

## What runs on pc2

Defined in [`compose.pc2.yaml`](../compose.pc2.yaml):

- **`zenoh_router_robot`** — the robot-network Zenoh discovery router (`rmw_zenohd`),
  binds `tcp/0.0.0.0:7447`. All robot-side nodes connect here, so on the other
  machines (NUC, dev) set `ZENOH_ROUTER_IP_ROBOT=<pc2 IP>` in their `.env`.
- **`a2_pc2_bridge`** — the Unitree SDK ↔ ROS bridge (`scripts/pc2/pc2_bridge.sh`).
- **`a2_pc2`** nodes — cameras (`gscam2`) and pc2-specific nodes.

> Run only **one** Zenoh router per host — `zenoh_router_robot` and the sim's
> `zenoh_router_sim` both bind TCP `7447`, so don't run them on the same machine.

## Bring up the pc2 stack

On pc2:
```bash
docker compose -f compose.pc2.yaml up -d        # zenoh_router_robot + a2_pc2_bridge
docker compose -f compose.pc2.yaml exec a2_pc2_bridge bash
```

## Launch the pc2 nodes

Build the meta package, then launch (run directly on pc2):
```bash
a2 build a2_pc2
ros2 launch a2_pc2 pc2.launch.py
ros2 launch a2_pc2 camera.launch.py
```
