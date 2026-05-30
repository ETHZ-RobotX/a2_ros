#include <memory>
#include <string>
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/point_cloud2.hpp"
#include "tf2_ros/buffer.h"
#include "tf2_ros/transform_listener.h"
#include "tf2_sensor_msgs/tf2_sensor_msgs.hpp"

// Transforms an incoming PointCloud2 into a fixed target frame and republishes
// it as /registered_scan.  Works with any TF provider — ground-truth from
// a2_bridge in simulation, or DLIO on real hardware.
//
// Parameters:
//   input_topic  (string)  — raw pointcloud to subscribe to
//   target_frame (string)  — frame to transform into (typically "map")
//   tf_lag_sec   (double)  — look up TF this many seconds in the past to avoid
//                            "extrapolation into the future" when the TF source
//                            lags behind the scan timestamp (default 0.025 s)

class RegisteredScanPub : public rclcpp::Node
{
public:
  RegisteredScanPub()
  : Node("registered_scan_pub"),
    tf_buffer_(this->get_clock()),
    tf_listener_(tf_buffer_)
  {
    declare_parameter("input_topic",  "/mujoco/front_lidar");
    declare_parameter("target_frame", "map");
    declare_parameter("tf_lag_sec",   0.025);

    input_topic_  = get_parameter("input_topic").as_string();
    target_frame_ = get_parameter("target_frame").as_string();
    tf_lag_       = get_parameter("tf_lag_sec").as_double();

    pub_ = create_publisher<sensor_msgs::msg::PointCloud2>("/registered_scan", 10);

    sub_ = create_subscription<sensor_msgs::msg::PointCloud2>(
      input_topic_, 10,
      std::bind(&RegisteredScanPub::cloud_callback, this, std::placeholders::_1));

    RCLCPP_INFO(get_logger(),
      "registered_scan_pub: %s -> /registered_scan (frame: %s, lag: %.3fs)",
      input_topic_.c_str(), target_frame_.c_str(), tf_lag_);
  }

private:
  void cloud_callback(const sensor_msgs::msg::PointCloud2::SharedPtr msg)
  {
    try {
      auto t_query = rclcpp::Time(msg->header.stamp) - rclcpp::Duration::from_seconds(tf_lag_);
      auto transform = tf_buffer_.lookupTransform(target_frame_, msg->header.frame_id, t_query);

      sensor_msgs::msg::PointCloud2 cloud_out;
      tf2::doTransform(*msg, cloud_out, transform);
      cloud_out.header.stamp    = msg->header.stamp;
      cloud_out.header.frame_id = target_frame_;

      // Add 'intensity' field alias for 'dist' so terrain_analysis can parse
      // the cloud as PointXYZI without warnings. No data copy — same offset.
      uint32_t dist_offset = 12;
      for (const auto & f : cloud_out.fields) {
        if (f.name == "dist") { dist_offset = f.offset; break; }
      }
      sensor_msgs::msg::PointField intensity_field;
      intensity_field.name     = "intensity";
      intensity_field.offset   = dist_offset;
      intensity_field.datatype = sensor_msgs::msg::PointField::FLOAT32;
      intensity_field.count    = 1;
      cloud_out.fields.push_back(intensity_field);

      pub_->publish(cloud_out);
    } catch (const tf2::TransformException & e) {
      RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 2000,
        "TF lookup failed: %s", e.what());
    }
  }

  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub_;
  tf2_ros::Buffer tf_buffer_;
  tf2_ros::TransformListener tf_listener_;

  std::string input_topic_;
  std::string target_frame_;
  double tf_lag_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<RegisteredScanPub>());
  rclcpp::shutdown();
  return 0;
}
