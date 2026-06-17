// PS4 (DualShock 4) via joy_node axis/button layout:
//   buttons: [0]=Cross, [1]=Circle, [2]=Square, [3]=Triangle
//   axes:    [0]=LS-H, [1]=LS-V, [2]=L2(1=rel/-1=press), [3]=RS-H, [4]=RS-V, [5]=R2
//
// Mode FSM (mirrors a2_interfaces/msg/OperatingMode):
//   1 STAND_DOWN  2 STAND_UP  3 BALANCE_STAND  4 VELOCITY_MOVE  5 FREE
//
// Joystick controls:
//   L2 + Triangle (rising edge) : step mode up  (1→2→3→4); from FREE → VELOCITY_MOVE
//   L2 + Cross    (rising edge) : step mode down (4→3→2→1); from FREE → STAND_DOWN
//   Circle        (rising edge) : go to FREE from any mode

#include <memory>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <sensor_msgs/msg/joy.hpp>
#include <a2_interfaces/msg/operating_mode.hpp>
#include <rclcpp/rclcpp.hpp>

namespace {
  constexpr int BTN_CROSS    = 0;
  constexpr int BTN_CIRCLE   = 1;
  constexpr int BTN_TRIANGLE = 2;
  constexpr int AXIS_LS_H    = 0;
  constexpr int AXIS_LS_V    = 1;
  constexpr int AXIS_L2      = 2;
  constexpr int AXIS_RS_H    = 3;

  using OM = a2_interfaces::msg::OperatingMode;
}

class QuadrupedTeleop : public rclcpp::Node
{
public:
  QuadrupedTeleop() : Node("teleop_node")
  {
    this->declare_parameter("linear_x_limit",  0.15);
    this->declare_parameter("linear_y_limit",  0.10);
    this->declare_parameter("angular_z_limit", 0.10);

    twist_pub_ = this->create_publisher<geometry_msgs::msg::TwistStamped>("/cmd_vel", 10);
    mode_pub_  = this->create_publisher<OM>("/a2/mode", 10);

    joy_sub_ = this->create_subscription<sensor_msgs::msg::Joy>(
      "joy", 10,
      std::bind(&QuadrupedTeleop::joyCallback, this, std::placeholders::_1));

    RCLCPP_INFO(this->get_logger(),
      "Teleop started. mode=%d (STAND_DOWN). "
      "L2+△ = step up | L2+✕ = step down | ○ = FREE",
      current_mode_);
  }

private:
  void publishMode(uint8_t mode)
  {
    current_mode_ = mode;
    OM msg;
    msg.mode = mode;
    mode_pub_->publish(msg);
    RCLCPP_INFO(this->get_logger(), "Mode → %d", mode);
  }

  void joyCallback(const sensor_msgs::msg::Joy::SharedPtr msg)
  {
    // --- velocity (only in VELOCITY_MOVE to avoid "incompatible op mode" warnings) ---
    if (current_mode_ == OM::VELOCITY_MOVE) {
      auto twist = geometry_msgs::msg::TwistStamped();
      twist.header.stamp    = this->now();
      twist.twist.linear.x  = msg->axes[AXIS_LS_V] *
                                this->get_parameter("linear_x_limit").as_double();
      twist.twist.linear.y  = msg->axes[AXIS_LS_H] *
                                this->get_parameter("linear_y_limit").as_double();
      twist.twist.angular.z = msg->axes[AXIS_RS_H] *
                                this->get_parameter("angular_z_limit").as_double();
      twist_pub_->publish(twist);
    }

    // --- guard: enough axes/buttons ---
    if (static_cast<int>(msg->buttons.size()) <= BTN_TRIANGLE ||
        static_cast<int>(msg->axes.size())    <= AXIS_L2) {
      return;
    }

    bool l2       = msg->axes[AXIS_L2] < -0.5f;
    bool triangle = msg->buttons[BTN_TRIANGLE] == 1;
    bool cross    = msg->buttons[BTN_CROSS]    == 1;
    bool circle   = msg->buttons[BTN_CIRCLE]   == 1;

    // Rising-edge detection — trigger only on fresh press, not while held
    bool l2_tri_now   = l2 && triangle;
    bool l2_cross_now = l2 && cross;

    bool l2_tri_press   = l2_tri_now   && !prev_l2_tri_;
    bool l2_cross_press = l2_cross_now && !prev_l2_cross_;
    bool circle_press   = circle        && !prev_circle_;

    prev_l2_tri_   = l2_tri_now;
    prev_l2_cross_ = l2_cross_now;
    prev_circle_   = circle;

    // --- FSM transitions ---
    if (circle_press) {
      if (current_mode_ != OM::FREE)
        publishMode(OM::FREE);
    } else if (l2_tri_press) {
      if (current_mode_ == OM::FREE) {
        publishMode(OM::VELOCITY_MOVE);
      } else if (current_mode_ < OM::VELOCITY_MOVE) {
        publishMode(current_mode_ + 1u);
      }
    } else if (l2_cross_press) {
      if (current_mode_ == OM::FREE) {
        publishMode(OM::STAND_DOWN);
      } else if (current_mode_ > OM::STAND_DOWN) {
        publishMode(current_mode_ - 1u);
      }
    }
  }

  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr twist_pub_;
  rclcpp::Publisher<OM>::SharedPtr mode_pub_;
  rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr joy_sub_;

  uint8_t current_mode_ = OM::STAND_DOWN;
  bool prev_l2_tri_   = false;
  bool prev_l2_cross_ = false;
  bool prev_circle_   = false;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<QuadrupedTeleop>());
  rclcpp::shutdown();
  return 0;
}
