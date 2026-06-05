#include <mutex>
#include <rclcpp/logging.hpp>
#include <rclcpp/node_options.hpp>
#include "a2_sport_client.hpp"
#include "a2_interfaces/msg/operating_mode.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "ros2_sport_client.hpp"

namespace {
constexpr std::chrono::milliseconds kControlPeriod{20}; // 50 Hz
// TODO: Move these to ros params?
constexpr float kMaxVelX{0.15};  // m/s
constexpr float kMaxVelY{0.1};   // m/s
constexpr float kMaxYawRate{0.1}; // rad/s
} // namespace

A2SportClientNode::A2SportClientNode(const rclcpp::NodeOptions &options) :
  Node("sport_client", options),
  sport_client_(this), mode_fsm_(kMaxVelX, kMaxVelY, kMaxYawRate) {
  setupSubscribers();
  setupTimers();
}

void A2SportClientNode::setupSubscribers() {
  mode_sub_ = this->create_subscription<a2_interfaces::msg::OperatingMode>("/mode", rclcpp::QoS(10), [this](a2_interfaces::msg::OperatingMode::SharedPtr msg){
    this->modeCallback(msg);
  });

  cmd_vel_sub_ = this->create_subscription<geometry_msgs::msg::Twist>("/cmd_vel", rclcpp::QoS(10), [this](geometry_msgs::msg::Twist::SharedPtr msg){
    this->cmdVelCallback(msg);
  });
}

void A2SportClientNode::setupTimers() {
  timer_ = this->create_timer(kControlPeriod, [this]() {
      this->controlLoop();
  });
}

void A2SportClientNode::modeCallback(const a2_interfaces::msg::OperatingMode::SharedPtr msg) {
  std::lock_guard<std::mutex> lock(state_mutex_);
  if (!mode_fsm_.mode_transition(static_cast<OpMode>(msg->mode))) {
    RCLCPP_WARN(this->get_logger(), "Invalid Transition to %d", msg->mode);
    return;
  }
  RCLCPP_INFO(this->get_logger(), "Mode Requested: %d", msg->mode);
}

void A2SportClientNode::cmdVelCallback(const geometry_msgs::msg::Twist::SharedPtr msg) {
  std::lock_guard<std::mutex> lock(state_mutex_);
  if (!mode_fsm_.set_cmd_vel(msg->linear.x, msg->linear.y, msg->angular.z)) {
    RCLCPP_WARN(this->get_logger(), "Incompatible Op Mode, Zero Velocity");
  }
}

void A2SportClientNode::controlLoop() {
  OpMode req_mode;
  std::array<float, 3> req_vel;
  bool mode_changed = false;
  {
    std::lock_guard<std::mutex> lock(state_mutex_);
    std::tie(req_mode, mode_changed) = mode_fsm_.get_mode();
    req_vel = mode_fsm_.get_cmd_vel();
  }

  if (req_mode != OpMode::VELOCITY_MOVE && !mode_changed) {
    // Nothing changed when not in velocity move, so noop
    return;
  }

  switch (req_mode) {
    case OpMode::ESTOP:
      RCLCPP_DEBUG(this->get_logger(), "Mode: ESTOP/DAMP");
      sport_client_.Damp(req_);
      break;
    case OpMode::STAND_DOWN:
      RCLCPP_DEBUG(this->get_logger(), "Mode: STAND DOWN");
      sport_client_.StandDown(req_);
      break;
    case OpMode::STAND_UP:
      RCLCPP_DEBUG(this->get_logger(), "Mode: STAND_UP");
      sport_client_.StandUp(req_);
      break;
    case OpMode::BALANCE_STAND:
      RCLCPP_DEBUG(this->get_logger(), "Mode: BALANCE_STAND");
      sport_client_.BalanceStand(req_);
      break;
    case OpMode::VELOCITY_MOVE:
      RCLCPP_DEBUG(this->get_logger(), "Mode: VELOCITY_MOVE");
      sport_client_.Move(req_, req_vel[0], req_vel[1], req_vel[2]);
      break;
    case OpMode::FREE:
      RCLCPP_DEBUG(this->get_logger(), "Mode: FREE");
      sport_client_.StopMove(req_);
      break;
    default:
      RCLCPP_WARN(this->get_logger(), "Invalid Mode Requested. Ignoring");
      break;
  }
}

int main(int argc, char **argv) {
    try {
        rclcpp::init(argc, argv);
        auto options = rclcpp::NodeOptions().automatically_declare_parameters_from_overrides(true);
        auto node = std::make_shared<A2SportClientNode>(options);

        rclcpp::executors::MultiThreadedExecutor exec(rclcpp::ExecutorOptions(), 2);
        exec.add_node(node);
        exec.spin();
        rclcpp::shutdown();
        return 0;
    } catch (const std::exception &e) {
        std::cerr << "Fatal error: " << e.what() << std::endl;
        return 1;
    }
}
