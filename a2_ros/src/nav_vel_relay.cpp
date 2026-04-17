#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "geometry_msgs/msg/twist_stamped.hpp"

// Relays /nav_vel_cmd (TwistStamped from local_planner pathFollower)
// to /cmd_vel (Twist) consumed by the locomotion controller.
class NavVelRelay : public rclcpp::Node {
public:
  NavVelRelay() : Node("nav_vel_relay")
  {
    pub_ = create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 10);
    sub_ = create_subscription<geometry_msgs::msg::TwistStamped>(
      "/nav_vel_cmd", 10,
      [this](const geometry_msgs::msg::TwistStamped::SharedPtr msg) {
        pub_->publish(msg->twist);
      });
  }
private:
  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr          pub_;
  rclcpp::Subscription<geometry_msgs::msg::TwistStamped>::SharedPtr sub_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<NavVelRelay>());
  rclcpp::shutdown();
  return 0;
}
