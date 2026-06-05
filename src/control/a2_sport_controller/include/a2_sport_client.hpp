#ifndef A2_SPORT_CLIENT_H_
#define A2_SPORT_CLIENT_H_

#include <rclcpp/rclcpp.hpp>
#include <rclcpp/subscription.hpp>

#include "ros2_sport_client.hpp"
#include "mode_fsm.hpp"
#include "a2_interfaces/msg/operating_mode.hpp"
#include "geometry_msgs/msg/twist.hpp"

class A2SportClientNode : public rclcpp::Node {
public:
  explicit A2SportClientNode(const rclcpp::NodeOptions &options = rclcpp::NodeOptions());

private:
  // Initialization
  void setupSubscribers();
  void setupTimers();

  // Callback Functions
  void modeCallback(const a2_interfaces::msg::OperatingMode::SharedPtr msg);
  void cmdVelCallback(const geometry_msgs::msg::Twist::SharedPtr msg);

  // Control
  void controlLoop();

private:
  // Sport Client Specific
  SportClient sport_client_;
  unitree_api::msg::Request req_;  // Unitree A2 ROS2 request message

  // ROS
  rclcpp::Subscription<a2_interfaces::msg::OperatingMode>::SharedPtr mode_sub_;
  rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr cmd_vel_sub_;
  rclcpp::TimerBase::SharedPtr timer_;

  // State - Need to be accessed via mutex
  ModeFsm mode_fsm_;
  std::mutex state_mutex_;
};

#endif /* A2_SPORT_CLIENT_H_ */
