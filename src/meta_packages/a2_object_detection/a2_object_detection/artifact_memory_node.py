#!/usr/bin/env python3

import json
import os
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.duration import Duration
from rclpy.time import Time

from geometry_msgs.msg import Pose, PoseArray, Quaternion
from visualization_msgs.msg import Marker, MarkerArray
from std_msgs.msg import Header

from tf2_ros import Buffer, TransformListener, TransformException
from scipy.spatial.transform import Rotation

from object_detection_msgs.msg import ObjectDetectionInfoArray


class ArtifactMemoryNode(Node):
    def __init__(self):
        super().__init__("artifact_memory_node")

        self.declare_parameters(
            namespace="",
            parameters=[
                ("input_detection_topic", "/detection_info"),
                ("map_frame", "map"),
                ("merge_radius", 0.75),
                ("min_observations", 2),
                ("save_path", "/tmp/artifacts_map.json"),
                ("save_every_n_updates", 1),
                ("use_latest_tf_if_time_fails", True),
            ],
        )

        self.input_detection_topic = self.get_parameter("input_detection_topic").value
        self.map_frame = self.get_parameter("map_frame").value
        self.merge_radius = float(self.get_parameter("merge_radius").value)
        self.min_observations = int(self.get_parameter("min_observations").value)
        self.save_path = self.get_parameter("save_path").value
        self.save_every_n_updates = int(self.get_parameter("save_every_n_updates").value)
        self.use_latest_tf_if_time_fails = bool(
            self.get_parameter("use_latest_tf_if_time_fails").value
        )

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.artifacts = []
        self.next_id = 0
        self.update_count = 0

        self.detection_sub = self.create_subscription(
            ObjectDetectionInfoArray,
            self.input_detection_topic,
            self.detection_callback,
            10,
        )

        self.pose_pub = self.create_publisher(PoseArray, "/artifacts/map_poses", 10)
        self.marker_pub = self.create_publisher(MarkerArray, "/artifacts/map_markers", 10)

        self.get_logger().info(
            f"Artifact memory listening on {self.input_detection_topic}, storing in frame {self.map_frame}"
        )

    def detection_callback(self, msg: ObjectDetectionInfoArray):
        if not msg.info:
            return

        source_frame = msg.header.frame_id
        if source_frame == "":
            self.get_logger().warn("Detection message has empty frame_id. Cannot transform to map.")
            return

        try:
            stamp = Time.from_msg(msg.header.stamp)

            transform = self.tf_buffer.lookup_transform(
                self.map_frame,
                source_frame,
                stamp,
                timeout=Duration(seconds=0.2),
            )

        except TransformException as ex:
            if not self.use_latest_tf_if_time_fails:
                self.get_logger().warn(
                    f"Could not transform from {source_frame} to {self.map_frame}: {ex}"
                )
                return

            try:
                transform = self.tf_buffer.lookup_transform(
                    self.map_frame,
                    source_frame,
                    Time(),
                    timeout=Duration(seconds=0.2),
                )
                self.get_logger().warn(
                    f"Using latest TF instead of timestamped TF for {source_frame} -> {self.map_frame}",
                    throttle_duration_sec=2.0,
                )
            except TransformException as ex2:
                self.get_logger().warn(
                    f"Could not transform from {source_frame} to {self.map_frame}: {ex2}",
                    throttle_duration_sec=2.0,
                )
                return

        for det in msg.info:
            p_local = np.array(
                [
                    det.position.x,
                    det.position.y,
                    det.position.z,
                ],
                dtype=np.float64,
            )

            p_map = self.transform_point(transform, p_local)

            self.update_or_create_artifact(
                class_id=str(det.class_id),
                position=p_map,
                confidence=float(det.confidence),
                stamp=msg.header.stamp,
            )

        self.update_count += 1

        self.publish_artifacts(msg.header.stamp)

        if self.update_count % self.save_every_n_updates == 0:
            self.save_artifacts()

    def transform_point(self, transform, point):
        t = transform.transform.translation
        q = transform.transform.rotation

        translation = np.array([t.x, t.y, t.z], dtype=np.float64)
        quat = [q.x, q.y, q.z, q.w]

        rot = Rotation.from_quat(quat).as_matrix()
        return rot @ point + translation

    def update_or_create_artifact(self, class_id, position, confidence, stamp):
        best_idx = None
        best_dist = float("inf")

        for i, artifact in enumerate(self.artifacts):
            if artifact["class_id"] != class_id:
                continue

            dist = np.linalg.norm(position - artifact["position"])

            if dist < self.merge_radius and dist < best_dist:
                best_dist = dist
                best_idx = i

        if best_idx is None:
            artifact = {
                "id": self.next_id,
                "class_id": class_id,
                "position": position,
                "confidence": confidence,
                "observations": 1,
                "first_seen_sec": stamp.sec,
                "first_seen_nanosec": stamp.nanosec,
                "last_seen_sec": stamp.sec,
                "last_seen_nanosec": stamp.nanosec,
            }

            self.artifacts.append(artifact)
            self.next_id += 1

            self.get_logger().info(
                f"New artifact {artifact['id']} class={class_id} at map {position}"
            )

        else:
            artifact = self.artifacts[best_idx]
            n = artifact["observations"]

            # Running average position estimate.
            artifact["position"] = (artifact["position"] * n + position) / (n + 1)

            # Keep strongest confidence seen so far.
            artifact["confidence"] = max(artifact["confidence"], confidence)

            artifact["observations"] += 1
            artifact["last_seen_sec"] = stamp.sec
            artifact["last_seen_nanosec"] = stamp.nanosec

    def publish_artifacts(self, stamp):
        header = Header()
        header.stamp = stamp
        header.frame_id = self.map_frame

        pose_array = PoseArray()
        pose_array.header = header

        marker_array = MarkerArray()

        clear = Marker()
        clear.header = header
        clear.action = Marker.DELETEALL
        marker_array.markers.append(clear)

        for artifact in self.artifacts:
            if artifact["observations"] < self.min_observations:
                continue

            p = artifact["position"]

            pose = Pose()
            pose.position.x = float(p[0])
            pose.position.y = float(p[1])
            pose.position.z = float(p[2])
            pose.orientation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
            pose_array.poses.append(pose)

            sphere = Marker()
            sphere.header = header
            sphere.ns = "artifact_memory"
            sphere.id = int(artifact["id"] * 2)
            sphere.type = Marker.SPHERE
            sphere.action = Marker.ADD
            sphere.pose = pose
            sphere.scale.x = 0.35
            sphere.scale.y = 0.35
            sphere.scale.z = 0.35
            sphere.color.r = 1.0
            sphere.color.g = 0.5
            sphere.color.b = 0.0
            sphere.color.a = 1.0
            marker_array.markers.append(sphere)

            label = Marker()
            label.header = header
            label.ns = "artifact_labels"
            label.id = int(artifact["id"] * 2 + 1)
            label.type = Marker.TEXT_VIEW_FACING
            label.action = Marker.ADD
            label.pose.position.x = float(p[0])
            label.pose.position.y = float(p[1])
            label.pose.position.z = float(p[2] + 0.4)
            label.pose.orientation.w = 1.0
            label.scale.z = 0.25
            label.color.r = 1.0
            label.color.g = 1.0
            label.color.b = 1.0
            label.color.a = 1.0
            label.text = (
                f"id={artifact['id']} "
                f"class={artifact['class_id']} "
                f"n={artifact['observations']} "
                f"conf={artifact['confidence']:.2f}"
            )
            marker_array.markers.append(label)

        self.pose_pub.publish(pose_array)
        self.marker_pub.publish(marker_array)

    def save_artifacts(self):
        output = []

        for artifact in self.artifacts:
            if artifact["observations"] < self.min_observations:
                continue

            p = artifact["position"]

            output.append(
                {
                    "id": artifact["id"],
                    "class_id": artifact["class_id"],
                    "x": float(p[0]),
                    "y": float(p[1]),
                    "z": float(p[2]),
                    "confidence": float(artifact["confidence"]),
                    "observations": int(artifact["observations"]),
                    "first_seen": {
                        "sec": int(artifact["first_seen_sec"]),
                        "nanosec": int(artifact["first_seen_nanosec"]),
                    },
                    "last_seen": {
                        "sec": int(artifact["last_seen_sec"]),
                        "nanosec": int(artifact["last_seen_nanosec"]),
                    },
                    "frame_id": self.map_frame,
                }
            )

        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)

        with open(self.save_path, "w") as f:
            json.dump(output, f, indent=2)


def main(args=None):
    rclpy.init(args=args)

    node = ArtifactMemoryNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.save_artifacts()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()