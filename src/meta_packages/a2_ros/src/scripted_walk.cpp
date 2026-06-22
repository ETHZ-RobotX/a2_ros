#include <chrono>
#include <cstdlib>
#include <memory>
#include <stdexcept>
#include <string>

#include <geometry_msgs/msg/twist_stamped.hpp>
#include <rclcpp/rclcpp.hpp>

class ScriptedWalk : public rclcpp::Node {
public:
  ScriptedWalk() : Node("scripted_walk")
  {
    declare_parameter("speed", 0.5);
    declare_parameter("duration", 2.0);
    declare_parameter("cmd_topic", "/key_vel");
    declare_parameter("publish_rate", 50.0);
    declare_parameter("stop_after", true);

    speed_ = get_parameter("speed").as_double();
    duration_ = get_parameter("duration").as_double();
    cmd_topic_ = get_parameter("cmd_topic").as_string();
    publish_rate_ = get_parameter("publish_rate").as_double();
    stop_after_ = get_parameter("stop_after").as_bool();

    if (duration_ <= 0.0) {
      throw std::runtime_error("duration must be positive");
    }
    if (publish_rate_ <= 0.0) {
      throw std::runtime_error("publish_rate must be positive");
    }

    cmd_pub_ = create_publisher<geometry_msgs::msg::TwistStamped>(cmd_topic_, 10);
  }

  bool run()
  {
    RCLCPP_INFO(get_logger(), "Assuming robot is already in velocity move mode");
    RCLCPP_INFO(get_logger(), "Walking forward at %.3f m/s for %.3f s", speed_, duration_);
    publishVelocityFor(speed_, duration_);

    RCLCPP_INFO(get_logger(), "Walking backward at %.3f m/s for %.3f s", -speed_, duration_);
    publishVelocityFor(-speed_, duration_);

    if (stop_after_) {
      RCLCPP_INFO(get_logger(), "Publishing stop command");
      publishVelocityFor(0.0, 0.5);
    }

    RCLCPP_INFO(get_logger(), "Scripted walk complete");
    return true;
  }

private:
  void publishVelocityFor(double linear_x, double seconds)
  {
    const auto end_time =
      std::chrono::steady_clock::now() + std::chrono::duration<double>(seconds);
    rclcpp::WallRate rate(publish_rate_);

    while (rclcpp::ok() && std::chrono::steady_clock::now() < end_time) {
      geometry_msgs::msg::TwistStamped msg;
      msg.header.stamp = now();
      msg.header.frame_id = "base_link";
      msg.twist.linear.x = linear_x;
      cmd_pub_->publish(msg);
      rate.sleep();
    }
  }

  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr cmd_pub_;
  double speed_{0.5};
  double duration_{2.0};
  double publish_rate_{50.0};
  bool stop_after_{true};
  std::string cmd_topic_{"/key_vel"};
};

int main(int argc, char** argv)
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<ScriptedWalk>();
  const bool ok = node->run();
  rclcpp::shutdown();
  return ok ? EXIT_SUCCESS : EXIT_FAILURE;
}
