#include <chrono>
#include <memory>
#include <cmath>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"
#include "nav_msgs/msg/odometry.hpp"

using namespace std::chrono_literals;

class WaypointNavigator : public rclcpp::Node
{
public:
  WaypointNavigator()
  : Node("waypoint_navigator"), current_x_(0.0), current_y_(0.0), current_yaw_(0.0),
    target_x_(0.0), target_y_(0.0), target_initialized_(false)
  {
    // Tunable parameters
    delta_x_          = this->declare_parameter<double>("delta_x", 1.0);     // m (relative to start)
    delta_y_          = this->declare_parameter<double>("delta_y", 1.0);     // m (relative to start)
    linear_speed_     = this->declare_parameter<double>("linear_speed", 0.2); // m/s
    position_tolerance_ = this->declare_parameter<double>("position_tolerance", 0.1); // m
    angle_tolerance_  = this->declare_parameter<double>("angle_tolerance", 0.1); // rad
    frame_id_         = this->declare_parameter<std::string>("frame_id", "base_link");

    // Subscribe to odometry
    odom_subscription_ = this->create_subscription<nav_msgs::msg::Odometry>(
      "/odom", 10, std::bind(&WaypointNavigator::odom_callback, this, std::placeholders::_1));

    // Publisher for twist commands
    publisher_ = this->create_publisher<geometry_msgs::msg::TwistStamped>("/cmd_vel", 10);

    // Timer for control loop
    timer_ = this->create_wall_timer(
      100ms, std::bind(&WaypointNavigator::timer_callback, this));

    RCLCPP_INFO(this->get_logger(),
      "Waypoint Navigator: delta=(%.2f, %.2f) m, v=%.2f m/s, pos_tol=%.2f m, ang_tol=%.2f rad",
      delta_x_, delta_y_, linear_speed_, position_tolerance_, angle_tolerance_);
  }

private:
  void odom_callback(const nav_msgs::msg::Odometry::SharedPtr msg)
  {
    // Extract position from odometry
    current_x_ = msg->pose.pose.position.x;
    current_y_ = msg->pose.pose.position.y;

    // Initialize target on first odometry message
    if (!target_initialized_) {
      target_x_ = current_x_ + delta_x_;
      target_y_ = current_y_ + delta_y_;
      target_initialized_ = true;
      RCLCPP_INFO(this->get_logger(),
        "Target initialized at (%.2f, %.2f) m (start: (%.2f, %.2f) m + delta: (%.2f, %.2f) m)",
        target_x_, target_y_, current_x_, current_y_, delta_x_, delta_y_);
    }

    // Extract yaw angle from quaternion
    double qx = msg->pose.pose.orientation.x;
    double qy = msg->pose.pose.orientation.y;
    double qz = msg->pose.pose.orientation.z;
    double qw = msg->pose.pose.orientation.w;

    // Convert quaternion to yaw
    current_yaw_ = std::atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz));
  }

  void timer_callback()
  {
    // Calculate distance to waypoint
    double dx = target_x_ - current_x_;
    double dy = target_y_ - current_y_;
    double distance = std::sqrt(dx * dx + dy * dy);

    // Check if reached waypoint
    if (distance < position_tolerance_) {
      RCLCPP_INFO(this->get_logger(), "Waypoint reached!");
      publish_zero_twist();
      rclcpp::shutdown();
      return;
    }

    // Calculate desired heading to waypoint
    double desired_yaw = std::atan2(dy, dx);

    // Calculate yaw error (shortest path)
    double yaw_error = desired_yaw - current_yaw_;

    // Normalize yaw error to [-pi, pi]
    while (yaw_error > M_PI) yaw_error -= 2.0 * M_PI;
    while (yaw_error < -M_PI) yaw_error += 2.0 * M_PI;

    auto msg = geometry_msgs::msg::TwistStamped();
    msg.header.stamp = this->get_clock()->now();
    msg.header.frame_id = frame_id_;

    // Simple proportional controller for angular velocity
    double angular_velocity = 1.5 * yaw_error; // proportional gain

    if (std::abs(yaw_error) < angle_tolerance_) {
      // Heading is correct, move forward
      msg.twist.linear.x = linear_speed_;
      msg.twist.angular.z = angular_velocity;
    } else {
      // Need to rotate first (in-place rotation)
      msg.twist.linear.x = 0.0;
      msg.twist.angular.z = angular_velocity;
    }

    msg.twist.linear.y = 0.0;
    msg.twist.linear.z = 0.0;
    msg.twist.angular.x = 0.0;
    msg.twist.angular.y = 0.0;

    publisher_->publish(msg);

    RCLCPP_DEBUG(this->get_logger(),
      "Distance: %.2f m, Yaw error: %.2f rad, Cmd: v=%.2f, w=%.2f",
      distance, yaw_error, msg.twist.linear.x, msg.twist.angular.z);
  }

  void publish_zero_twist()
  {
    auto msg = geometry_msgs::msg::TwistStamped();
    msg.header.stamp = this->get_clock()->now();
    msg.header.frame_id = frame_id_;
    msg.twist.linear.x = 0.0;
    msg.twist.angular.z = 0.0;
    publisher_->publish(msg);
  }

  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr publisher_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_subscription_;
  rclcpp::TimerBase::SharedPtr timer_;

  double current_x_, current_y_, current_yaw_;
  double target_x_, target_y_;
  double delta_x_, delta_y_;
  double linear_speed_;
  double position_tolerance_;
  double angle_tolerance_;
  std::string frame_id_;
  bool target_initialized_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<WaypointNavigator>());
  rclcpp::shutdown();
  return 0;
}
