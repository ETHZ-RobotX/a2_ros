#include <memory>
#include <geometry_msgs/msg/twist.hpp>
#include <sensor_msgs/msg/joy.hpp>
#include <std_msgs/msg/int32.hpp>
#include <rclcpp/rclcpp.hpp>

class QuadrupedTeleop : public rclcpp::Node
{
public:
  QuadrupedTeleop() : Node("teleop_node")
  {
    // Declare parameters for scaling (tuning sensitivity)
    this->declare_parameter("linear_speed_limit", 1.0);
    this->declare_parameter("angular_speed_limit", 2.0);

    // Publisher for cmd_vel
    twist_pub_ = this->create_publisher<geometry_msgs::msg::Twist>("cmd_vel", 10);
    // Publisher for the locomotion mode
    mode_pub_ = this->create_publisher<std_msgs::msg::Int32>("mode", 10);

    // Subscriber for joystick
    joy_sub_ = this->create_subscription<sensor_msgs::msg::Joy>(
      "joy", 10, std::bind(&QuadrupedTeleop::joy_callback, this, std::placeholders::_1));

    RCLCPP_INFO(this->get_logger(), "Quadruped Teleop Node Started.");
  }

private:
  void joy_callback(const sensor_msgs::msg::Joy::SharedPtr msg)
  {
    auto twist = geometry_msgs::msg::Twist();
    auto mode = std_msgs::msg::Int32();

    double linear_scale = this->get_parameter("linear_speed_limit").as_double();
    double angular_scale = this->get_parameter("angular_speed_limit").as_double();

    // Mapping for standard Gamepad (PS4/Xbox/Logitech)
    // Left Stick Vertical -> Linear X (Forward/Backward)
    twist.linear.x = msg->axes[1] * linear_scale;
    // Left Stick Horizontal -> Linear Y (Strafing)
    twist.linear.y = msg->axes[0] * linear_scale;
    // Right Stick Horizontal -> Angular Z (Yaw/Turning)
    twist.angular.z = msg->axes[3] * angular_scale;

    twist_pub_->publish(twist);

    int new_mode = current_mode_;
    if (msg->buttons[0] == 1 && msg->axes[2] == -1) {
        new_mode = 1;   // Sit down
    }
    if (msg->buttons[3] == 1 && msg->axes[2] == -1) {
        new_mode = 2;   // Stand up
    }
    if (msg->axes[2] == -1 && msg->axes[5] == -1) {
        new_mode = 3;   // Walk
    }
    if (new_mode != current_mode_) {
        current_mode_ = new_mode;
        mode.data = current_mode_;
        mode_pub_->publish(mode);
    }
  }

  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr twist_pub_;
  rclcpp::Publisher<std_msgs::msg::Int32>::SharedPtr mode_pub_;
  rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr joy_sub_;
  int current_mode_ = 0;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<QuadrupedTeleop>());
  rclcpp::shutdown();
  return 0;
}
