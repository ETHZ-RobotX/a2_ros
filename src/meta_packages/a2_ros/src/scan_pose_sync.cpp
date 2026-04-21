#include "rclcpp/rclcpp.hpp"
#include "nav_msgs/msg/odometry.hpp"
#include "sensor_msgs/msg/point_cloud2.hpp"
#include "tf2_ros/buffer.h"
#include "tf2_ros/transform_listener.h"

class ScanPoseSync : public rclcpp::Node
{
public:
  ScanPoseSync() : Node("scan_pose_sync"),
    tf_buffer_(get_clock()),
    tf_listener_(tf_buffer_)
  {
    pub_ = create_publisher<nav_msgs::msg::Odometry>("/state_estimation_at_scan", 10);

    scan_sub_ = create_subscription<sensor_msgs::msg::PointCloud2>(
      "/registered_scan", 10,
      [this](sensor_msgs::msg::PointCloud2::SharedPtr msg) { onScan(msg); });
  }

private:
  void onScan(const sensor_msgs::msg::PointCloud2::SharedPtr scan)
  {
    // Look up the full chain: map -> base_link -> front_lidar_link
    geometry_msgs::msg::TransformStamped tf;
    try {
      tf = tf_buffer_.lookupTransform("map", "front_lidar_link", tf2::TimePointZero);
    } catch (const tf2::TransformException & e) {
      RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 2000, "TF lookup failed: %s", e.what());
      return;
    }

    nav_msgs::msg::Odometry out;
    out.header.stamp            = scan->header.stamp;
    out.header.frame_id         = "map";
    out.child_frame_id          = "front_lidar_link";
    out.pose.pose.position.x    = tf.transform.translation.x;
    out.pose.pose.position.y    = tf.transform.translation.y;
    out.pose.pose.position.z    = tf.transform.translation.z;
    out.pose.pose.orientation   = tf.transform.rotation;
    pub_->publish(out);
  }

  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr scan_sub_;
  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr pub_;
  tf2_ros::Buffer tf_buffer_;
  tf2_ros::TransformListener tf_listener_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<ScanPoseSync>());
  rclcpp::shutdown();
}
