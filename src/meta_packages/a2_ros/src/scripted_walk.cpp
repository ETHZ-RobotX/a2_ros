#include <chrono>
#include <cstdlib>
#include <memory>
#include <stdexcept>
#include <string>

#include <a2_interfaces/msg/operating_mode.hpp>
#include <a2_interfaces/srv/set_operating_mode.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <rclcpp/rclcpp.hpp>

using namespace std::chrono_literals;

namespace {
using OperatingMode = a2_interfaces::msg::OperatingMode;
using SetOperatingMode = a2_interfaces::srv::SetOperatingMode;
}  // namespace

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
    mode_client_ = create_client<SetOperatingMode>("/a2/set_mode");
  }

  bool run()
  {
    if (!mode_client_->wait_for_service(5s)) {
      RCLCPP_ERROR(get_logger(), "Service /a2/set_mode is not available");
      return false;
    }

    if (!setMode(OperatingMode::STAND_UP) ||
        !setMode(OperatingMode::BALANCE_STAND) ||
        !setMode(OperatingMode::VELOCITY_MOVE)) {
      return false;
    }

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
  bool setMode(uint8_t mode)
  {
    auto request = std::make_shared<SetOperatingMode::Request>();
    request->mode = mode;

    auto future = mode_client_->async_send_request(request);
    if (rclcpp::spin_until_future_complete(shared_from_this(), future, 5s) !=
        rclcpp::FutureReturnCode::SUCCESS) {
      RCLCPP_ERROR(get_logger(), "Timed out requesting mode %u", mode);
      return false;
    }

    const auto response = future.get();
    if (!response->success) {
      if (response->current_mode == mode || response->current_mode > mode) {
        RCLCPP_WARN(get_logger(),
                    "Mode %u rejected but current mode is already %u: %s", mode,
                    response->current_mode, response->message.c_str());
        return true;
      }
      RCLCPP_ERROR(get_logger(), "Mode %u rejected: %s", mode, response->message.c_str());
      return false;
    }

    RCLCPP_INFO(get_logger(), "Mode %u accepted: %s", mode, response->message.c_str());
    return true;
  }

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

  rclcpp::Client<SetOperatingMode>::SharedPtr mode_client_;
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
