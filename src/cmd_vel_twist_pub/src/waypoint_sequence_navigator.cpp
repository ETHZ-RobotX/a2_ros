#include <chrono>
#include <memory>
#include <cmath>
#include <vector>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"
#include "nav_msgs/msg/odometry.hpp"

using namespace std::chrono_literals;

struct Waypoint
{
  double x, y;
  Waypoint(double x = 0.0, double y = 0.0) : x(x), y(y) {}
};

class WaypointSequenceNavigator : public rclcpp::Node
{
public:
  WaypointSequenceNavigator()
  : Node("waypoint_sequence_navigator"), current_x_(0.0), current_y_(0.0), current_yaw_(0.0),
    waypoint_index_(0), target_initialized_(false), timed_action_active_(false)
  {
    // Tunable parameters
    linear_speed_     = this->declare_parameter<double>("linear_speed", 0.2); // m/s
    position_tolerance_ = this->declare_parameter<double>("position_tolerance", 0.1); // m
    angle_tolerance_  = this->declare_parameter<double>("angle_tolerance", 0.1); // rad
    frame_id_         = this->declare_parameter<std::string>("frame_id", "base_link");
    std::string state_topic = this->declare_parameter<std::string>("state_topic", "/state_estimation");  // use /odom for sim

    // Define waypoint sequence (relative to start position)
    // Example: square (1,0) -> (1,1) -> (0,1) -> (0,0), then move forward for 3 seconds
    waypoint_deltas_ = {
      {1.0, 0.0},   // Move 1m forward
      {0.0, 1.0},   // Move 1m left
      {-1.0, 0.0},  // Move 1m backward
      {0.0, -1.0}   // Move 1m right - back to start
    };

    // Subscribe to odometry
    odom_subscription_ = this->create_subscription<nav_msgs::msg::Odometry>(
      state_topic, 10, std::bind(&WaypointSequenceNavigator::odom_callback, this, std::placeholders::_1));

    // Publisher for twist commands
    publisher_ = this->create_publisher<geometry_msgs::msg::TwistStamped>("/cmd_vel", 10);

    // Timer for control loop
    timer_ = this->create_wall_timer(
      100ms, std::bind(&WaypointSequenceNavigator::timer_callback, this));

    RCLCPP_WARN(this->get_logger(),
      "Waypoint Sequence Navigator: %zu waypoints, v=%.2f m/s, pos_tol=%.2f, ang_tol=%.2f, topic=%s",
      waypoint_deltas_.size(), linear_speed_, position_tolerance_, angle_tolerance_, state_topic.c_str());
  }

private:
  void odom_callback(const nav_msgs::msg::Odometry::SharedPtr msg)
  {
    // Extract position from odometry
    current_x_ = msg->pose.pose.position.x;
    current_y_ = msg->pose.pose.position.y;

    // Initialize waypoints on first odometry message
    if (!target_initialized_) {
      initialize_waypoints(current_x_, current_y_);
      target_initialized_ = true;
    }

    // Extract yaw angle from quaternion
    double qx = msg->pose.pose.orientation.x;
    double qy = msg->pose.pose.orientation.y;
    double qz = msg->pose.pose.orientation.z;
    double qw = msg->pose.pose.orientation.w;

    // Convert quaternion to yaw
    current_yaw_ = std::atan2(2.0 * (qw * qz + qx * qy), 1.0 - 2.0 * (qy * qy + qz * qz));
  }

  void initialize_waypoints(double start_x, double start_y)
  {
    waypoints_.clear();
    double current_x = start_x;
    double current_y = start_y;

    // Convert relative deltas to absolute positions
    for (const auto& delta : waypoint_deltas_) {
      current_x += delta.x;
      current_y += delta.y;
      waypoints_.emplace_back(current_x, current_y);
    }

    RCLCPP_INFO(this->get_logger(),
      "Waypoint sequence initialized. Start: (%.2f, %.2f), %zu waypoints",
      start_x, start_y, waypoints_.size());

    for (size_t i = 0; i < waypoints_.size(); ++i) {
      RCLCPP_INFO(this->get_logger(), "  Waypoint %zu: (%.2f, %.2f)", i, waypoints_[i].x, waypoints_[i].y);
    }
  }

  void timer_callback()
  {
    // Wait for odometry to initialize waypoints
    if (!target_initialized_) {
      return;
    }

    // Handle timed action (e.g., move forward for 3 seconds)
    if (timed_action_active_) {
      auto now = std::chrono::steady_clock::now();
      double elapsed = std::chrono::duration<double>(now - timed_action_start_time_).count();

      if (elapsed >= timed_action_duration_) {
        RCLCPP_INFO(this->get_logger(), "Timed action completed!");
        timed_action_active_ = false;
        publish_zero_twist();
        rclcpp::shutdown();
        return;
      }

      auto msg = geometry_msgs::msg::TwistStamped();
      msg.header.stamp = this->get_clock()->now();
      msg.header.frame_id = frame_id_;
      msg.twist.linear.x = linear_speed_;
      msg.twist.angular.z = 0.0;
      publisher_->publish(msg);
      return;
    }

    // Check if all waypoints are completed
    if (waypoint_index_ >= waypoints_.size()) {
      RCLCPP_INFO(this->get_logger(), "All waypoints completed! Starting timed action...");
      start_timed_action(3.0); // Move forward for 3 seconds
      return;
    }

    // Navigate to current waypoint
    const auto& target = waypoints_[waypoint_index_];
    double dx = target.x - current_x_;
    double dy = target.y - current_y_;
    double distance = std::sqrt(dx * dx + dy * dy);

    // Check if reached current waypoint
    if (distance < position_tolerance_) {
      RCLCPP_INFO(this->get_logger(), "Waypoint %zu reached!", waypoint_index_);
      waypoint_index_++;
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
    double angular_velocity = 1.5 * yaw_error;

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
      "Waypoint %zu: distance=%.2f m, yaw_error=%.2f rad, cmd: v=%.2f, w=%.2f",
      waypoint_index_, distance, yaw_error, msg.twist.linear.x, msg.twist.angular.z);
  }

  void start_timed_action(double duration_seconds)
  {
    timed_action_active_ = true;
    timed_action_duration_ = duration_seconds;
    timed_action_start_time_ = std::chrono::steady_clock::now();
    RCLCPP_INFO(this->get_logger(), "Starting timed action for %.1f seconds", duration_seconds);
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
  double linear_speed_;
  double position_tolerance_;
  double angle_tolerance_;
  std::string frame_id_;

  std::vector<Waypoint> waypoint_deltas_;
  std::vector<Waypoint> waypoints_;
  size_t waypoint_index_;
  bool target_initialized_;

  bool timed_action_active_;
  double timed_action_duration_;
  std::chrono::steady_clock::time_point timed_action_start_time_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<WaypointSequenceNavigator>());
  rclcpp::shutdown();
  return 0;
}
